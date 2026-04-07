from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel
from sqlalchemy import Column, Integer, Text, Boolean, DateTime

from database import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)
    cooldown_days = Column(Integer, nullable=False, default=1)
    last_done = Column(DateTime, nullable=True)
    sort_order = Column(Integer, nullable=False, default=0)
    active = Column(Boolean, nullable=False, default=True)


# --- Pydantic schemas ---

class TaskCreate(BaseModel):
    name: str
    cooldown_days: int = 1


class TaskUpdate(BaseModel):
    name: Optional[str] = None
    cooldown_days: Optional[int] = None
    active: Optional[bool] = None


class ReorderItem(BaseModel):
    id: int
    sort_order: int


class TaskSuggest(BaseModel):
    name: str


class TaskResponse(BaseModel):
    id: int
    name: str
    cooldown_days: int
    last_done: Optional[str]
    sort_order: int
    active: bool
    available: bool
    available_at: Optional[str]

    @staticmethod
    def from_orm(task: Task) -> "TaskResponse":
        now = datetime.now(timezone.utc)
        available = True
        available_at = None

        if task.last_done is not None:
            # Make last_done timezone-aware if it isn't already
            last_done = task.last_done
            if last_done.tzinfo is None:
                last_done = last_done.replace(tzinfo=timezone.utc)

            from datetime import timedelta
            available_at_dt = last_done + timedelta(days=task.cooldown_days)
            available_at_str = available_at_dt.strftime("%Y-%m-%dT%H:%M:%S")

            if now >= available_at_dt:
                available = True
                available_at = None
            else:
                available = False
                available_at = available_at_str

        last_done_str = None
        if task.last_done is not None:
            ld = task.last_done
            if ld.tzinfo is None:
                ld = ld.replace(tzinfo=timezone.utc)
            last_done_str = ld.strftime("%Y-%m-%dT%H:%M:%S")

        return TaskResponse(
            id=task.id,
            name=task.name,
            cooldown_days=task.cooldown_days,
            last_done=last_done_str,
            sort_order=task.sort_order,
            active=task.active,
            available=available,
            available_at=available_at,
        )
