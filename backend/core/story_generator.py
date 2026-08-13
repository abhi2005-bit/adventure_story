from sqlalchemy.orm import Session

from backend.core.models import StoryLLMResponse, StoryNodeLLM
from backend.models.story import Story, StoryNode
from dotenv import load_dotenv

load_dotenv()

class StoryGenerator:
    @classmethod
    def generate_story(cls, db: Session, session_id: str, theme: str = "fantasy") -> Story:
        story_structure = cls._fallback_story(theme)

        story = Story(title=story_structure.title, session_id=session_id)
        db.add(story)
        db.flush()

        cls._process_story_node(db, story.id, story_structure.rootNode, is_root=True)
        db.commit()
        db.refresh(story)
        return story

    @classmethod
    def _fallback_story(cls, theme: str) -> StoryLLMResponse:
        return StoryLLMResponse(
            title=f"{theme.title()} Adventure",
            rootNode=StoryNodeLLM(
                content=f"Your {theme} adventure begins at a fork in the road.",
                isEnding=False,
                isWinningEnding=False,
                options=[
                    {
                        "text": "Take the bright path",
                        "nextNode": {
                            "content": "The path opens into a safe clearing. You find the treasure and win.",
                            "isEnding": True,
                            "isWinningEnding": True,
                            "options": [],
                        },
                    },
                    {
                        "text": "Enter the dark tunnel",
                        "nextNode": {
                            "content": "The tunnel collapses behind you. Your adventure ends here.",
                            "isEnding": True,
                            "isWinningEnding": False,
                            "options": [],
                        },
                    },
                ],
            ),
        )

    @classmethod
    def _process_story_node(
        cls,
        db: Session,
        story_id: int,
        node_data: StoryNodeLLM,
        is_root: bool = False,
    ) -> StoryNode:
        node = StoryNode(
            story_id=story_id,
            content=node_data.content,
            is_root=is_root,
            is_ending=node_data.isEnding,
            is_winning_ending=node_data.isWinningEnding,
            options=[],
        )
        db.add(node)
        db.flush()

        options = []
        if not node.is_ending and node_data.options:
            for option_data in node_data.options:
                next_node = StoryNodeLLM.model_validate(option_data.nextNode)
                child_node = cls._process_story_node(db, story_id, next_node)
                options.append({"text": option_data.text, "node_id": child_node.id})

        node.options = options
        db.flush()
        return node
