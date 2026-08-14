from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class StoryJobBase(BaseModel):
    theme: str


class StoryJobSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    job_id: str
    status: str
    created_at: datetime
    story_id: Optional[int] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


class StoryJobCreate(StoryJobBase):
    pass
