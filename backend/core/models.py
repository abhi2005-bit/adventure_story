from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

class StoryOptionLLM(BaseModel):
    text: str = Field(description="The text of the option shown to the user")
    consequence: Optional[str] = Field(default=None, description="Brief description of what this choice might lead to")
    nextNode: Dict[str, Any] = Field(description="The next story node")


class StoryNodeLLM(BaseModel):
    content: str = Field(description="The main content of the story node")
    isEnding: bool = Field(description="Whether this node is an ending")
    isWinningEnding: bool = Field(description="Whether this node is a winning ending")
    options: Optional[List[StoryOptionLLM]] = Field(default=None, description="Options for this node")


class StoryLLMResponse(BaseModel):
    title: str = Field(description="The title of the story")
    rootNode: StoryNodeLLM = Field(description="The root node of the story")
