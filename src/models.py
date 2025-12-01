from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship


class Participation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    activity_id: int = Field(foreign_key="activity.id")
    student_id: int = Field(foreign_key="student.id")


class Activity(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    description: Optional[str] = None
    schedule: Optional[str] = None
    max_participants: int = 0

    participants: List[Participation] = Relationship(back_populates="activity")


class Student(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    name: Optional[str] = None
    grade: Optional[str] = None

    participations: List[Participation] = Relationship(back_populates="student")


# Setup relationships on Participation side
Participation.activity = Relationship(sa_relationship_kwargs={"lazy": "selectin"}, back_populates="participants")
Participation.student = Relationship(sa_relationship_kwargs={"lazy": "selectin"}, back_populates="participations")
