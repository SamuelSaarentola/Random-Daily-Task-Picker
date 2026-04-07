import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import random
from datetime import datetime, timezone, timedelta
from typing import List

from fastapi import FastAPI, Depends, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import engine, Base, get_db
from models import (
    Task,
    TaskCreate,
    TaskUpdate,
    TaskSuggest,
    ReorderItem,
    TaskResponse,
)

# Create tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Mitä tänään?")

# CORS — allow all origins (local use only)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Seed default tasks if the table is empty
def seed_tasks():
    from database import SessionLocal
    db = SessionLocal()
    try:
        count = db.query(func.count(Task.id)).scalar()
        if count == 0:
            defaults = [
                {"name": "Play a game", "cooldown_days": 2},
                {"name": "Draw", "cooldown_days": 1},
                {"name": "Coloring book", "cooldown_days": 1},
                {"name": "Minecraft", "cooldown_days": 2},
                {"name": "Outside 30min", "cooldown_days": 1},
                {"name": "Learn to type", "cooldown_days": 1},
                {"name": "Read 30min", "cooldown_days": 1},
                {"name": "Watch 1 episode", "cooldown_days": 1},
            ]
            for i, d in enumerate(defaults):
                t = Task(**d, sort_order=i)
                db.add(t)
            db.commit()
    finally:
        db.close()


seed_tasks()


# --- Static files ---
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
index_path = os.path.join(frontend_dir, "index.html")
todo_path = os.path.join(frontend_dir, "todo.html")

# Serve static assets (JS, CSS, etc.) from /static/
app.mount("/static", StaticFiles(directory=frontend_dir), name="static")


@app.get("/")
def serve_index():
    if os.path.isfile(index_path):
        return FileResponse(index_path)
    return Response(status_code=404)


@app.get("/todo")
def serve_todo():
    if os.path.isfile(todo_path):
        return FileResponse(todo_path)
    return Response(status_code=404)


# --- Helper ---
def get_available_tasks(db: Session) -> List[Task]:
    """Return active tasks whose cooldown has passed, computed in Python."""
    all_tasks = db.query(Task).filter(Task.active == True).order_by(Task.sort_order).all()
    now = datetime.now(timezone.utc)
    available = []
    for t in all_tasks:
        if t.last_done is None:
            available.append(t)
        else:
            last_done = t.last_done
            if last_done.tzinfo is None:
                last_done = last_done.replace(tzinfo=timezone.utc)
            cooldown_end = last_done + timedelta(days=t.cooldown_days)
            if now >= cooldown_end:
                available.append(t)
    return available


# --- Endpoints ---

@app.get("/api/tasks", response_model=List[TaskResponse])
def list_tasks(db: Session = Depends(get_db)):
    tasks = db.query(Task).order_by(Task.sort_order).all()
    return [TaskResponse.from_orm(t) for t in tasks]


@app.get("/api/tasks/available/count")
def available_count(db: Session = Depends(get_db)):
    """Return count of tasks that are currently available (not on cooldown)."""
    available = get_available_tasks(db)
    return {"count": len(available)}


@app.get("/api/tasks/active/names")
def active_task_names(db: Session = Depends(get_db)):
    """Return list of active task names for the home screen animation."""
    tasks = db.query(Task.name).filter(Task.active == True).all()
    return {"names": [t.name for t in tasks]}


@app.get("/api/tasks/random")
def random_task(db: Session = Depends(get_db), response: Response = None):
    available = get_available_tasks(db)
    if not available:
        return Response(status_code=204)
    picked = random.choice(available)
    return TaskResponse.from_orm(picked)


@app.post("/api/tasks", response_model=TaskResponse, status_code=201)
def create_task(body: TaskCreate, db: Session = Depends(get_db)):
    # Get max sort_order
    max_order = db.query(func.max(Task.sort_order)).scalar() or 0
    task = Task(
        name=body.name,
        cooldown_days=body.cooldown_days,
        sort_order=max_order + 1,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return TaskResponse.from_orm(task)


@app.put("/api/tasks/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, body: TaskUpdate, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if body.name is not None:
        task.name = body.name
    if body.cooldown_days is not None:
        task.cooldown_days = body.cooldown_days
    if body.active is not None:
        task.active = body.active
    db.commit()
    db.refresh(task)
    return TaskResponse.from_orm(task)


@app.delete("/api/tasks/{task_id}", status_code=204)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
    return Response(status_code=204)


@app.post("/api/tasks/{task_id}/done", response_model=TaskResponse)
def mark_done(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.last_done = datetime.now(timezone.utc)
    db.commit()
    db.refresh(task)
    return TaskResponse.from_orm(task)


# Use POST for reorder to avoid conflict with PUT /api/tasks/{task_id}
@app.post("/api/tasks/reorder", status_code=204)
def reorder_tasks(items: List[ReorderItem], db: Session = Depends(get_db)):
    for item in items:
        task = db.query(Task).filter(Task.id == item.id).first()
        if task:
            task.sort_order = item.sort_order
    db.commit()
    return Response(status_code=204)


@app.post("/api/tasks/{task_id}/reset-cooldown", response_model=TaskResponse)
def reset_cooldown(task_id: int, db: Session = Depends(get_db)):
    """Reset task cooldown by clearing last_done timestamp."""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.last_done = None
    db.commit()
    db.refresh(task)
    return TaskResponse.from_orm(task)


@app.post("/api/tasks/suggest", response_model=TaskResponse, status_code=201)
def suggest_task(body: TaskSuggest, db: Session = Depends(get_db)):
    """Add a user-suggested task (disabled by default, parent must enable)."""
    # Check if task with same name already exists
    existing = db.query(Task).filter(Task.name == body.name).first()
    if existing:
        return TaskResponse.from_orm(existing)
    # Get max sort_order
    max_order = db.query(func.max(Task.sort_order)).scalar() or 0
    task = Task(
        name=body.name.strip(),
        cooldown_days=1,
        sort_order=max_order + 1,
        active=False,  # Disabled by default
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return TaskResponse.from_orm(task)
