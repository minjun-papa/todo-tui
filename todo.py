#!/usr/bin/env python3
"""
Terminal Todo App - TUI 기반 할 일 관리 애플리케이션
Epic > Story > Task 계층 구조 지원
Jira 동기화 지원
"""

import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict

try:
    from textual.app import App, ComposeResult
    from textual.containers import Container, Horizontal, Vertical
    from textual.widgets import (
        Header, Footer, Static, Button, Input, Label,
        Tree, Select
    )
    from textual.screen import Screen
    from textual.binding import Binding
    from textual.reactive import reactive
    from textual.message import Message
except ImportError:
    print("textual 라이브러리가 필요합니다.")
    print("설치: pip install textual")
    exit(1)

# Jira 클라이언트 임포트
try:
    from jira_client import JiraClient, JiraConfig
    JIRA_AVAILABLE = True
except ImportError:
    JIRA_AVAILABLE = False
    JiraClient = None
    JiraConfig = None


@dataclass
class Season:
    """시즌 데이터 클래스"""
    id: int
    name: str
    start_date: str
    end_date: str
    status: str = "active"  # active, expired, archived
    created_at: str = ""

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "status": self.status,
            "created_at": self.created_at
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)

    def is_expired(self) -> bool:
        """시즌 만료 여부 확인"""
        today = datetime.now().strftime("%Y-%m-%d")
        return self.end_date < today

    def get_progress(self) -> float:
        """시즌 진행률 (0-100)"""
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
class TodoItem:
    """Todo 항목 데이터 클래스"""
    id: int
    content: str
    type: str = "task"  # epic, story, task
    category: str = "general"
    priority: str = "medium"
    due_date: Optional[str] = None
    status: str = "todo"  # todo, in_progress, done
    created_at: str = ""
    completed_at: Optional[str] = None  # 완료 날짜
    parent_id: Optional[int] = None
    season_id: Optional[int] = None
    jira_key: Optional[str] = None  # Jira 이슈 키 (예: PROJ-123)
    jira_id: Optional[str] = None   # Jira 이슈 ID
    description: Optional[str] = None  # 항목 설명
    order: int = 0  # 정렬 순서

    def to_dict(self):
        return {
            "id": self.id,
            "content": self.content,
            "type": self.type,
            "category": self.category,
            "priority": self.priority,
            "due_date": self.due_date,
            "status": self.status,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "parent_id": self.parent_id,
            "season_id": self.season_id,
            "jira_key": self.jira_key,
            "jira_id": self.jira_id,
            "description": self.description,
            "order": self.order
        }

    @classmethod
    def from_dict(cls, data: dict):
        # 기존 completed 필드를 status로 변환 (호환성)
        if "completed" in data and "status" not in data:
            data["status"] = "done" if data["completed"] else "todo"
            del data["completed"]
        return cls(**data)


class SeasonManager:
    """시즌 관리 클래스"""

    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.seasons_dir = self._get_seasons_dir()
        self.seasons_file = self.seasons_dir / "seasons.json"
        self.seasons: List[Season] = []
        self.current_season_id: Optional[int] = None
        self._load_seasons()

    def _get_seasons_dir(self) -> Path:
        """시즌 데이터 폴더 경로"""
        if self.config_path.exists():
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                save_path = config.get("save_path", "~/todos")
                seasons_dir = Path(save_path).expanduser() / "seasons"
        else:
            seasons_dir = Path.home() / "todos" / "seasons"
        seasons_dir.mkdir(parents=True, exist_ok=True)
        return seasons_dir

    def _load_seasons(self):
        """시즌 데이터 로드"""
        if not self.seasons_file.exists():
            self.seasons = []
            return

        try:
            with open(self.seasons_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.seasons = [Season.from_dict(item) for item in data]
            # 현재 시즌 설정 (가장 최근 활성 시즌)
            active_seasons = [s for s in self.seasons if s.status == "active"]
            if active_seasons:
                self.current_season_id = active_seasons[-1].id
        except (json.JSONDecodeError, KeyError):
            self.seasons = []

    def _save_seasons(self):
        """시즌 데이터 저장"""
        with open(self.seasons_file, "w", encoding="utf-8") as f:
            json.dump([s.to_dict() for s in self.seasons], f, indent=2, ensure_ascii=False)

    def create_season(self, name: str, start_date: str, end_date: str) -> Season:
        """새 시즌 생성"""
        new_id = max([s.id for s in self.seasons], default=0) + 1
        season = Season(
            id=new_id,
            name=name,
            start_date=start_date,
            end_date=end_date,
            status="active",
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        self.seasons.append(season)
        self._save_seasons()
        return season

    def get_active_seasons(self) -> List[Season]:
        """활성 시즌 목록"""
        return [s for s in self.seasons if s.status == "active"]

    def get_expired_seasons(self) -> List[Season]:
        """만료된 시즌 목록"""
        return [s for s in self.seasons if s.status == "expired"]

    def get_archived_seasons(self) -> List[Season]:
        """아카이브된 시즌 목록"""
        return [s for s in self.seasons if s.status == "archived"]

    def get_all_seasons(self) -> List[Season]:
        """모든 시즌 목록"""
        return self.seasons

    def get_season(self, season_id: int) -> Optional[Season]:
        """시즌 조회"""
        for season in self.seasons:
            if season.id == season_id:
                return season
        return None

    def set_current_season(self, season_id: int):
        """현재 시즌 설정"""
        if any(s.id == season_id for s in self.seasons):
            self.current_season_id = season_id

    def get_current_season(self) -> Optional[Season]:
        """현재 시즌 반환"""
        if self.current_season_id:
            return self.get_season(self.current_season_id)
        return None

    def archive_season(self, season_id: int):
        """시즌 아카이브"""
        season = self.get_season(season_id)
        if season:
            season.status = "archived"
            self._save_seasons()

    def check_expired_seasons(self):
        """만료된 시즌 체크 및 상태 업데이트"""
        for season in self.seasons:
            if season.status == "active" and season.is_expired():
                season.status = "expired"
        self._save_seasons()

    def get_season_file_path(self, season_id: int) -> Path:
        """시즌별 todo 파일 경로"""
        return self.seasons_dir / f"season_{season_id}.json"

    def get_season_stats(self, todos: List[TodoItem]) -> dict:
        """시즌 통계 계산"""
        total = len(todos)
        todo_count = sum(1 for t in todos if t.status == "todo")
        in_progress = sum(1 for t in todos if t.status == "in_progress")
        done = sum(1 for t in todos if t.status == "done")
        completion_rate = round((done / total) * 100, 1) if total > 0 else 0

        return {
            "total": total,
            "todo": todo_count,
            "in_progress": in_progress,
            "done": done,
            "completion_rate": completion_rate,
            "epics": sum(1 for t in todos if t.type == "epic"),
            "stories": sum(1 for t in todos if t.type == "story"),
            "tasks": sum(1 for t in todos if t.type == "task")
        }


class TodoManager:
    """Todo 관리 클래스"""

    TYPE_ORDER = {"epic": 0, "story": 1, "task": 2}

    def __init__(self):
        self.config_path = Path(__file__).parent / "config.json"
        self.todos: List[TodoItem] = []
        self.todo_file: Path = self._get_todo_file_path()
        self.season_manager: Optional[SeasonManager] = None
        self.jira_client: Optional[JiraClient] = None
        self.storage_type: str = "local"
        self._load_config()
        self._load_todos()

    def _load_config(self):
        """설정 로드"""
        if self.config_path.exists():
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                self.storage_type = config.get("storage_type", "local")

    def _get_todo_file_path(self) -> Path:
        """설정 파일에서 저장 위치를 가져옵니다."""
        if self.config_path.exists():
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                save_path = config.get("save_path", "~/todos")
                return Path(save_path).expanduser() / "todos.json"
        else:
            default_path = Path.home() / "todos"
            default_path.mkdir(parents=True, exist_ok=True)
            self._save_config(str(default_path))
            return default_path / "todos.json"

    def _save_config(self, save_path: str, storage_type: str = "local", jira_config: dict = None):
        """설정을 저장합니다."""
        config = {
            "save_path": save_path,
            "storage_type": storage_type,
            "jira": jira_config or {
                "enabled": False,
                "base_url": "",
                "email": "",
                "api_token": "",
                "project_key": ""
            }
        }
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        self.storage_type = storage_type

    def set_jira_client(self, jira_client: Optional[JiraClient]):
        """Jira 클라이언트 설정"""
        self.jira_client = jira_client

    def is_jira_enabled(self) -> bool:
        """Jira 동기화 활성화 여부"""
        return self.jira_client is not None and self.storage_type == "jira"

    def sync_from_jira(self) -> List[TodoItem]:
        """Jira에서 Todo 동기화"""
        if not self.is_jira_enabled():
            return []

        try:
            jira_issues = self.jira_client.get_issues()
            synced_todos = []

            for issue in jira_issues:
                # 기존 Todo에서 Jira 키로 찾기
                existing = next(
                    (t for t in self.todos if t.jira_key == issue["key"]),
                    None
                )

                if existing:
                    # 기존 Todo 업데이트
                    todo_data = self.jira_client.convert_jira_to_todo(issue)
                    existing.content = todo_data["content"]
                    existing.status = todo_data["status"]
                    existing.priority = todo_data["priority"]
                    if todo_data.get("due_date"):
                        existing.due_date = todo_data["due_date"]
                    synced_todos.append(existing)
                else:
                    # 새 Todo 생성
                    todo_data = self.jira_client.convert_jira_to_todo(issue)
                    new_id = max([t.id for t in self.todos], default=0) + 1
                    new_todo = TodoItem(
                        id=new_id,
                        content=todo_data["content"],
                        type=todo_data["type"],
                        status=todo_data["status"],
                        priority=todo_data["priority"],
                        due_date=todo_data.get("due_date"),
                        jira_key=todo_data.get("jira_key"),
                        jira_id=todo_data.get("jira_id"),
                        created_at=todo_data.get("created_at", datetime.now().strftime("%Y-%m-%d"))
                    )
                    self.todos.append(new_todo)
                    synced_todos.append(new_todo)

            self._save_todos()
            return synced_todos

        except Exception as e:
            print(f"Jira 동기화 실패: {e}")
            return []

    def sync_to_jira(self, todo: TodoItem) -> Optional[dict]:
        """Todo를 Jira로 동기화 (이슈 생성/업데이트)"""
        if not self.is_jira_enabled():
            return None

        try:
            # 부모의 Jira 키 찾기
            parent_key = None
            if todo.parent_id:
                parent = next((t for t in self.todos if t.id == todo.parent_id), None)
                if parent and parent.jira_key:
                    parent_key = parent.jira_key

            if todo.jira_key:
                # 기존 이슈 업데이트
                self.jira_client.update_issue(todo.jira_key, {
                    "content": todo.content,
                    "priority": todo.priority,
                    "due_date": todo.due_date
                })
                return {"key": todo.jira_key, "id": todo.jira_id}
            else:
                # 새 이슈 생성
                result = self.jira_client.create_issue({
                    "content": todo.content,
                    "type": todo.type,
                    "priority": todo.priority,
                    "due_date": todo.due_date,
                    "parent_key": parent_key
                })
                todo.jira_key = result["key"]
                todo.jira_id = result["id"]
                self._save_todos()
                return result

        except Exception as e:
            print(f"Jira 이슈 생성/업데이트 실패: {e}")
            return None

    def _load_todos(self):
        """JSON 파일에서 todos를 로드합니다."""
        if not self.todo_file.exists():
            self.todos = []
            return

        try:
            with open(self.todo_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.todos = [TodoItem.from_dict(item) for item in data]
        except (json.JSONDecodeError, KeyError):
            self.todos = []

    def _save_todos(self):
        """todos를 JSON 파일로 저장합니다."""
        self.todo_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.todo_file, "w", encoding="utf-8") as f:
            json.dump([t.to_dict() for t in self.todos], f, indent=2, ensure_ascii=False)

    def set_season_manager(self, season_manager: SeasonManager):
        """시즌 매니저 설정"""
        self.season_manager = season_manager

    def get_todos_by_season(self, season_id: Optional[int]) -> List[TodoItem]:
        """시즌별 Todo 필터링"""
        if season_id is None:
            return [t for t in self.todos if t.season_id is None]
        return [t for t in self.todos if t.season_id == season_id]

    def get_todos_by_date_range(self, start_date: str, end_date: str) -> List[TodoItem]:
        """날짜 범위로 Todo 필터링"""
        return [
            t for t in self.todos
            if t.created_at and start_date <= t.created_at <= end_date
        ]

    def get_today_todos(self) -> List[TodoItem]:
        """오늘 생성된/수정된 Todo"""
        today = datetime.now().strftime("%Y-%m-%d")
        return [t for t in self.todos if t.created_at and t.created_at.startswith(today)]

    def get_weekly_todos(self) -> List[TodoItem]:
        """이번 주 Todo"""
        from datetime import timedelta
        today = datetime.now()
        start_of_week = (today - timedelta(days=today.weekday())).strftime("%Y-%m-%d")
        end_of_week = (today + timedelta(days=6 - today.weekday())).strftime("%Y-%m-%d")
        return self.get_todos_by_date_range(start_of_week, end_of_week)

    def get_report_data(self, report_type: str, season_id: Optional[int] = None) -> dict:
        """리포트 데이터 생성"""
        today_str = datetime.now().strftime("%Y-%m-%d")

        if report_type == "today":
            # 오늘 생성된 작업
            created_today = [t for t in self.todos if t.created_at and t.created_at == today_str]
            # 오늘 완료된 작업
            completed_today = [t for t in self.todos if t.completed_at and t.completed_at == today_str]
            # 중복 제거 (ID 기준)
            seen_ids = set()
            todos = []
            for t in created_today + completed_today:
                if t.id not in seen_ids:
                    seen_ids.add(t.id)
                    todos.append(t)
            period = today_str
        elif report_type == "weekly":
            todos = self.get_weekly_todos()
            from datetime import timedelta
            today = datetime.now()
            start = (today - timedelta(days=today.weekday())).strftime("%Y-%m-%d")
            end = (today + timedelta(days=6 - today.weekday())).strftime("%Y-%m-%d")
            period = f"{start} ~ {end}"
            created_today = None
            completed_today = None
        elif report_type == "season" and season_id:
            todos = self.get_todos_by_season(season_id)
            if self.season_manager:
                season = self.season_manager.get_season(season_id)
                if season:
                    period = f"{season.name} ({season.start_date} ~ {season.end_date})"
                else:
                    period = f"Season {season_id}"
            else:
                period = f"Season {season_id}"
            created_today = None
            completed_today = None
        else:
            todos = self.todos
            period = "전체"
            created_today = None
            completed_today = None

        stats = {
            "total": len(todos),
            "todo": sum(1 for t in todos if t.status == "todo"),
            "in_progress": sum(1 for t in todos if t.status == "in_progress"),
            "done": sum(1 for t in todos if t.status == "done"),
            "epics": sum(1 for t in todos if t.type == "epic"),
            "stories": sum(1 for t in todos if t.type == "story"),
            "tasks": sum(1 for t in todos if t.type == "task"),
            "completion_rate": round((sum(1 for t in todos if t.status == "done") / len(todos)) * 100, 1) if todos else 0,
            "high_priority": sum(1 for t in todos if t.priority == "high"),
            "overdue": sum(1 for t in todos if t.due_date and t.due_date < datetime.now().strftime("%Y-%m-%d") and t.status != "done")
        }

        return {
            "period": period,
            "stats": stats,
            "todos": todos,
            "created_today": created_today,
            "completed_today": completed_today
        }

    def add_todo(self, content: str, type: str = "task", category: str = "general",
                 priority: str = "medium", due_date: Optional[str] = None,
                 parent_id: Optional[int] = None, season_id: Optional[int] = None,
                 description: Optional[str] = None) -> TodoItem:
        """새 할 일을 추가합니다."""
        new_id = max([t.id for t in self.todos], default=0) + 1

        # season_id가 지정되지 않았으면 현재 시즌 사용
        if season_id is None and self.season_manager:
            season_id = self.season_manager.current_season_id

        # 같은 부모를 가진 항목 중 최대 order 찾기
        siblings = [t for t in self.todos if t.parent_id == parent_id]
        max_order = max([t.order for t in siblings], default=-1) + 1 if siblings else 0

        todo = TodoItem(
            id=new_id,
            content=content,
            type=type,
            category=category,
            priority=priority,
            due_date=due_date,
            status="todo",
            created_at=datetime.now().strftime("%Y-%m-%d"),
            parent_id=parent_id,
            season_id=season_id,
            description=description,
            order=max_order
        )

        self.todos.append(todo)

        # Jira 동기화
        if self.is_jira_enabled():
            try:
                result = self.sync_to_jira(todo)
                if result:
                    todo.jira_key = result.get("key")
                    todo.jira_id = result.get("id")
            except Exception as e:
                print(f"Jira 이슈 생성 실패: {e}")

        self._save_todos()
        return todo

    def change_status(self, todo_id: int) -> Optional[TodoItem]:
        """할 일 상태를 순환합니다: todo -> in_progress -> done -> todo"""
        status_order = ["todo", "in_progress", "done"]
        for todo in self.todos:
            if todo.id == todo_id:
                current_idx = status_order.index(todo.status)
                new_status = status_order[(current_idx + 1) % 3]
                todo.status = new_status

                # 완료 날짜 관리
                if new_status == "done":
                    todo.completed_at = datetime.now().strftime("%Y-%m-%d")
                elif new_status == "todo" and todo.status == "done":
                    todo.completed_at = None

                # Jira 상태 동기화
                if self.is_jira_enabled() and todo.jira_key:
                    try:
                        self.jira_client.transition_issue(todo.jira_key, new_status)
                    except Exception as e:
                        print(f"Jira 상태 변경 실패: {e}")

                self._save_todos()
                return todo
        return None

    def toggle_todo(self, todo_id: int) -> Optional[TodoItem]:
        """할 일 완료 상태를 토글합니다 (호환성 유지)."""
        return self.change_status(todo_id)

    def toggle_check(self, todo_id: int) -> Optional[TodoItem]:
        """체크 토글: todo <-> done (in_progress는 done으로)"""
        for todo in self.todos:
            if todo.id == todo_id:
                if todo.status == "done":
                    todo.status = "todo"
                    todo.completed_at = None  # 완료 취소 시 완료 날짜 제거
                else:
                    todo.status = "done"
                    todo.completed_at = datetime.now().strftime("%Y-%m-%d")  # 완료 날짜 기록

                # Jira 상태 동기화
                if self.is_jira_enabled() and todo.jira_key:
                    try:
                        self.jira_client.transition_issue(todo.jira_key, todo.status)
                    except Exception as e:
                        print(f"Jira 상태 변경 실패: {e}")

                self._save_todos()
                return todo
        return None

    def delete_todo(self, todo_id: int) -> Optional[TodoItem]:
        """할 일과 모든 하위 항목을 삭제합니다."""
        # 하위 항목들 찾기 (재귀적으로)
        ids_to_delete = [todo_id]
        changed = True
        while changed:
            changed = False
            for todo in self.todos:
                if todo.parent_id in ids_to_delete and todo.id not in ids_to_delete:
                    ids_to_delete.append(todo.id)
                    changed = True

        # 삭제 실행
        deleted = None
        self.todos = [t for t in self.todos if t.id not in ids_to_delete]
        self._save_todos()
        return deleted

    def get_children(self, parent_id: Optional[int] = None) -> List[TodoItem]:
        """특정 부모의 직접 하위 항목들을 반환합니다."""
        return [t for t in self.todos if t.parent_id == parent_id]

    def get_root_items(self) -> List[TodoItem]:
        """최상위 항목들 반환 (부모가 없는 항목)"""
        return [t for t in self.todos if t.parent_id is None]

    def get_possible_parents(self, current_type: str) -> List[TodoItem]:
        """현재 타입에서 선택 가능한 부모 목록 반환"""
        if current_type == "epic":
            return []  # Epic은 부모를 가질 수 없음
        elif current_type == "story":
            return [t for t in self.todos if t.type == "epic"]
        else:  # task
            return [t for t in self.todos if t.type in ("epic", "story")]

    def get_stats(self) -> dict:
        """통계 반환"""
        total = len(self.todos)
        todo_count = sum(1 for t in self.todos if t.status == "todo")
        in_progress = sum(1 for t in self.todos if t.status == "in_progress")
        done = sum(1 for t in self.todos if t.status == "done")
        epics = sum(1 for t in self.todos if t.type == "epic")
        stories = sum(1 for t in self.todos if t.type == "story")
        tasks = sum(1 for t in self.todos if t.type == "task")
        return {
            "total": total,
            "todo": todo_count,
            "in_progress": in_progress,
            "done": done,
            "epics": epics,
            "stories": stories,
            "tasks": tasks
        }

    def get_in_progress_items(self) -> List[TodoItem]:
        """진행중인 항목 반환 (Epic 제외)"""
        return [t for t in self.todos if t.status == "in_progress" and t.type != "epic"]

    def get_todo_by_id(self, todo_id: int) -> Optional[TodoItem]:
        """ID로 Todo 항목 찾기"""
        for todo in self.todos:
            if todo.id == todo_id:
                return todo
        return None

    def move_item_up(self, todo_id: int) -> bool:
        """항목을 위로 이동 (같은 부모 내에서)"""
        todo = self.get_todo_by_id(todo_id)
        if not todo:
            return False

        # 같은 부모를 가진 형제 항목들 찾기
        siblings = sorted(
            [t for t in self.todos if t.parent_id == todo.parent_id],
            key=lambda t: t.order
        )

        if len(siblings) <= 1:
            return False

        # 현재 항목의 인덱스 찾기
        current_idx = next((i for i, s in enumerate(siblings) if s.id == todo_id), -1)
        if current_idx <= 0:
            return False  # 이미 첫 번째

        # 순서 교환
        prev_sibling = siblings[current_idx - 1]
        todo.order, prev_sibling.order = prev_sibling.order, todo.order
        self._save_todos()
        return True

    def move_item_down(self, todo_id: int) -> bool:
        """항목을 아래로 이동 (같은 부모 내에서)"""
        todo = self.get_todo_by_id(todo_id)
        if not todo:
            return False

        # 같은 부모를 가진 형제 항목들 찾기
        siblings = sorted(
            [t for t in self.todos if t.parent_id == todo.parent_id],
            key=lambda t: t.order
        )

        if len(siblings) <= 1:
            return False

        # 현재 항목의 인덱스 찾기
        current_idx = next((i for i, s in enumerate(siblings) if s.id == todo_id), -1)
        if current_idx < 0 or current_idx >= len(siblings) - 1:
            return False  # 이미 마지막

        # 순서 교환
        next_sibling = siblings[current_idx + 1]
        todo.order, next_sibling.order = next_sibling.order, todo.order
        self._save_todos()
        return True

    def update_description(self, todo_id: int, description: Optional[str]) -> bool:
        """항목 설명 업데이트"""
        todo = self.get_todo_by_id(todo_id)
        if todo:
            todo.description = description
            self._save_todos()
            return True
        return False


class DescriptionPopup(Screen):
    """설명 팝업 화면"""

    CSS = """
    DescriptionPopup {
        align: center middle;
    }

    .popup-container {
        width: 60;
        max-height: 20;
        border: solid yellow;
        padding: 1 2;
        background: $surface;
    }

    .popup-title {
        text-align: center;
        text-style: bold;
        color: yellow;
        margin-bottom: 1;
    }

    .popup-content {
        margin-bottom: 1;
    }

    .button-row {
        height: auto;
        align: center middle;
        margin-top: 1;
    }

    Button {
        margin: 0 1;
    }
    """

    BINDINGS = [
        Binding("escape", "close", "닫기"),
        Binding("e", "edit", "수정"),
    ]

    def __init__(self, todo_id: int, content: str, description: Optional[str] = None):
        super().__init__()
        self.todo_id = todo_id
        self.todo_content = content
        self.todo_description = description

    def compose(self) -> ComposeResult:
        with Container(classes="popup-container"):
            yield Static("📝 항목 상세 정보", classes="popup-title")
            yield Static(f"제목: {self.todo_content}", classes="popup-content")
            yield Static(f"설명: {self.todo_description or '(설명 없음)'}", classes="popup-content", id="desc_text")
            with Horizontal(classes="button-row"):
                yield Button("수정", variant="primary", id="edit")
                yield Button("닫기", variant="default", id="close")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "close":
            self.app.pop_screen()
        elif event.button.id == "edit":
            self.app.push_screen(EditDescriptionScreen(self.todo_id, self.todo_description))

    def action_close(self):
        self.app.pop_screen()

    def action_edit(self):
        self.app.push_screen(EditDescriptionScreen(self.todo_id, self.todo_description))

    def on_screen_resume(self):
        """EditDescriptionScreen에서 돌아올 때 설명 새로고침"""
        todo = self.app.manager.get_todo_by_id(self.todo_id)
        if todo:
            self.todo_description = todo.description
            desc_text = self.query_one("#desc_text", Static)
            desc_text.update(f"설명: {self.todo_description or '(설명 없음)'}")


class EditDescriptionScreen(Screen):
    """설명 수정 화면"""

    CSS = """
    EditDescriptionScreen {
        align: center middle;
    }

    .edit-container {
        width: 60;
        height: auto;
        border: solid green;
        padding: 1 2;
        background: $surface;
    }

    .title {
        text-align: center;
        text-style: bold;
        color: green;
        margin-bottom: 1;
    }

    TextArea {
        width: 100%;
        height: 8;
        margin-bottom: 1;
    }

    .button-row {
        height: auto;
        align: center middle;
        margin-top: 1;
    }

    Button {
        margin: 0 1;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "취소"),
        Binding("ctrl+s", "save", "저장"),
    ]

    def __init__(self, todo_id: int, current_description: Optional[str] = None):
        super().__init__()
        self.todo_id = todo_id
        self.current_description = current_description or ""

    def compose(self) -> ComposeResult:
        from textual.widgets import TextArea
        with Container(classes="edit-container"):
            yield Static("📝 설명 수정", classes="title")
            yield TextArea(self.current_description, id="description")
            with Horizontal(classes="button-row"):
                yield Button("저장", variant="success", id="save")
                yield Button("취소", variant="error", id="cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":
            self.action_save()
        elif event.button.id == "cancel":
            self.app.pop_screen()

    def action_save(self):
        from textual.widgets import TextArea
        description = self.query_one("#description", TextArea).text.strip()
        if description == "":
            description = None
        self.app.manager.update_description(self.todo_id, description)
        self.app.pop_screen()

    def action_cancel(self):
        self.app.pop_screen()


class AddTodoScreen(Screen):
    """할 일 추가 화면"""

    CSS = """
    AddTodoScreen {
        align: center middle;
    }

    .add-container {
        width: 60;
        height: auto;
        border: solid green;
        padding: 1 2;
        background: $surface;
    }

    Input, Select {
        width: 100%;
        margin-bottom: 1;
    }

    .button-row {
        height: auto;
        align: center middle;
        margin-top: 1;
    }

    Button {
        margin: 0 2;
    }

    Label {
        text-style: bold;
        margin-bottom: 1;
    }

    .title {
        text-align: center;
        text-style: bold;
        color: green;
        margin-bottom: 1;
    }

    .options-toggle {
        color: yellow;
        margin-top: 1;
        margin-bottom: 1;
    }

    .options-panel {
        margin-top: 1;
        padding-top: 1;
        border-top: solid $primary;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "취소"),
        Binding("enter", "submit", "추가"),
    ]

    show_options = reactive(False)

    def __init__(self, parent_id: Optional[int] = None, parent_type: Optional[str] = None):
        super().__init__()
        self.default_parent_id = parent_id
        self.default_type = self._get_default_type(parent_type)

    def _get_default_type(self, parent_type: Optional[str]) -> str:
        """부모 타입에 따른 기본 타입 결정"""
        if parent_type is None:
            return "epic"
        elif parent_type == "epic":
            return "story"
        elif parent_type == "story":
            return "task"
        return "task"

    def compose(self) -> ComposeResult:
        with Container(classes="add-container"):
            yield Static("새 항목 추가", classes="title")

            yield Label("유형")
            yield Select(
                [
                    ("📁 Epic (최상위)", "epic"),
                    ("📖 Story (Epic 하위)", "story"),
                    ("✅ Task (Story/Epic 하위)", "task"),
                ],
                id="type",
                prompt="유형 선택"
            )

            yield Label("내용 *")
            yield Input(placeholder="항목 내용을 입력하세요", id="content")

            yield Label("설명")
            yield Input(placeholder="항목 설명 (선택사항)", id="description")

            # 추가 옵션 토글 버튼
            yield Button("▶ 추가 옵션 (우선순위, 마감일)", id="toggle_options", classes="options-toggle")

            # 추가 옵션 패널
            with Container(classes="options-panel", id="options_panel"):
                yield Label("우선순위")
                yield Select(
                    [
                        ("🔴 높음 (High)", "high"),
                        ("🟡 보통 (Medium)", "medium"),
                        ("🟢 낮음 (Low)", "low"),
                    ],
                    id="priority",
                    prompt="우선순위 선택 (기본: 보통)"
                )

                yield Label("마감일")
                yield Input(placeholder="마감일 (YYYY-MM-DD)", id="due_date")

            with Horizontal(classes="button-row"):
                yield Button("추가", variant="success", id="add")
                yield Button("취소", variant="error", id="cancel")

    def on_mount(self):
        # 유형 기본값 설정
        type_select = self.query_one("#type", Select)
        type_select.value = self.default_type

        # 추가 옵션 패널 숨기기
        options_panel = self.query_one("#options_panel", Container)
        options_panel.display = False

        # 우선순위 기본값
        priority_select = self.query_one("#priority", Select)
        priority_select.value = "medium"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "add":
            self.action_submit()
        elif event.button.id == "cancel":
            self.app.pop_screen()
        elif event.button.id == "toggle_options":
            self.action_toggle_options()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Input에서 Enter 키 눌렀을 때"""
        if event.input.id == "content":
            self.action_submit()

    def action_toggle_options(self):
        """추가 옵션 패널 토글"""
        self.show_options = not self.show_options
        options_panel = self.query_one("#options_panel", Container)
        toggle_btn = self.query_one("#toggle_options", Button)

        if self.show_options:
            options_panel.display = True
            toggle_btn.label = "▼ 추가 옵션 (우선순위, 마감일)"
        else:
            options_panel.display = False
            toggle_btn.label = "▶ 추가 옵션 (우선순위, 마감일)"

    def action_submit(self):
        content = self.query_one("#content", Input).value.strip()
        if not content:
            return

        type_value = self.query_one("#type", Select).value or "task"
        priority = self.query_one("#priority", Select).value or "medium"
        due_date = self.query_one("#due_date", Input).value.strip() or None
        description = self.query_one("#description", Input).value.strip() or None

        # 빈 문자열이면 None으로 변환
        if due_date == "":
            due_date = None
        if description == "":
            description = None

        # 부모 ID 설정 (생성자에서 받은 값 사용)
        parent_id = self.default_parent_id

        self.app.manager.add_todo(
            content=content,
            type=type_value,
            category="general",  # 카테고리는 기본값 사용
            priority=priority,
            due_date=due_date,
            parent_id=parent_id,
            description=description
        )
        self.app.pop_screen()

    def action_cancel(self):
        self.app.pop_screen()


class AddSeasonScreen(Screen):
    """시즌 생성 화면"""

    CSS = """
    AddSeasonScreen {
        align: center middle;
    }

    .season-container {
        width: 50;
        height: auto;
        border: solid blue;
        padding: 1 2;
        background: $surface;
    }

    Input {
        width: 100%;
        margin-bottom: 1;
    }

    .button-row {
        height: auto;
        align: center middle;
        margin-top: 1;
    }

    Button {
        margin: 0 2;
    }

    Label {
        text-style: bold;
        margin-bottom: 1;
    }

    .title {
        text-align: center;
        text-style: bold;
        color: blue;
        margin-bottom: 1;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "취소"),
    ]

    def compose(self) -> ComposeResult:
        with Container(classes="season-container"):
            yield Static("🗓️ 새 시즌 생성", classes="title")
            yield Label("시즌 이름")
            yield Input(placeholder="예: 2024 Q1, 프로젝트 A", id="season_name")
            yield Label("시작일 (YYYY-MM-DD)")
            yield Input(placeholder=datetime.now().strftime("%Y-%m-%d"), id="start_date")
            yield Label("종료일 (YYYY-MM-DD)")
            yield Input(placeholder="2024-03-31", id="end_date")
            with Horizontal(classes="button-row"):
                yield Button("생성", variant="primary", id="create")
                yield Button("취소", variant="error", id="cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "create":
            self.action_create()
        elif event.button.id == "cancel":
            self.app.pop_screen()

    def action_create(self):
        name = self.query_one("#season_name", Input).value.strip()
        start_date = self.query_one("#start_date", Input).value.strip()
        end_date = self.query_one("#end_date", Input).value.strip()

        if not name or not start_date or not end_date:
            return

        # 날짜 형식 검증
        try:
            datetime.strptime(start_date, "%Y-%m-%d")
            datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            return

        if self.app.season_manager:
            season = self.app.season_manager.create_season(name, start_date, end_date)
            self.app.season_manager.set_current_season(season.id)
        self.app.pop_screen()

    def action_cancel(self):
        self.app.pop_screen()


class SetupScreen(Screen):
    """초기 설정 선택 화면"""

    CSS = """
    SetupScreen {
        align: center middle;
    }

    .setup-container {
        width: 60;
        height: auto;
        border: solid green;
        padding: 1 2;
        background: $surface;
    }

    .title {
        text-align: center;
        text-style: bold;
        color: green;
        margin-bottom: 1;
    }

    .option {
        padding: 1;
        margin-bottom: 1;
        background: $panel;
    }

    .option:hover {
        background: $primary;
    }

    .option.selected {
        background: $primary;
        border: solid green;
    }

    .option-title {
        text-style: bold;
        margin-bottom: 1;
    }

    .option-desc {
        color: $text-muted;
    }

    Button {
        margin-top: 1;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "취소"),
        Binding("1", "select_local", "로컬"),
        Binding("2", "select_jira", "Jira"),
    ]

    selected_option = reactive("local")

    def compose(self) -> ComposeResult:
        with Container(classes="setup-container"):
            yield Static("초기 설정", classes="title")
            yield Static("데이터 저장 방식을 선택하세요:", classes="option-desc")

            with Vertical(id="options"):
                with Container(classes="option selected", id="option_local"):
                    yield Static("로컬 저장", classes="option-title")
                    yield Static("내 컴퓨터에 JSON 파일로 저장", classes="option-desc")

                with Container(classes="option", id="option_jira"):
                    yield Static("Jira 동기화", classes="option-title")
                    yield Static("Jira와 실시간 동기화 (API 토큰 필요)", classes="option-desc")

            yield Button("선택", variant="success", id="select")

    def on_mount(self):
        self._update_selection()

    def _update_selection(self):
        local_option = self.query_one("#option_local", Container)
        jira_option = self.query_one("#option_jira", Container)

        if self.selected_option == "local":
            local_option.set_class(True, "selected")
            jira_option.set_class(False, "selected")
        else:
            local_option.set_class(False, "selected")
            jira_option.set_class(True, "selected")

    def on_click(self, event):
        if event.target and hasattr(event.target, "id"):
            if "option_local" in str(event.target) or \
               (hasattr(event.target, "parent") and event.target.parent and
                hasattr(event.target.parent, "id") and event.target.parent.id == "option_local"):
                self.selected_option = "local"
                self._update_selection()
            elif "option_jira" in str(event.target) or \
                 (hasattr(event.target, "parent") and event.target.parent and
                  hasattr(event.target.parent, "id") and event.target.parent.id == "option_jira"):
                self.selected_option = "jira"
                self._update_selection()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "select":
            self.action_select()

    def action_select_local(self):
        self.selected_option = "local"
        self._update_selection()
        self.action_select()

    def action_select_jira(self):
        self.selected_option = "jira"
        self._update_selection()
        self.action_select()

    def action_select(self):
        if self.selected_option == "jira":
            self.app.push_screen(JiraSetupScreen())
        else:
            # 로컬 저장 설정
            self.app.manager._save_config(
                str(self.app.manager.todo_file.parent),
                "local"
            )
            self.app.pop_screen()

    def action_cancel(self):
        self.app.pop_screen()


class JiraSetupScreen(Screen):
    """Jira 설정 화면"""

    CSS = """
    JiraSetupScreen {
        align: center middle;
    }

    .jira-container {
        width: 60;
        height: auto;
        border: solid cyan;
        padding: 1 2;
        background: $surface;
    }

    .title {
        text-align: center;
        text-style: bold;
        color: cyan;
        margin-bottom: 1;
    }

    Input {
        width: 100%;
        margin-bottom: 1;
    }

    Label {
        text-style: bold;
        margin-bottom: 1;
    }

    .button-row {
        height: auto;
        align: center middle;
        margin-top: 1;
    }

    Button {
        margin: 0 1;
    }

    .status {
        text-align: center;
        margin-top: 1;
        padding: 1;
    }

    .status.success {
        color: green;
    }

    .status.error {
        color: red;
    }

    .help {
        color: $text-muted;
        text-align: center;
        margin-top: 1;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "취소"),
    ]

    def compose(self) -> ComposeResult:
        with Container(classes="jira-container"):
            yield Static("Jira 설정", classes="title")

            yield Label("Jira URL")
            yield Input(placeholder="https://your-company.atlassian.net", id="base_url")

            yield Label("이메일")
            yield Input(placeholder="your-email@example.com", id="email")

            yield Label("API 토큰")
            yield Input(placeholder="API 토큰", id="api_token", password=True)

            yield Label("프로젝트 키")
            yield Input(placeholder="PROJ", id="project_key")

            yield Static("", id="status", classes="status")
            yield Static("API 토큰: atlassian.com > 계정 설정 > 보안 > API 토큰", classes="help")

            with Horizontal(classes="button-row"):
                yield Button("연결 테스트", id="test", variant="primary")
                yield Button("저장", id="save", variant="success")
                yield Button("취소", id="cancel", variant="error")

    def on_mount(self):
        # 기존 설정 로드
        try:
            with open(self.app.manager.config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                jira_config = config.get("jira", {})
                self.query_one("#base_url", Input).value = jira_config.get("base_url", "")
                self.query_one("#email", Input).value = jira_config.get("email", "")
                self.query_one("#api_token", Input).value = jira_config.get("api_token", "")
                self.query_one("#project_key", Input).value = jira_config.get("project_key", "")
        except:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "test":
            self.action_test()
        elif event.button.id == "save":
            self.action_save()
        elif event.button.id == "cancel":
            self.app.pop_screen()

    def _get_config(self) -> dict:
        return {
            "enabled": True,
            "base_url": self.query_one("#base_url", Input).value.strip(),
            "email": self.query_one("#email", Input).value.strip(),
            "api_token": self.query_one("#api_token", Input).value,
            "project_key": self.query_one("#project_key", Input).value.strip().upper()
        }

    def action_test(self):
        if not JIRA_AVAILABLE:
            self._show_status("Jira 모듈이 설치되지 않음 (pip install requests)", "error")
            return

        config = self._get_config()
        status = self.query_one("#status", Static)

        if not all([config["base_url"], config["email"], config["api_token"], config["project_key"]]):
            self._show_status("모든 필드를 입력하세요", "error")
            return

        try:
            jira_config = JiraConfig.from_dict(config)
            client = JiraClient(jira_config)

            # 연결 테스트
            success, msg = client.test_connection()
            if not success:
                self._show_status(msg, "error")
                return

            # 프로젝트 테스트
            success, msg = client.test_project()
            if success:
                self._show_status(f"연결 성공! {msg}", "success")
            else:
                self._show_status(msg, "error")

        except Exception as e:
            self._show_status(f"오류: {str(e)}", "error")

    def action_save(self):
        config = self._get_config()

        if not all([config["base_url"], config["email"], config["api_token"], config["project_key"]]):
            self._show_status("모든 필드를 입력하세요", "error")
            return

        # 설정 저장
        self.app.manager._save_config(
            str(self.app.manager.todo_file.parent),
            "jira",
            config
        )

        # Jira 클라이언트 초기화
        if JIRA_AVAILABLE:
            try:
                jira_config = JiraConfig.from_dict(config)
                self.app.manager.set_jira_client(JiraClient(jira_config))
                self._show_status("Jira 설정 저장됨", "success")
            except Exception as e:
                self._show_status(f"클라이언트 초기화 실패: {e}", "error")
                return

        # 이전 화면들 닫기 (SetupScreen도)
        self.app.pop_screen()
        if len(self.app.screen_stack) > 1:
            self.app.pop_screen()

    def _show_status(self, message: str, status_type: str):
        status = self.query_one("#status", Static)
        status.update(message)
        status.set_class(status_type == "success", "success")
        status.set_class(status_type == "error", "error")

    def action_cancel(self):
        self.app.pop_screen()


class SeasonSelectScreen(Screen):
    """시즌 선택 화면"""

    CSS = """
    SeasonSelectScreen {
        align: center middle;
    }

    .select-container {
        width: 60;
        height: auto;
        max-height: 30;
        border: solid blue;
        padding: 1 2;
        background: $surface;
    }

    .title {
        text-align: center;
        text-style: bold;
        color: blue;
        margin-bottom: 1;
    }

    .section-title {
        text-style: bold;
        color: yellow;
        margin-top: 1;
        margin-bottom: 1;
    }

    .season-item {
        padding: 1;
        margin-bottom: 1;
        background: $panel;
    }

    .season-item:hover {
        background: $primary;
    }

    .season-item.active {
        background: $primary;
        border: solid green;
    }

    .no-season {
        color: $text-muted;
        text-align: center;
        margin-top: 1;
    }

    Button {
        width: 100%;
        margin-bottom: 1;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "취소"),
        Binding("r", "report", "리포트"),
    ]

    def compose(self) -> ComposeResult:
        with Container(classes="select-container"):
            yield Static("📅 시즌 선택", classes="title")

            yield Static("활성 시즌", classes="section-title")
            with Vertical(id="active-seasons"):
                pass

            yield Static("완료된 시즌", classes="section-title")
            with Vertical(id="archived-seasons"):
                pass

            yield Button("➕ 새 시즌 생성", id="new_season", variant="success")
            yield Button("📊 리포트 보기", id="report", variant="primary")
            yield Button("취소", id="cancel", variant="error")

    def on_mount(self):
        self._refresh_seasons()

    def _refresh_seasons(self):
        if not self.app.season_manager:
            return

        active_container = self.query_one("#active-seasons", Vertical)
        archived_container = self.query_one("#archived-seasons", Vertical)

        # Clear existing buttons
        active_container.remove_children()
        archived_container.remove_children()

        # Active seasons
        active_seasons = self.app.season_manager.get_active_seasons()
        if active_seasons:
            for season in active_seasons:
                progress = season.get_progress()
                is_current = season.id == self.app.season_manager.current_season_id
                btn_class = "active" if is_current else ""
                label = f"{'✓ ' if is_current else ''}{season.name} ({season.start_date} ~ {season.end_date}) [{progress}%]"
                btn = Button(label, id=f"season_{season.id}", classes=f"season-item {btn_class}")
                if is_current:
                    btn.variant = "success"
                active_container.mount(btn)
        else:
            active_container.mount(Static("활성 시즌이 없습니다", classes="no-season"))

        # Archived/Expired seasons
        archived_seasons = self.app.season_manager.get_archived_seasons() + self.app.season_manager.get_expired_seasons()
        if archived_seasons:
            for season in archived_seasons:
                label = f"{season.name} ({season.start_date} ~ {season.end_date}) [{season.status}]"
                btn = Button(label, id=f"season_{season.id}", classes="season-item")
                archived_container.mount(btn)
        else:
            archived_container.mount(Static("완료된 시즌이 없습니다", classes="no-season"))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "new_season":
            self.app.push_screen(AddSeasonScreen())
        elif event.button.id == "report":
            self.app.push_screen(ReportScreen())
        elif event.button.id == "cancel":
            self.app.pop_screen()
        elif event.button.id and event.button.id.startswith("season_"):
            season_id = int(event.button.id.split("_")[1])
            if self.app.season_manager:
                self.app.season_manager.set_current_season(season_id)
            self.app.pop_screen()

    def action_report(self):
        self.app.push_screen(ReportScreen())

    def action_cancel(self):
        self.app.pop_screen()


class ReportScreen(Screen):
    """리포트 화면"""

    CSS = """
    ReportScreen {
        align: center middle;
    }

    .report-container {
        width: 70;
        height: auto;
        max-height: 35;
        border: solid cyan;
        padding: 1 2;
        background: $surface;
    }

    .title {
        text-align: center;
        text-style: bold;
        color: cyan;
        margin-bottom: 1;
    }

    .period {
        text-align: center;
        color: yellow;
        margin-bottom: 1;
    }

    .stats-grid {
        layout: grid;
        grid-size: 4;
        grid-gutter: 1;
        margin-bottom: 1;
    }

    .stat-item {
        text-align: center;
        padding: 1;
        background: $panel;
    }

    .stat-value {
        text-style: bold;
        color: green;
    }

    .stat-label {
        color: $text-muted;
    }

    .section-title {
        text-style: bold;
        color: yellow;
        margin-top: 1;
        margin-bottom: 1;
    }

    .todo-list {
        max-height: 10;
        overflow: auto;
    }

    .todo-item {
        padding: 0 1;
    }

    .todo-item.done {
        color: green;
    }

    .todo-item.in_progress {
        color: yellow;
    }

    .todo-item.todo {
        color: $text-muted;
    }

    Button {
        margin-top: 1;
    }

    .button-row {
        align: center middle;
        margin-top: 1;
    }

    .button-row Button {
        margin: 0 1;
    }
    """

    BINDINGS = [
        Binding("escape", "back", "뒤로"),
        Binding("1", "today", "오늘"),
        Binding("2", "weekly", "주간"),
        Binding("3", "season", "시즌"),
    ]

    report_type = reactive("today")
    selected_season_id = reactive(None)

    def compose(self) -> ComposeResult:
        with Container(classes="report-container"):
            yield Static("📊 리포트", classes="title")
            yield Static("", id="period", classes="period")

            with Horizontal(classes="button-row"):
                yield Button("오늘", id="btn_today", variant="primary")
                yield Button("주간", id="btn_weekly")
                yield Button("시즌", id="btn_season")

            with Container(classes="stats-grid", id="stats_grid"):
                pass

            yield Static("상세 내역", classes="section-title")
            with Container(classes="todo-list", id="todo_list"):
                pass

            with Horizontal(classes="button-row"):
                yield Button("닫기", id="close", variant="error")

    def on_mount(self):
        self._update_report()

    def _update_report(self):
        if self.report_type == "season" and self.app.season_manager:
            season = self.app.season_manager.get_current_season()
            self.selected_season_id = season.id if season else None

        report_data = self.app.manager.get_report_data(self.report_type, self.selected_season_id)

        # Update period
        self.query_one("#period", Static).update(f"기간: {report_data['period']}")

        # Update button states
        self.query_one("#btn_today", Button).variant = "primary" if self.report_type == "today" else "default"
        self.query_one("#btn_weekly", Button).variant = "primary" if self.report_type == "weekly" else "default"
        self.query_one("#btn_season", Button).variant = "primary" if self.report_type == "season" else "default"

        # Update stats
        stats_grid = self.query_one("#stats_grid", Container)
        stats_grid.remove_children()

        stats = report_data["stats"]
        stat_items = [
            ("전체", stats["total"]),
            ("대기", stats["todo"]),
            ("진행중", stats["in_progress"]),
            ("완료", stats["done"]),
            ("완료율", f"{stats['completion_rate']}%"),
            ("Epic", stats["epics"]),
            ("Story", stats["stories"]),
            ("Task", stats["tasks"]),
        ]

        for label, value in stat_items:
            with Container(classes="stat-item"):
                yield Static(str(value), classes="stat-value")
                yield Static(label, classes="stat-label")

        # Update todo list
        todo_list = self.query_one("#todo_list", Container)
        todo_list.remove_children()

        status_icons = {"todo": "⬜", "in_progress": "🔄", "done": "✅"}
        type_icons = {"epic": "📁", "story": "📖", "task": "📌"}

        # 오늘 리포트인 경우 생성/완료 분리 표시
        if self.report_type == "today" and report_data.get("created_today") is not None:
            # 오늘 생성된 작업
            created_today = report_data["created_today"]
            todo_list.mount(Static(f"📝 오늘 생성 ({len(created_today)}개)", classes="section-title"))

            if created_today:
                for todo in created_today[:10]:
                    icon = status_icons.get(todo.status, "⬜")
                    type_icon = type_icons.get(todo.type, "📌")
                    text = f"{icon} {type_icon} {todo.content}"
                    todo_list.mount(Static(text, classes=f"todo-item {todo.status}"))
                if len(created_today) > 10:
                    todo_list.mount(Static(f"... 외 {len(created_today) - 10}개", classes="todo-item"))
            else:
                todo_list.mount(Static("없음", classes="todo-item"))

            # 오늘 완료된 작업
            completed_today = report_data["completed_today"]
            todo_list.mount(Static(f"✅ 오늘 완료 ({len(completed_today)}개)", classes="section-title"))

            if completed_today:
                for todo in completed_today[:10]:
                    icon = status_icons.get(todo.status, "⬜")
                    type_icon = type_icons.get(todo.type, "📌")
                    text = f"{icon} {type_icon} {todo.content}"
                    todo_list.mount(Static(text, classes=f"todo-item {todo.status}"))
                if len(completed_today) > 10:
                    todo_list.mount(Static(f"... 외 {len(completed_today) - 10}개", classes="todo-item"))
            else:
                todo_list.mount(Static("없음", classes="todo-item"))
        else:
            # 기존 방식: 전체 목록 표시
            for todo in report_data["todos"][:20]:
                icon = status_icons.get(todo.status, "⬜")
                type_icon = type_icons.get(todo.type, "📌")

                date_info = f"생성: {todo.created_at}" if todo.created_at else ""
                if todo.status == "done" and todo.completed_at:
                    date_info += f" | 완료: {todo.completed_at}"
                elif todo.due_date:
                    date_info += f" | 마감: {todo.due_date}"

                text = f"{icon} {type_icon} {todo.content}"
                if date_info:
                    text += f" [{date_info}]"
                todo_list.mount(Static(text, classes=f"todo-item {todo.status}"))

            if len(report_data["todos"]) > 20:
                todo_list.mount(Static(f"... 외 {len(report_data['todos']) - 20}개", classes="todo-item"))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_today":
            self.report_type = "today"
            self._update_report()
        elif event.button.id == "btn_weekly":
            self.report_type = "weekly"
            self._update_report()
        elif event.button.id == "btn_season":
            self.report_type = "season"
            self._update_report()
        elif event.button.id == "close":
            self.app.pop_screen()

    def action_today(self):
        self.report_type = "today"
        self._update_report()

    def action_weekly(self):
        self.report_type = "weekly"
        self._update_report()

    def action_season(self):
        self.report_type = "season"
        self._update_report()

    def action_back(self):
        self.app.pop_screen()


class TodoTree(Tree):
    """커스텀 트리 위젯"""

    BINDINGS = [
        Binding("space", "toggle_todo", "체크"),
        Binding("d", "delete_todo", "삭제"),
        Binding("a", "add_todo", "추가"),
        Binding("right", "expand_node", "펼치기"),
        Binding("left", "collapse_node", "접기"),
        Binding("enter", "toggle_select", "선택"),
    ]

    class TodoSelected(Message):
        """Todo 항목 선택 메시지"""
        def __init__(self, todo_id: int, todo_type: str):
            super().__init__()
            self.todo_id = todo_id
            self.todo_type = todo_type

    def on_tree_node_highlighted(self, event: Tree.NodeHighlighted) -> None:
        """노드 하이라이트 시 (방향키 이동)"""
        node = event.node
        if node and hasattr(node, 'data') and node.data and hasattr(node.data, 'todo_id'):
            self.post_message(self.TodoSelected(node.data.todo_id, node.data.todo_type))

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """노드 선택 시"""
        node = event.node
        if hasattr(node.data, 'todo_id'):
            self.post_message(self.TodoSelected(node.data.todo_id, node.data.todo_type))

    def action_toggle_todo(self) -> None:
        """스페이스바로 체크 토글 - 부모 화면의 action_toggle 호출"""
        if hasattr(self.screen, 'action_toggle'):
            self.screen.action_toggle()

    def action_delete_todo(self) -> None:
        """d 키로 삭제 - 부모 화면의 action_delete 호출"""
        if hasattr(self.screen, 'action_delete'):
            self.screen.action_delete()

    def action_add_todo(self) -> None:
        """a 키로 추가 - 부모 화면의 action_add 호출"""
        if hasattr(self.screen, 'action_add'):
            self.screen.action_add()


class TodoListScreen(Screen):
    """메인 Todo 목록 화면"""

    CSS = """
    .todo-container {
        height: 100%;
    }

    Tree {
        height: 1fr;
    }

    .jira-bar {
        dock: top;
        height: 1;
        background: $success;
        color: $text;
        padding: 0 1;
        text-align: center;
    }

    .jira-bar.disconnected {
        background: $warning;
    }

    .season-bar {
        dock: top;
        height: 1;
        background: $primary-darken-2;
        color: $text;
        padding: 0 1;
        text-align: center;
    }

    .stats-bar {
        dock: top;
        height: 5;
        background: $primary;
        color: $text;
        padding: 1;
    }

    .stats-row {
        height: 2;
    }
    """

    BINDINGS = [
        Binding("space", "toggle", "체크"),
        Binding("a", "add", "추가"),
        Binding("A", "add_child", "하위추가"),
        Binding("s", "change_status", "상태변경"),
        Binding("d", "delete", "삭제"),
        Binding("i", "show_info", "상세정보"),
        Binding("ctrl+up", "move_up", "위로이동"),
        Binding("ctrl+down", "move_down", "아래로이동"),
        Binding("right", "expand", "펼치기"),
        Binding("left", "collapse", "접기"),
        Binding("e", "expand_all", "전체펼침"),
        Binding("c", "collapse_all", "전체접음"),
        Binding("S", "season", "시즌"),
        Binding("r", "report", "리포트"),
        Binding("j", "jira_sync", "Jira동기화"),
        Binding("ctrl+j", "jira_settings", "Jira설정"),
        Binding("q", "quit", "종료"),
    ]

    selected_todo_id = reactive(None)
    selected_todo_type = reactive(None)

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(classes="todo-container"):
            yield Static(self._get_jira_status(), id="jira-bar", classes="jira-bar")
            yield Static(self._get_season_info(), id="season-bar", classes="season-bar")
            yield Static(self._get_stats(), id="stats", classes="stats-bar")
            yield TodoTree("📋 Todo List", id="todo-tree")
        yield Footer()

    def _get_jira_status(self) -> str:
        """Jira 연결 상태"""
        if self.app.manager.is_jira_enabled():
            return "🔗 Jira 연결됨 | J: 동기화 | Ctrl+J: 설정"
        else:
            return "💾 로컬 저장 | Ctrl+J: Jira 설정"

    def _get_season_info(self) -> str:
        """현재 시즌 정보"""
        if not self.app.season_manager:
            return "📅 시즌: 없음 (S: 시즌 선택)"
        current = self.app.season_manager.get_current_season()
        if current:
            progress = current.get_progress()
            return f"📅 {current.name} ({current.start_date} ~ {current.end_date}) [{progress}%] | S: 시즌 변경 | R: 리포트"
        return "📅 시즌: 없음 (S: 시즌 선택)"

    def _get_stats(self) -> str:
        # 현재 시즌의 todos만 표시
        if self.app.season_manager and self.app.season_manager.current_season_id:
            todos = self.app.manager.get_todos_by_season(self.app.season_manager.current_season_id)
            stats = {
                "total": len(todos),
                "todo": sum(1 for t in todos if t.status == "todo"),
                "in_progress": sum(1 for t in todos if t.status == "in_progress"),
                "done": sum(1 for t in todos if t.status == "done"),
                "epics": sum(1 for t in todos if t.type == "epic"),
                "stories": sum(1 for t in todos if t.type == "story"),
                "tasks": sum(1 for t in todos if t.type == "task")
            }
        else:
            stats = self.app.manager.get_stats()
        return (
            f"📊 전체: {stats['total']} | 📋 대기: {stats['todo']} | 🔄 진행중: {stats['in_progress']} | ✅ 완료: {stats['done']}\n"
            f"📁 Epic: {stats['epics']} | 📖 Story: {stats['stories']} | ✅ Task: {stats['tasks']}"
        )

    def on_mount(self):
        self._refresh_tree()

    def _get_expanded_nodes(self, node) -> set:
        """확장된 노드들의 todo_id 수집"""
        expanded_ids = set()
        if node.is_expanded and hasattr(node, 'data') and node.data and hasattr(node.data, 'todo_id'):
            expanded_ids.add(node.data.todo_id)
        for child in node.children:
            expanded_ids.update(self._get_expanded_nodes(child))
        return expanded_ids

    def _restore_expanded_nodes(self, node, expanded_ids: set):
        """노드 확장 상태 복원"""
        if hasattr(node, 'data') and node.data and hasattr(node.data, 'todo_id'):
            if node.data.todo_id in expanded_ids:
                node.expand()
        for child in node.children:
            self._restore_expanded_nodes(child, expanded_ids)

    def _refresh_tree(self):
        """트리 새로고침"""
        tree = self.query_one("#todo-tree", TodoTree)

        # 현재 확장된 노드들 저장
        expanded_ids = self._get_expanded_nodes(tree.root)

        tree.clear()

        # 시즌별 필터링
        if self.app.season_manager and self.app.season_manager.current_season_id:
            season_id = self.app.season_manager.current_season_id
            all_todos = self.app.manager.get_todos_by_season(season_id)
            root_items = [t for t in all_todos if t.parent_id is None]
        else:
            root_items = self.app.manager.get_root_items()

        self._build_tree_nodes(tree.root, root_items)

        tree.root.expand()

        # 확장 상태 복원
        self._restore_expanded_nodes(tree.root, expanded_ids)

        # 시즌 정보 업데이트
        season_bar = self.query_one("#season-bar", Static)
        season_bar.update(self._get_season_info())

        # 통계 업데이트
        stats = self.query_one("#stats", Static)
        stats.update(self._get_stats())

    def _build_tree_nodes(self, parent_node, items: List[TodoItem]):
        """재귀적으로 트리 노드 빌드"""
        # order, 타입, 우선순위로 정렬
        items = sorted(items, key=lambda t: (
            t.order,
            TodoManager.TYPE_ORDER.get(t.type, 99),
            {"high": 0, "medium": 1, "low": 2}.get(t.priority, 1)
        ))

        for todo in items:
            # 아이콘 설정
            type_icons = {"epic": "📁", "story": "📖", "task": "📌"}
            priority_icons = {"high": "🔴", "medium": "🟡", "low": "🟢"}
            status_icons = {"todo": "⬜", "in_progress": "🔄", "done": "✅"}

            type_icon = type_icons.get(todo.type, "📌")
            priority_icon = priority_icons.get(todo.priority, "🟡")
            status_icon = status_icons.get(todo.status, "⬜")

            due_str = f" (due: {todo.due_date})" if todo.due_date else ""
            jira_str = f" [{todo.jira_key}]" if todo.jira_key else ""
            desc_str = " 📝" if todo.description else ""
            label = f"{status_icon} {type_icon} {priority_icon} [{todo.category}] {todo.content}{jira_str}{due_str}{desc_str}"

            # 노드 데이터 생성
            node_data = type('NodeData', (), {
                'todo_id': todo.id,
                'todo_type': todo.type,
                'todo_status': todo.status
            })()

            node = parent_node.add(label, data=node_data, expand=False)

            # 하위 항목 재귀적으로 추가 (시즌 필터링 적용)
            all_children = self.app.manager.get_children(todo.id)
            if self.app.season_manager and self.app.season_manager.current_season_id:
                season_id = self.app.season_manager.current_season_id
                children = [c for c in all_children if c.season_id == season_id]
            else:
                children = all_children

            if children:
                self._build_tree_nodes(node, children)

    def on_todo_tree_todo_selected(self, event: TodoTree.TodoSelected):
        """트리에서 항목 선택 시"""
        self.selected_todo_id = event.todo_id
        self.selected_todo_type = event.todo_type

    def action_add(self):
        """최상위 항목 추가"""
        self.app.push_screen(AddTodoScreen())

    def action_add_child(self):
        """선택한 항목의 하위 항목 추가"""
        if self.selected_todo_id:
            # 선택된 항목의 타입 찾기
            selected_todo = next(
                (t for t in self.app.manager.todos if t.id == self.selected_todo_id),
                None
            )
            if selected_todo:
                if selected_todo.type == "task":
                    # Task 하위에는 추가할 수 없음
                    return
                self.app.push_screen(AddTodoScreen(
                    parent_id=self.selected_todo_id,
                    parent_type=self.selected_todo_type
                ))
        else:
            self.app.push_screen(AddTodoScreen())

    def action_change_status(self):
        """상태 변경: todo -> in_progress -> done -> todo"""
        if self.selected_todo_id:
            self.app.manager.change_status(self.selected_todo_id)
            self._refresh_tree()

    def action_toggle(self):
        """체크 토글: todo <-> done"""
        if self.selected_todo_id:
            self.app.manager.toggle_check(self.selected_todo_id)
            self._refresh_tree()

    def action_delete(self):
        """삭제"""
        if self.selected_todo_id:
            self.app.manager.delete_todo(self.selected_todo_id)
            self.selected_todo_id = None
            self._refresh_tree()

    def action_show_info(self):
        """상세 정보 팝업 표시"""
        if self.selected_todo_id:
            todo = self.app.manager.get_todo_by_id(self.selected_todo_id)
            if todo:
                self.app.push_screen(DescriptionPopup(
                    todo_id=todo.id,
                    content=todo.content,
                    description=todo.description
                ))

    def action_move_up(self):
        """항목을 위로 이동"""
        if self.selected_todo_id:
            if self.app.manager.move_item_up(self.selected_todo_id):
                self._refresh_tree()

    def action_move_down(self):
        """항목을 아래로 이동"""
        if self.selected_todo_id:
            if self.app.manager.move_item_down(self.selected_todo_id):
                self._refresh_tree()

    def action_expand(self):
        """선택 노드 펼치기"""
        tree = self.query_one("#todo-tree", TodoTree)
        if tree.cursor_node:
            tree.cursor_node.expand()

    def action_collapse(self):
        """선택 노드 접기"""
        tree = self.query_one("#todo-tree", TodoTree)
        if tree.cursor_node:
            tree.cursor_node.collapse()

    def action_expand_all(self):
        """전체 펼치기"""
        tree = self.query_one("#todo-tree", TodoTree)
        tree.root.expand_all()

    def action_collapse_all(self):
        """전체 접기"""
        tree = self.query_one("#todo-tree", TodoTree)
        def collapse_recursive(node):
            node.collapse()
            for child in node.children:
                collapse_recursive(child)
        collapse_recursive(tree.root)
        tree.root.expand()

    def action_season(self):
        """시즌 선택 화면"""
        self.app.push_screen(SeasonSelectScreen())

    def action_report(self):
        """리포트 화면"""
        self.app.push_screen(ReportScreen())

    def action_jira_sync(self):
        """Jira 동기화"""
        if not self.app.manager.is_jira_enabled():
            return

        try:
            synced = self.app.manager.sync_from_jira()
            self._refresh_tree()
            # 동기화 결과 표시
            jira_bar = self.query_one("#jira-bar", Static)
            jira_bar.update(f"🔗 Jira 동기화 완료: {len(synced)}개 항목")
        except Exception as e:
            jira_bar = self.query_one("#jira-bar", Static)
            jira_bar.update(f"Jira 동기화 실패: {e}")

    def action_jira_settings(self):
        """Jira 설정 화면"""
        self.app.push_screen(JiraSetupScreen())

    def on_screen_resume(self):
        self._refresh_tree()


class TodoApp(App):
    """메인 Todo 애플리케이션"""

    CSS = """
    Screen {
        background: $surface;
    }

    Tree {
        background: $surface;
    }

    Tree:focus {
        background: $surface;
    }
    """

    SCREENS = {
        "main": TodoListScreen,
        "add": AddTodoScreen,
        "add_season": AddSeasonScreen,
        "select_season": SeasonSelectScreen,
        "report": ReportScreen,
        "setup": SetupScreen,
        "jira_setup": JiraSetupScreen,
    }

    BINDINGS = [
        Binding("q", "quit", "종료"),
    ]

    def __init__(self):
        self.manager = TodoManager()
        config_path = Path(__file__).parent / "config.json"
        self.season_manager = SeasonManager(config_path)
        self.manager.set_season_manager(self.season_manager)

        # Jira 클라이언트 초기화
        self._init_jira_client()

        super().__init__()

    def _init_jira_client(self):
        """Jira 클라이언트 초기화"""
        if not JIRA_AVAILABLE:
            return

        try:
            with open(self.manager.config_path, "r", encoding="utf-8") as f:
                config = json.load(f)

            jira_config = config.get("jira", {})
            if jira_config.get("enabled", False):
                jira_config_obj = JiraConfig.from_dict(jira_config)
                if jira_config_obj.is_valid():
                    self.manager.set_jira_client(JiraClient(jira_config_obj))
        except Exception as e:
            print(f"Jira 초기화 실패: {e}")

    def on_mount(self):
        self.push_screen("main")


def main():
    """메인 함수"""
    app = TodoApp()
    app.run()


if __name__ == "__main__":
    main()
