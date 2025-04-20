from sqlmodel import SQLModel, create_engine, Session
from .config import get_settings

settings = get_settings()
engine = create_engine(settings.SQLITE_DB, echo=False)

def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
