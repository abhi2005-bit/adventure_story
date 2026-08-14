"""
LLM-powered story generation service.
Handles context-aware story generation with structured output.
"""
import json
import os
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from backend.core.models import StoryLLMResponse, StoryNodeLLM, StoryOptionLLM
from backend.models.story import Story, StoryNode
from backend.core.config import settings


class StoryGeneratorService:
    """Service for generating story content using LLM."""
    
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.client = None
        if self.api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
            except ImportError:
                pass
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt for story generation."""
        return """You are a master interactive fiction writer creating branching narrative adventures.
Generate immersive, context-aware story nodes with meaningful choices that have real consequences.

RULES:
1. Each choice must be DISTINCT and lead to genuinely different outcomes
2. Choices must be contextually relevant to the current scene, theme, and story state
3. Track consequences: items gained/lost, relationships changed, events triggered, locations visited
4. Maintain story consistency - no contradictions with established facts
5. Generate 2-4 options per node (unless it's an ending)
6. Endings should feel earned based on player's journey
7. Story depth: aim for 3-6 meaningful decisions before endings

OUTPUT FORMAT (JSON):
{
  "content": "Story narrative text (2-4 paragraphs)",
  "is_ending": false,
  "is_winning_ending": false,
  "options": [
    {
      "text": "Specific, contextual choice text",
      "consequence": "Brief description of what this choice might lead to"
    }
  ],
  "story_state_updates": {
    "location": "current location name",
    "characters": ["character names met"],
    "inventory": ["items obtained"],
    "events": ["key events that occurred"],
    "relationships": {"character": "relationship status"},
    "objectives": ["current goals"],
    "important_decisions": ["major choices made"]
  }
}"""
    
    def _build_user_prompt(
        self,
        theme: str,
        current_node_content: str = "",
        previous_choices: List[str] = None,
        story_state: Dict = None,
        is_root: bool = False,
        depth: int = 0,
        max_depth: int = 5
    ) -> str:
        """Build the user prompt with full context."""
        previous_choices = previous_choices or []
        story_state = story_state or {}
        
        context_parts = [f"THEME: {theme}"]
        
        if is_root:
            context_parts.append("\nThis is the START of the story. Create an engaging opening scene that establishes the world, protagonist, and initial conflict. Provide 3 distinct starting choices.")
        else:
            context_parts.append(f"\nCURRENT SCENE:\n{current_node_content}")
            
            if previous_choices:
                context_parts.append(f"\nPREVIOUS CHOICES MADE:\n" + "\n".join(f"- {c}" for c in previous_choices))
            
            if story_state:
                state_lines = []
                if story_state.get("location"):
                    state_lines.append(f"Location: {story_state['location']}")
                if story_state.get("characters"):
                    state_lines.append(f"Characters: {', '.join(story_state['characters'])}")
                if story_state.get("inventory"):
                    state_lines.append(f"Inventory: {', '.join(story_state['inventory'])}")
                if story_state.get("events"):
                    state_lines.append(f"Key Events: {', '.join(story_state['events'])}")
                if story_state.get("relationships"):
                    rels = [f"{k}: {v}" for k, v in story_state['relationships'].items()]
                    state_lines.append(f"Relationships: {', '.join(rels)}")
                if story_state.get("objectives"):
                    state_lines.append(f"Objectives: {', '.join(story_state['objectives'])}")
                if story_state.get("important_decisions"):
                    state_lines.append(f"Important Decisions: {', '.join(story_state['important_decisions'])}")
                
                if state_lines:
                    context_parts.append("\nSTORY STATE:\n" + "\n".join(state_lines))
            
            context_parts.append(f"\nSTORY DEPTH: {depth} / {max_depth} decisions made")
            
            if depth >= max_depth - 1:
                context_parts.append("\n⚠️ This story is approaching its conclusion. Generate choices that lead toward meaningful endings (winning, losing, or neutral). At least one choice should lead to an ending.")
        
        context_parts.append("\nGenerate the next story node with context-aware choices.")
        
        return "\n".join(context_parts)
    
    def _call_llm(self, system_prompt: str, user_prompt: str) -> Optional[Dict]:
        """Call the LLM API and return parsed response."""
        if not self.client:
            return None
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.8,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            print(f"LLM call failed: {e}")
            return None
    
    def _validate_and_fix_response(self, data: Dict, is_root: bool, depth: int, max_depth: int) -> Dict:
        """Validate and fix LLM response."""
        # Ensure required fields
        data.setdefault("content", "The story continues...")
        data.setdefault("is_ending", False)
        data.setdefault("is_winning_ending", False)
        data.setdefault("options", [])
        data.setdefault("story_state_updates", {})
        
        # Force ending if at max depth
        if depth >= max_depth and not data["is_ending"]:
            data["is_ending"] = True
            data["is_winning_ending"] = depth >= max_depth - 1  # Slightly favor winning at max depth
            data["options"] = []
        
        # Ensure non-ending nodes have options
        if not data["is_ending"] and len(data["options"]) < 2:
            # Add generic but contextual fallback options
            fallback_options = [
                {"text": "Investigate further", "consequence": "May reveal hidden details"},
                {"text": "Take a cautious approach", "consequence": "Safer but might miss opportunities"},
                {"text": "Act boldly", "consequence": "High risk, high reward"}
            ]
            data["options"] = fallback_options[:3]
        
        # Deduplicate options
        seen_texts = set()
        unique_options = []
        for opt in data["options"]:
            text_lower = opt.get("text", "").lower().strip()
            if text_lower and text_lower not in seen_texts:
                seen_texts.add(text_lower)
                unique_options.append(opt)
        data["options"] = unique_options[:4]  # Max 4 options
        
        return data
    
    def _convert_to_pydantic(self, data: Dict) -> StoryNodeLLM:
        """Convert validated dict to Pydantic model."""
        options = []
        for opt in data.get("options", []):
            # Create a minimal nextNode for the option (will be generated when chosen)
            next_node = StoryNodeLLM(
                content="",
                isEnding=False,
                isWinningEnding=False,
                options=[]
            )
            options.append(StoryOptionLLM(text=opt["text"], nextNode=next_node.model_dump()))
        
        return StoryNodeLLM(
            content=data["content"],
            isEnding=data["is_ending"],
            isWinningEnding=data["is_winning_ending"],
            options=options if options else None
        )
    
    def generate_root_node(
        self,
        db: Session,
        theme: str,
        session_id: str,
        max_depth: int = 5
    ) -> Story:
        """Generate the root node of a new story."""
        story = Story(title=f"{theme.title()} Adventure", session_id=session_id, max_depth=max_depth)
        db.add(story)
        db.flush()
        
        # Generate root node via LLM
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(
            theme=theme,
            is_root=True,
            max_depth=max_depth
        )
        
        llm_data = self._call_llm(system_prompt, user_prompt)
        
        if llm_data:
            llm_data = self._validate_and_fix_response(llm_data, is_root=True, depth=0, max_depth=max_depth)
            node_data = self._convert_to_pydantic(llm_data)
            story_state = llm_data.get("story_state_updates", {})
        else:
            # Fallback
            node_data = self._fallback_root_node(theme)
            story_state = {"location": "starting area", "objectives": ["begin adventure"]}
        
        # Create root node
        root_node = self._create_node_from_llm(db, story.id, node_data, is_root=True, story_state=story_state)
        
        # Update story with initial state
        story.current_state = story_state
        db.commit()
        db.refresh(story)
        
        return story
    
    def generate_next_node(
        self,
        db: Session,
        story: Story,
        current_node: StoryNode,
        chosen_option_text: str,
        story_state: Dict,
        previous_choices: List[str],
        depth: int
    ) -> StoryNode:
        """Generate the next story node based on player's choice."""
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(
            theme=story.title.replace(" Adventure", ""),
            current_node_content=current_node.content,
            previous_choices=previous_choices + [chosen_option_text],
            story_state=story_state,
            is_root=False,
            depth=depth,
            max_depth=story.max_depth or 5
        )
        
        llm_data = self._call_llm(system_prompt, user_prompt)
        
        if llm_data:
            llm_data = self._validate_and_fix_response(
                llm_data, 
                is_root=False, 
                depth=depth, 
                max_depth=story.max_depth or 5
            )
            node_data = self._convert_to_pydantic(llm_data)
            new_state_updates = llm_data.get("story_state_updates", {})
        else:
            node_data = self._fallback_next_node(chosen_option_text)
            new_state_updates = {}
        
        # Merge story state
        merged_state = self._merge_story_state(story_state, new_state_updates)
        
        # Create new node
        new_node = self._create_node_from_llm(
            db, 
            story.id, 
            node_data, 
            is_root=False, 
            parent_node_id=current_node.id,
            story_state=merged_state,
            depth=depth + 1
        )
        
        # Update the chosen option in current node to point to new node
        self._update_option_target(db, current_node, chosen_option_text, new_node.id)
        
        # Update story's current state
        story.current_state = merged_state
        db.commit()
        
        return new_node
    
    def _create_node_from_llm(
        self,
        db: Session,
        story_id: int,
        node_data: StoryNodeLLM,
        is_root: bool = False,
        parent_node_id: int = None,
        story_state: Dict = None,
        depth: int = 0
    ) -> StoryNode:
        """Create a StoryNode from LLM data."""
        node = StoryNode(
            story_id=story_id,
            content=node_data.content,
            is_root=is_root,
            is_ending=node_data.isEnding,
            is_winning_ending=node_data.isWinningEnding,
            options=[],  # Will be populated after child nodes created
            parent_node_id=parent_node_id,
            depth=depth,
            story_state=story_state or {}
        )
        db.add(node)
        db.flush()
        
        # Process options recursively (for root node, we create all at once)
        if not node.is_ending and node_data.options:
            options = []
            for option_data in node_data.options:
                # For root node, generate all child nodes immediately
                # For subsequent nodes, we'll generate on demand
                if is_root:
                    next_node_llm = StoryNodeLLM.model_validate(option_data.nextNode)
                    child_node = self._create_node_from_llm(
                        db, story_id, next_node_llm, 
                        is_root=False, parent_node_id=node.id,
                        story_state=story_state, depth=depth + 1
                    )
                    options.append({"text": option_data.text, "node_id": child_node.id})
                else:
                    # For non-root, just store the option text, node will be generated on choice
                    options.append({"text": option_data.text, "node_id": None})
            
            node.options = options
            db.flush()
        
        return node
    
    def _update_option_target(self, db: Session, node: StoryNode, option_text: str, target_node_id: int):
        """Update an option's target node_id."""
        if not node.options:
            return
        for opt in node.options:
            if opt.get("text") == option_text:
                opt["node_id"] = target_node_id
                break
        db.flush()
    
    def _merge_story_state(self, current: Dict, updates: Dict) -> Dict:
        """Merge story state updates."""
        merged = current.copy() if current else {}
        
        for key, value in updates.items():
            if key in ["characters", "inventory", "events", "objectives", "important_decisions"]:
                # Merge lists, avoiding duplicates
                existing = merged.get(key, [])
                if isinstance(value, list):
                    for item in value:
                        if item not in existing:
                            existing.append(item)
                    merged[key] = existing
            elif key == "relationships":
                # Merge dicts
                existing = merged.get(key, {})
                if isinstance(value, dict):
                    existing.update(value)
                merged[key] = existing
            else:
                # Replace scalar values
                merged[key] = value
        
        return merged
    
    def _fallback_root_node(self, theme: str) -> StoryNodeLLM:
        """Fallback root node when LLM unavailable."""
        return StoryNodeLLM(
            content=f"Your {theme} adventure begins. You stand at a crossroads, the path ahead uncertain but full of possibility.",
            isEnding=False,
            isWinningEnding=False,
            options=[
                StoryOptionLLM(
                    text="Take the well-traveled road",
                    nextNode=StoryNodeLLM(content="The road leads to a bustling town.", isEnding=True, isWinningEnding=True, options=[])
                ),
                StoryOptionLLM(
                    text="Venture into the wild unknown",
                    nextNode=StoryNodeLLM(content="The wilderness holds dangers and secrets.", isEnding=True, isWinningEnding=False, options=[])
                ),
                StoryOptionLLM(
                    text="Seek guidance from a local",
                    nextNode=StoryNodeLLM(content="An old traveler shares a cryptic map.", isEnding=False, isWinningEnding=False, options=[])
                )
            ]
        )
    
    def _fallback_next_node(self, chosen_option: str) -> StoryNodeLLM:
        """Fallback next node when LLM unavailable."""
        return StoryNodeLLM(
            content=f"You chose: {chosen_option}. The path unfolds before you with new challenges and opportunities.",
            isEnding=False,
            isWinningEnding=False,
            options=[
                StoryOptionLLM(
                    text="Press forward with determination",
                    nextNode=StoryNodeLLM(content="Your determination leads to victory.", isEnding=True, isWinningEnding=True, options=[])
                ),
                StoryOptionLLM(
                    text="Pause to assess the situation",
                    nextNode=StoryNodeLLM(content="Careful observation reveals a hidden path.", isEnding=True, isWinningEnding=True, options=[])
                )
            ]
        )


# Singleton instance
story_generator_service = StoryGeneratorService()