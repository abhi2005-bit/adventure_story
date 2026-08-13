from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class StoryOptionSchema(BaseModel):
    text: str
    node_id: Optional[int] = None


class StoryNodeBase(BaseModel):
    content: str
    is_ending: bool = False
    is_winning_ending: bool = False


class CompleteStoryNodeSchema(StoryNodeBase):
    id: int
    options: List[StoryOptionSchema] = Field(default_factory=list)

    class Config:
        from_attributes = True


class StoryBase(BaseModel):
    title: str
    session_id: Optional[str] = None

    class Config:
        from_attributes = True


class CreateStoryRequest(BaseModel):
    theme: str


class CompleteStorySchema(StoryBase):
    id: int
    created_at: datetime
    root_nodes: CompleteStoryNodeSchema
    all_nodes: Dict[int, CompleteStoryNodeSchema]

    class Config:
        from_attributes = True
