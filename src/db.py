import os
from sqlmodel import SQLModel, create_engine, Session
from typing import Generator

# Use DATABASE_URL if set, otherwise fallback to sqlite for local dev
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./mergington.db")

engine = create_engine(DATABASE_URL, echo=False)


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
