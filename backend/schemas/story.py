from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class StoryOptionSchema(BaseModel):
    text: str
    node_id: Optional[int] = None
    consequence: Optional[str] = None


class StoryNodeBase(BaseModel):
    content: str
    is_ending: bool = False
    is_winning_ending: bool = False
    depth: int = 0
    story_state: Dict = Field(default_factory=dict)


class CompleteStoryNodeSchema(StoryNodeBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    options: List[StoryOptionSchema] = Field(default_factory=list)
    parent_node_id: Optional[int] = None


class StoryBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    title: str
    session_id: Optional[str] = None
    current_state: Dict = Field(default_factory=dict)
    max_depth: int = 5


class CreateStoryRequest(BaseModel):
    theme: str


class CompleteStorySchema(StoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    root_nodes: CompleteStoryNodeSchema
    all_nodes: Dict[int, CompleteStoryNodeSchema]


class ChoiceRequest(BaseModel):
    option_text: str
    current_node_id: int


class ChoiceResponse(BaseModel):
    story: CompleteStorySchema
    current_node: CompleteStoryNodeSchema
    is_ending: bool
    is_winning_ending: bool
