import uuid
from typing import Optional, List
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
    CompleteStoryNodeSchema,
    CreateStoryRequest,
    ChoiceRequest,
    ChoiceResponse
)
from backend.schemas.job import StoryJobSchema
from backend.services.story_generator import story_generator_service

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

        story = story_generator_service.generate_root_node(
            db=db,
            theme=theme,
            session_id=session_id,
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


@router.post("/{story_id}/choice", response_model=ChoiceResponse)
def make_choice(
    story_id: int,
    request: ChoiceRequest,
    db: Session = Depends(get_db)
):
    """Submit a choice and generate the next story node."""
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    
    current_node = db.query(StoryNode).filter(
        StoryNode.id == request.current_node_id,
        StoryNode.story_id == story_id
    ).first()
    if not current_node:
        raise HTTPException(status_code=404, detail="Current node not found")
    
    if current_node.is_ending:
        raise HTTPException(status_code=400, detail="Story has already ended")
    
    # Find the chosen option
    chosen_option = None
    for opt in current_node.options or []:
        if opt.get("text") == request.option_text:
            chosen_option = opt
            break
    
    if not chosen_option:
        raise HTTPException(status_code=400, detail="Invalid choice")
    
    # If the option already has a target node, use it
    if chosen_option.get("node_id"):
        next_node = db.query(StoryNode).filter(
            StoryNode.id == chosen_option["node_id"],
            StoryNode.story_id == story_id
        ).first()
        if next_node:
            return build_choice_response(story, next_node)
    
    # Otherwise, generate the next node
    # Build previous choices list from the path to current node
    previous_choices = build_previous_choices(db, current_node)
    
    next_node = story_generator_service.generate_next_node(
        db=db,
        story=story,
        current_node=current_node,
        chosen_option_text=request.option_text,
        story_state=story.current_state or {},
        previous_choices=previous_choices,
        depth=current_node.depth
    )
    
    return build_choice_response(story, next_node)


def build_previous_choices(db: Session, node: StoryNode) -> List[str]:
    """Build list of previous choices from root to current node."""
    choices = []
    current = node
    while current.parent_node_id:
        parent = db.query(StoryNode).filter(StoryNode.id == current.parent_node_id).first()
        if parent and parent.options:
            for opt in parent.options:
                if opt.get("node_id") == current.id:
                    choices.insert(0, opt.get("text", ""))
                    break
        current = parent
    return choices


def build_choice_response(story: Story, current_node: StoryNode) -> ChoiceResponse:
    """Build the response for a choice submission."""
    complete_story = build_complete_story_tree(story)
    current_node_schema = build_node_schema(current_node)
    
    return ChoiceResponse(
        story=complete_story,
        current_node=current_node_schema,
        is_ending=current_node.is_ending,
        is_winning_ending=current_node.is_winning_ending
    )


def get_story_complete_by_id(story_id: int, db: Session) -> CompleteStorySchema:
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    return build_complete_story_tree(story)


def build_complete_story_tree(story: Story) -> CompleteStorySchema:
    nodes = story.nodes
    all_nodes = {}
    root_node = None

    for node in nodes:
        node_schema = build_node_schema(node)
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
        current_state=story.current_state or {},
        max_depth=story.max_depth,
        root_nodes=root_node,
        all_nodes=all_nodes,
    )


def build_node_schema(node: StoryNode) -> CompleteStoryNodeSchema:
    """Build a CompleteStoryNodeSchema from a StoryNode."""
    options = []
    for opt in node.options or []:
        options.append({
            "text": opt.get("text", ""),
            "node_id": opt.get("node_id"),
            "consequence": opt.get("consequence")
        })
    
    return CompleteStoryNodeSchema(
        id=node.id,
        content=node.content,
        is_ending=node.is_ending,
        is_winning_ending=node.is_winning_ending,
        depth=node.depth,
        story_state=node.story_state or {},
        options=options,
        parent_node_id=node.parent_node_id
    )
