import uuid
from typing import Optional
from datetime import datetime

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Cookie,
    Depends,
    HTTPException,
    Response,
)

from sqlalchemy.orm import Session

from backend.db.database import get_db, SessionLocal
from backend.models.job import StoryJob
from backend.models.story import Story, StoryNode
from backend.schemas.story import (
    CompleteStorySchema,
    CreateStoryRequest
)
from backend.schemas.job import StoryJobSchema
from backend.core.story_generator import StoryGenerator

router = APIRouter(
    prefix="/story",
    tags=["stories"]
)


def get_session_id(session_id: Optional[str] = Cookie(None)):
    if not session_id:
        session_id = str(uuid.uuid4())

    return session_id


@router.post("/create", response_model=StoryJobSchema)
def create_story(
    request: CreateStoryRequest,
    background_tasks: BackgroundTasks,
    response: Response,
    session_id: str = Depends(get_session_id),
    db: Session = Depends(get_db)
):
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True
    )

    job_id = str(uuid.uuid4())

    job = StoryJob(
        job_id=job_id,
        session_id=session_id,
        theme=request.theme,
        status="pending"
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    background_tasks.add_task(
        generate_story_task,
        job_id=job_id,
        theme=request.theme,
        session_id=session_id
    )

    return job


def generate_story_task(
    job_id: str,
    session_id: str,
    theme: str
):
    db = SessionLocal()

    try:
        job = db.query(StoryJob).filter(
            StoryJob.job_id == job_id
        ).first()

        if not job:
            return

        job.status = "processing"
        db.commit()

        story = StoryGenerator.generate_story(
            db=db,
            session_id=session_id,
            theme=theme,
        )

        job.story_id = story.id

        job.status = "completed"
        job.completed_at = datetime.now()

        db.commit()

    except Exception as e:
        if "job" in locals() and job:
            job.status = "failed"
            job.completed_at = datetime.now()
            job.error = str(e)
            db.commit()

    finally:
        db.close()


@router.get("/job/{job_id}/complete", response_model=CompleteStorySchema)
def get_complete_story_by_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(StoryJob).filter(StoryJob.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status in {"pending", "processing"}:
        raise HTTPException(
            status_code=409,
            detail="Story generation is still in progress. Please wait for the job to finish.",
        )

    if job.story_id is None:
        raise HTTPException(
            status_code=409,
            detail="Story generation has not produced a story yet.",
        )

    return get_story_complete_by_id(job.story_id, db)


@router.get("/{story_id}/complete", response_model=CompleteStorySchema)
def get_complete_story(story_id: int, db: Session = Depends(get_db)):
    return get_story_complete_by_id(story_id, db)


def get_story_complete_by_id(story_id: int, db: Session) -> CompleteStorySchema:
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    return build_complete_story_tree(db, story)


def build_complete_story_tree(db: Session, story: Story) -> CompleteStorySchema:
    nodes = db.query(StoryNode).filter(StoryNode.story_id == story.id).all()
    all_nodes = {}
    root_node = None

    for node in nodes:
        node_schema = {
            "id": node.id,
            "content": node.content,
            "options": node.options or [],
            "is_ending": node.is_ending,
            "is_winning_ending": node.is_winning_ending,
        }
        all_nodes[node.id] = node_schema
        if node.is_root:
            root_node = node_schema

    if root_node is None:
        raise HTTPException(status_code=404, detail="Story root node not found")

    return CompleteStorySchema(
        id=story.id,
        title=story.title,
        session_id=story.session_id,
        created_at=story.created_at,
        root_nodes=root_node,
        all_nodes=all_nodes,
    )
