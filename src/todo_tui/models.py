"""Data models for todo-tui v2: Season > Sprint > Task hierarchy."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List


@dataclass
class Season:
    """4-month cycle season."""
    id: int
    name: str
    start_date: str  # YYYY-MM-DD
    end_date: str    # YYYY-MM-DD
    status: str = "active"  # active, expired, archived
    goals: str = ""
    created_at: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "status": self.status,
            "goals": self.goals,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Season":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def is_expired(self) -> bool:
        today = datetime.now().strftime("%Y-%m-%d")
        return self.end_date < today

    def get_progress(self) -> float:
        try:
            start = datetime.strptime(self.start_date, "%Y-%m-%d")
            end = datetime.strptime(self.end_date, "%Y-%m-%d")
            today = datetime.now()
            if today <= start:
                return 0.0
            elif today >= end:
                return 100.0
            else:
                total_days = (end - start).days
                elapsed_days = (today - start).days
                return round((elapsed_days / total_days) * 100, 1)
        except ValueError:
            return 0.0


@dataclass
class Sprint:
    """Weekly sprint within a season."""
    id: int
    season_id: int
    name: str
    start_date: str  # YYYY-MM-DD
    end_date: str    # YYYY-MM-DD
    status: str = "active"  # active, completed
    goal: str = ""
    created_at: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "season_id": self.season_id,
            "name": self.name,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "status": self.status,
            "goal": self.goal,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Sprint":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def contains_date(self, date_str: str) -> bool:
        return self.start_date <= date_str <= self.end_date


@dataclass
class Task:
    """Individual task within a sprint."""
    id: int
    content: str
    sprint_id: Optional[int] = None
    season_id: Optional[int] = None
    status: str = "todo"  # todo, in_progress, done
    priority: str = "medium"  # high, medium, low
    memo: str = ""
    due_date: Optional[str] = None
    created_at: str = ""
    completed_at: Optional[str] = None
    order: int = 0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "content": self.content,
            "sprint_id": self.sprint_id,
            "season_id": self.season_id,
            "status": self.status,
            "priority": self.priority,
            "memo": self.memo,
            "due_date": self.due_date,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "order": self.order,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# MCP compatibility classes - kept for todo_mcp_server.py
@dataclass
class Plan:
    """Plan model for MCP server compatibility."""
    id: int
    name: str
    status: str = "active"
    created_at: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Plan":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class HistoryEntry:
    """History entry for MCP server compatibility."""
    id: int
    plan_id: int
    content: str
    entry_type: str = "log"  # log, decision, issue
    created_at: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "plan_id": self.plan_id,
            "content": self.content,
            "entry_type": self.entry_type,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "HistoryEntry":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
