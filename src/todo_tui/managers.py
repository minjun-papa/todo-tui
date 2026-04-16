"""Managers for Season, Sprint, and Task CRUD operations."""

import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from .models import Season, Sprint, Task


class SeasonManager:
    """Season CRUD and queries."""

    def __init__(self, save_dir: Path):
        self.save_dir = save_dir
        self.save_dir.mkdir(parents=True, exist_ok=True)
        self.seasons_file = self.save_dir / "seasons.json"
        self.seasons: List[Season] = []
        self.current_season_id: Optional[int] = None
        self._load()

    def _load(self):
        if not self.seasons_file.exists():
            self.seasons = []
            return
        try:
            with open(self.seasons_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.seasons = [Season.from_dict(item) for item in data]
            active = [s for s in self.seasons if s.status == "active"]
            if active:
                self.current_season_id = active[-1].id
        except (json.JSONDecodeError, KeyError):
            self.seasons = []

    def _save(self):
        with open(self.seasons_file, "w", encoding="utf-8") as f:
            json.dump([s.to_dict() for s in self.seasons], f, indent=2, ensure_ascii=False)

    def create(self, name: str, start_date: str, end_date: str, goals: str = "") -> Season:
        new_id = max([s.id for s in self.seasons], default=0) + 1
        season = Season(
            id=new_id,
            name=name,
            start_date=start_date,
            end_date=end_date,
            status="active",
            goals=goals,
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        self.seasons.append(season)
        self._save()
        return season

    def get(self, season_id: int) -> Optional[Season]:
        return next((s for s in self.seasons if s.id == season_id), None)

    def get_current(self) -> Optional[Season]:
        if self.current_season_id:
            return self.get(self.current_season_id)
        return None

    def set_current(self, season_id: int):
        if any(s.id == season_id for s in self.seasons):
            self.current_season_id = season_id

    def get_active(self) -> List[Season]:
        return [s for s in self.seasons if s.status == "active"]

    def get_archived(self) -> List[Season]:
        return [s for s in self.seasons if s.status in ("archived", "expired")]

    def get_all(self) -> List[Season]:
        return self.seasons

    def archive(self, season_id: int):
        season = self.get(season_id)
        if season:
            season.status = "archived"
            self._save()

    def check_expired(self):
        for season in self.seasons:
            if season.status == "active" and season.is_expired():
                season.status = "expired"
        self._save()


class SprintManager:
    """Sprint CRUD and weekly sprint management."""

    def __init__(self, save_dir: Path, season_manager: SeasonManager):
        self.save_dir = save_dir
        self.save_dir.mkdir(parents=True, exist_ok=True)
        self.sprints_file = self.save_dir / "sprints.json"
        self.season_manager = season_manager
        self.sprints: List[Sprint] = []
        self._load()

    def _load(self):
        if not self.sprints_file.exists():
            self.sprints = []
            return
        try:
            with open(self.sprints_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.sprints = [Sprint.from_dict(item) for item in data]
        except (json.JSONDecodeError, KeyError):
            self.sprints = []

    def _save(self):
        with open(self.sprints_file, "w", encoding="utf-8") as f:
            json.dump([s.to_dict() for s in self.sprints], f, indent=2, ensure_ascii=False)

    def create(self, name: str, season_id: int, start_date: str, end_date: str, goal: str = "") -> Sprint:
        new_id = max([s.id for s in self.sprints], default=0) + 1
        sprint = Sprint(
            id=new_id,
            season_id=season_id,
            name=name,
            start_date=start_date,
            end_date=end_date,
            status="active",
            goal=goal,
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        self.sprints.append(sprint)
        self._save()
        return sprint

    def get(self, sprint_id: int) -> Optional[Sprint]:
        return next((s for s in self.sprints if s.id == sprint_id), None)

    def get_for_season(self, season_id: int) -> List[Sprint]:
        return [s for s in self.sprints if s.season_id == season_id]

    def get_active_for_season(self, season_id: int) -> List[Sprint]:
        return [s for s in self.sprints if s.season_id == season_id and s.status == "active"]

    def get_current_sprint(self, season_id: Optional[int] = None) -> Optional[Sprint]:
        """Get the sprint containing today's date."""
        today = datetime.now().strftime("%Y-%m-%d")
        if season_id:
            candidates = [s for s in self.sprints if s.season_id == season_id]
        else:
            candidates = self.sprints
        for sprint in candidates:
            if sprint.contains_date(today):
                return sprint
        return None

    def auto_create_weekly_sprint(self, season_id: int) -> Sprint:
        """Create a weekly sprint for the current week if none exists."""
        today = datetime.now()
        # Monday of current week
        start = today - timedelta(days=today.weekday())
        end = start + timedelta(days=6)
        start_str = start.strftime("%Y-%m-%d")
        end_str = end.strftime("%Y-%m-%d")

        # Check if a sprint already covers today
        today_str = today.strftime("%Y-%m-%d")
        for s in self.sprints:
            if s.season_id == season_id and s.start_date <= today_str <= s.end_date:
                return s

        # Generate sprint number
        existing = self.get_for_season(season_id)
        sprint_num = len(existing) + 1
        name = f"Sprint {sprint_num} ({start.strftime('%b %d')} - {end.strftime('%b %d')})"

        return self.create(name, season_id, start_str, end_str)

    def complete(self, sprint_id: int):
        sprint = self.get(sprint_id)
        if sprint:
            sprint.status = "completed"
            self._save()

    def get_stats(self, sprint_id: int, task_manager: "TaskManager") -> dict:
        tasks = task_manager.get_by_sprint(sprint_id)
        total = len(tasks)
        done = sum(1 for t in tasks if t.status == "done")
        return {
            "total": total,
            "todo": sum(1 for t in tasks if t.status == "todo"),
            "in_progress": sum(1 for t in tasks if t.status == "in_progress"),
            "done": done,
            "completion_rate": round((done / total) * 100, 1) if total > 0 else 0,
        }


class TaskManager:
    """Task CRUD operations."""

    def __init__(self, save_dir: Path):
        self.save_dir = save_dir
        self.save_dir.mkdir(parents=True, exist_ok=True)
        self.tasks_file = save_dir / "tasks.json"
        self.tasks: List[Task] = []
        self._load()

    def _load(self):
        if not self.tasks_file.exists():
            self.tasks = []
            return
        try:
            with open(self.tasks_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.tasks = [Task.from_dict(item) for item in data]
        except (json.JSONDecodeError, KeyError):
            self.tasks = []

    def _save(self):
        with open(self.tasks_file, "w", encoding="utf-8") as f:
            json.dump([t.to_dict() for t in self.tasks], f, indent=2, ensure_ascii=False)

    def create(
        self,
        content: str,
        sprint_id: Optional[int] = None,
        season_id: Optional[int] = None,
        priority: str = "medium",
        memo: str = "",
        due_date: Optional[str] = None,
    ) -> Task:
        new_id = max([t.id for t in self.tasks], default=0) + 1
        task = Task(
            id=new_id,
            content=content,
            sprint_id=sprint_id,
            season_id=season_id,
            status="todo",
            priority=priority,
            memo=memo,
            due_date=due_date,
            created_at=datetime.now().strftime("%Y-%m-%d"),
            order=new_id,
        )
        self.tasks.append(task)
        self._save()
        return task

    def get(self, task_id: int) -> Optional[Task]:
        return next((t for t in self.tasks if t.id == task_id), None)

    def get_by_sprint(self, sprint_id: int) -> List[Task]:
        return sorted(
            [t for t in self.tasks if t.sprint_id == sprint_id],
            key=lambda t: t.order,
        )

    def get_by_season(self, season_id: int) -> List[Task]:
        return [t for t in self.tasks if t.season_id == season_id]

    def get_unassigned(self) -> List[Task]:
        return [t for t in self.tasks if t.sprint_id is None]

    def toggle_status(self, task_id: int) -> Optional[Task]:
        status_cycle = ["todo", "in_progress", "done"]
        task = self.get(task_id)
        if not task:
            return None
        idx = status_cycle.index(task.status) if task.status in status_cycle else 0
        new_status = status_cycle[(idx + 1) % 3]
        task.status = new_status
        if new_status == "done":
            task.completed_at = datetime.now().strftime("%Y-%m-%d")
        elif task.completed_at and new_status != "done":
            task.completed_at = None
        self._save()
        return task

    def toggle_check(self, task_id: int) -> Optional[Task]:
        """Toggle between todo and done."""
        task = self.get(task_id)
        if not task:
            return None
        if task.status == "done":
            task.status = "todo"
            task.completed_at = None
        else:
            task.status = "done"
            task.completed_at = datetime.now().strftime("%Y-%m-%d")
        self._save()
        return task

    def update_memo(self, task_id: int, memo: str) -> Optional[Task]:
        task = self.get(task_id)
        if task:
            task.memo = memo
            self._save()
        return task

    def update(self, task_id: int, **kwargs) -> Optional[Task]:
        task = self.get(task_id)
        if not task:
            return None
        for key, value in kwargs.items():
            if hasattr(task, key):
                setattr(task, key, value)
        self._save()
        return task

    def delete(self, task_id: int) -> bool:
        self.tasks = [t for t in self.tasks if t.id != task_id]
        self._save()
        return True

    def reorder(self, task_id: int, new_order: int) -> Optional[Task]:
        task = self.get(task_id)
        if task:
            task.order = new_order
            self._save()
        return task

    def get_stats(self, season_id: Optional[int] = None, sprint_id: Optional[int] = None) -> dict:
        if sprint_id:
            tasks = self.get_by_sprint(sprint_id)
        elif season_id:
            tasks = self.get_by_season(season_id)
        else:
            tasks = self.tasks
        total = len(tasks)
        done = sum(1 for t in tasks if t.status == "done")
        return {
            "total": total,
            "todo": sum(1 for t in tasks if t.status == "todo"),
            "in_progress": sum(1 for t in tasks if t.status == "in_progress"),
            "done": done,
            "completion_rate": round((done / total) * 100, 1) if total > 0 else 0,
        }

    def get_today_tasks(self) -> List[Task]:
        today = datetime.now().strftime("%Y-%m-%d")
        return [
            t for t in self.tasks
            if t.created_at == today or (t.completed_at and t.completed_at == today)
        ]
