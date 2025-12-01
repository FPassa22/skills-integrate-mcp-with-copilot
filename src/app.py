"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
from pathlib import Path
from sqlmodel import select
from sqlmodel import Session as SqlSession
from .db import create_db_and_tables, get_session, engine
from .models import Activity, Student, Participation

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")


@app.on_event("startup")
def on_startup():
    # Create the DB tables
    create_db_and_tables()
    # Seed initial data if DB is empty
    with SqlSession(engine) as session:
        activities_count = session.exec(select(Activity)).all()
        if not activities_count:
            # Seed some students
            s1 = Student(email="michael@mergington.edu", name="Michael")
            s2 = Student(email="daniel@mergington.edu", name="Daniel")
            s3 = Student(email="emma@mergington.edu", name="Emma")
            session.add_all([s1, s2, s3])
            session.commit()
            session.refresh(s1)
            session.refresh(s2)
            session.refresh(s3)

            # Seed activities
            act_chess = Activity(name="Chess Club", description="Learn strategies and compete in chess tournaments", schedule="Fridays, 3:30 PM - 5:00 PM", max_participants=12)
            act_prog = Activity(name="Programming Class", description="Learn programming fundamentals and build software projects", schedule="Tuesdays and Thursdays, 3:30 PM - 4:30 PM", max_participants=20)
            session.add_all([act_chess, act_prog])
            session.commit()
            session.refresh(act_chess)
            session.refresh(act_prog)

            # Add participations
            p1 = Participation(activity_id=act_chess.id, student_id=s1.id)
            p2 = Participation(activity_id=act_chess.id, student_id=s2.id)
            p3 = Participation(activity_id=act_prog.id, student_id=s3.id)
            session.add_all([p1, p2, p3])
            session.commit()



@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities(session: SqlSession = Depends(get_session)):
    results = session.exec(select(Activity)).all()
    out = {}
    for act in results:
        # Fetch participant emails
        parts = session.exec(select(Participation).where(Participation.activity_id == act.id)).all()
        emails = []
        for p in parts:
            st = session.get(Student, p.student_id)
            if st:
                emails.append(st.email)
        out[act.name] = {
            "description": act.description,
            "schedule": act.schedule,
            "max_participants": act.max_participants,
            "participants": emails,
        }
    return out


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str, session: SqlSession = Depends(get_session)):
    """Sign up a student for an activity"""
    # Validate activity exists
    # Validate activity exists in DB
    statement = select(Activity).where(Activity.name == activity_name)
    act = session.exec(statement).one_or_none()
    if not act:
        raise HTTPException(status_code=404, detail="Activity not found")

    # find or create student
    st = session.exec(select(Student).where(Student.email == email)).one_or_none()
    if not st:
        st = Student(email=email)
        session.add(st)
        session.commit()
        session.refresh(st)

    # Validate student isn't already signed up
    existing = session.exec(select(Participation).where(Participation.activity_id == act.id, Participation.student_id == st.id)).one_or_none()
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Add student
    # Check capacity
    parts_list = session.exec(select(Participation).where(Participation.activity_id == act.id)).all()
    count = len(parts_list)
    if act.max_participants and count >= act.max_participants:
        raise HTTPException(status_code=400, detail="Activity is at full capacity")

    part = Participation(activity_id=act.id, student_id=st.id)
    session.add(part)
    session.commit()
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str, session: SqlSession = Depends(get_session)):
    """Unregister a student from an activity"""
    # Validate activity exists
    statement = select(Activity).where(Activity.name == activity_name)
    act = session.exec(statement).one_or_none()
    if not act:
        raise HTTPException(status_code=404, detail="Activity not found")

    st = session.exec(select(Student).where(Student.email == email)).one_or_none()
    if not st:
        raise HTTPException(status_code=400, detail="Student is not signed up for this activity")

    existing = session.exec(select(Participation).where(Participation.activity_id == act.id, Participation.student_id == st.id)).one_or_none()
    if not existing:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    session.delete(existing)
    session.commit()
    return {"message": f"Unregistered {email} from {activity_name}"}
