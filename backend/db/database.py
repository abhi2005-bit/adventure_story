from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base

from backend.core.config import settings

url = make_url(settings.DATABASE_URL)
if url.drivername == "sqlite" and url.database and url.database != ":memory:":
    Path(url.database).parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    import backend.models.job
    import backend.models.story

    Base.metadata.create_all(bind=engine)
