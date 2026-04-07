import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import random
from datetime import datetime, timezone, timedelta
from typing import List

from fastapi import FastAPI, Depends, HTTPException, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel
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

# --- Auth config ---
AUTH_USERNAME = os.environ.get("AUTH_USERNAME", "admin")
AUTH_PASSWORD = os.environ.get("AUTH_PASSWORD", "admin")
AUTH_SECRET = os.environ.get("AUTH_SECRET", "change-this-secret-key")

class AuthLogin(BaseModel):
    username: str
    password: str

# Create tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Mitä tänään?")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session middleware for cookie-based auth
app.add_middleware(
    SessionMiddleware,
    secret_key=AUTH_SECRET,
    session_cookie="taskpicker_auth",
    max_age=86400 * 30,
    same_site="lax",
    https_only=False,
)


def require_auth(request: Request):
    """Dependency: raises 401 if not authenticated."""
    if not request.session.get("authenticated"):
        raise HTTPException(status_code=401, detail="Not authenticated")


# --- Seed ---
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


# --- Static ---
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
index_path = os.path.join(frontend_dir, "index.html")
todo_path = os.path.join(frontend_dir, "todo.html")

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


# --- Auth endpoints ---
@app.post("/api/auth/login")
async def login(request: Request, body: AuthLogin):
    if body.username == AUTH_USERNAME and body.password == AUTH_PASSWORD:
        request.session["authenticated"] = True
        return {"ok": True}
    raise HTTPException(status_code=401, detail="Väärä tunnus tai salasana")


@app.post("/api/auth/logout")
async def logout(request: Request):
    request.session.clear()
    return {"ok": True}


@app.get("/api/auth/check")
async def auth_check(request: Request):
    return {"authenticated": bool(request.session.get("authenticated"))}


# --- Task endpoints ---

@app.get("/api/tasks", response_model=List[TaskResponse])
def list_tasks(db: Session = Depends(get_db)):
    tasks = db.query(Task).order_by(Task.sort_order).all()
    return [TaskResponse.from_orm(t) for t in tasks]


@app.get("/api/tasks/available/count")
def available_count(db: Session = Depends(get_db)):
    available = get_available_tasks(db)
    return {"count": len(available)}


@app.get("/api/tasks/active/names")
def active_task_names(db: Session = Depends(get_db)):
    tasks = db.query(Task.name).filter(Task.active == True).all()
    return {"names": [t.name for t in tasks]}


@app.get("/api/tasks/random")
def random_task(db: Session = Depends(get_db)):
    available = get_available_tasks(db)
    if not available:
        return Response(status_code=204)
    picked = random.choice(available)
    return TaskResponse.from_orm(picked)


# Public: mark done (anyone can complete a task)
@app.post("/api/tasks/{task_id}/done", response_model=TaskResponse)
def mark_done(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.last_done = datetime.now(timezone.utc)
    db.commit()
    db.refresh(task)
    return TaskResponse.from_orm(task)


# Public: suggest (adds as inactive)
@app.post("/api/tasks/suggest", response_model=TaskResponse, status_code=201)
def suggest_task(body: TaskSuggest, db: Session = Depends(get_db)):
    existing = db.query(Task).filter(Task.name == body.name).first()
    if existing:
        return TaskResponse.from_orm(existing)
    max_order = db.query(func.max(Task.sort_order)).scalar() or 0
    task = Task(
        name=body.name.strip(),
        cooldown_days=1,
        sort_order=max_order + 1,
        active=False,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return TaskResponse.from_orm(task)


# --- Protected management endpoints ---

@app.post("/api/tasks", response_model=TaskResponse, status_code=201)
def create_task(body: TaskCreate, db: Session = Depends(get_db), _: None = Depends(require_auth)):
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
def update_task(task_id: int, body: TaskUpdate, db: Session = Depends(get_db), _: None = Depends(require_auth)):
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
def delete_task(task_id: int, db: Session = Depends(get_db), _: None = Depends(require_auth)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
    return Response(status_code=204)


@app.post("/api/tasks/reorder", status_code=204)
def reorder_tasks(items: List[ReorderItem], db: Session = Depends(get_db), _: None = Depends(require_auth)):
    for item in items:
        task = db.query(Task).filter(Task.id == item.id).first()
        if task:
            task.sort_order = item.sort_order
    db.commit()
    return Response(status_code=204)


@app.post("/api/tasks/{task_id}/reset-cooldown", response_model=TaskResponse)
def reset_cooldown(task_id: int, db: Session = Depends(get_db), _: None = Depends(require_auth)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.last_done = None
    db.commit()
    db.refresh(task)
    return TaskResponse.from_orm(task)
