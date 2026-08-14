from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.db.database import Base


class Story(Base):
    __tablename__ = "stories"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    session_id = Column(String, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    current_state = Column(JSON, default=dict)
    max_depth = Column(Integer, default=5)

    nodes = relationship("StoryNode", back_populates="story", cascade="all, delete-orphan")


class StoryNode(Base):
    __tablename__ = "storynodes"

    id = Column(Integer, primary_key=True, index=True)
    story_id = Column(Integer, ForeignKey("stories.id"), index=True)
    content = Column(String)
    options = Column(JSON, default=list)
    is_root = Column(Boolean, default=False)
    is_ending = Column(Boolean, default=False)
    is_winning_ending = Column(Boolean, default=False)
    parent_node_id = Column(Integer, ForeignKey("storynodes.id"), nullable=True)
    depth = Column(Integer, default=0)
    story_state = Column(JSON, default=dict)

    story = relationship("Story", back_populates="nodes")
    parent = relationship("StoryNode", remote_side=[id], backref="children")