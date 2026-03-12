#!/usr/bin/env python3
"""
Terminal Todo App - TUI 기반 할 일 관리 애플리케이션
Epic > Story > Task 계층 구조 지원
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
    parent_id: Optional[int] = None

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
            "parent_id": self.parent_id
        }

    @classmethod
    def from_dict(cls, data: dict):
        # 기존 completed 필드를 status로 변환 (호환성)
        if "completed" in data and "status" not in data:
            data["status"] = "done" if data["completed"] else "todo"
            del data["completed"]
        return cls(**data)


class TodoManager:
    """Todo 관리 클래스"""

    TYPE_ORDER = {"epic": 0, "story": 1, "task": 2}

    def __init__(self):
        self.config_path = Path(__file__).parent / "config.json"
        self.todos: List[TodoItem] = []
        self.todo_file: Path = self._get_todo_file_path()
        self._load_todos()

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

    def _save_config(self, save_path: str):
        """설정을 저장합니다."""
        config = {"save_path": save_path}
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

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

    def add_todo(self, content: str, type: str = "task", category: str = "general",
                 priority: str = "medium", due_date: Optional[str] = None,
                 parent_id: Optional[int] = None) -> TodoItem:
        """새 할 일을 추가합니다."""
        new_id = max([t.id for t in self.todos], default=0) + 1

        todo = TodoItem(
            id=new_id,
            content=content,
            type=type,
            category=category,
            priority=priority,
            due_date=due_date,
            status="todo",
            created_at=datetime.now().strftime("%Y-%m-%d"),
            parent_id=parent_id
        )

        self.todos.append(todo)
        self._save_todos()
        return todo

    def change_status(self, todo_id: int) -> Optional[TodoItem]:
        """할 일 상태를 순환합니다: todo -> in_progress -> done -> todo"""
        status_order = ["todo", "in_progress", "done"]
        for todo in self.todos:
            if todo.id == todo_id:
                current_idx = status_order.index(todo.status)
                todo.status = status_order[(current_idx + 1) % 3]
                self._save_todos()
                return todo
        return None

    def toggle_todo(self, todo_id: int) -> Optional[TodoItem]:
        """할 일 완료 상태를 토글합니다 (호환성 유지)."""
        return self.change_status(todo_id)

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

        # 빈 문자열이면 None으로 변환
        if due_date == "":
            due_date = None

        # 부모 ID 설정 (생성자에서 받은 값 사용)
        parent_id = self.default_parent_id

        self.app.manager.add_todo(
            content=content,
            type=type_value,
            category="general",  # 카테고리는 기본값 사용
            priority=priority,
            due_date=due_date,
            parent_id=parent_id
        )
        self.app.pop_screen()

    def action_cancel(self):
        self.app.pop_screen()


class TodoTree(Tree):
    """커스텀 트리 위젯"""

    BINDINGS = [
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


class TodoListScreen(Screen):
    """메인 Todo 목록 화면"""

    CSS = """
    .todo-container {
        height: 100%;
    }

    Tree {
        height: 1fr;
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

    .in-progress-bar {
        dock: top;
        background: $warning;
        color: $text;
        padding: 1;
        margin-top: 5;
    }

    .in-progress-title {
        text-style: bold;
        margin-bottom: 1;
    }
    """

    BINDINGS = [
        Binding("a", "add", "추가"),
        Binding("A", "add_child", "하위추가"),
        Binding("s", "change_status", "상태변경"),
        Binding("d", "delete", "삭제"),
        Binding("right", "expand", "펼치기"),
        Binding("left", "collapse", "접기"),
        Binding("e", "expand_all", "전체펼침"),
        Binding("c", "collapse_all", "전체접음"),
        Binding("q", "quit", "종료"),
    ]

    selected_todo_id = reactive(None)
    selected_todo_type = reactive(None)

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(classes="todo-container"):
            yield Static(self._get_stats(), id="stats", classes="stats-bar")
            yield Static(self._get_in_progress(), id="in-progress", classes="in-progress-bar")
            yield TodoTree("📋 Todo List", id="todo-tree")
        yield Footer()

    def _get_stats(self) -> str:
        stats = self.app.manager.get_stats()
        return (
            f"📊 전체: {stats['total']} | 📋 대기: {stats['todo']} | 🔄 진행중: {stats['in_progress']} | ✅ 완료: {stats['done']}\n"
            f"📁 Epic: {stats['epics']} | 📖 Story: {stats['stories']} | ✅ Task: {stats['tasks']}"
        )

    def _get_in_progress(self) -> str:
        """진행중인 항목 목록 반환"""
        in_progress_items = self.app.manager.get_in_progress_items()
        if not in_progress_items:
            return "🔄 진행중: 없음"

        items_str = " | ".join([
            f"{t.content} ({t.type})"
            for t in in_progress_items[:5]  # 최대 5개까지만 표시
        ])
        if len(in_progress_items) > 5:
            items_str += f" ... 외 {len(in_progress_items) - 5}개"

        return f"🔄 진행중 ({len(in_progress_items)}): {items_str}"

    def on_mount(self):
        self._refresh_tree()

    def _refresh_tree(self):
        """트리 새로고침"""
        tree = self.query_one("#todo-tree", TodoTree)
        tree.clear()

        root_items = self.app.manager.get_root_items()
        self._build_tree_nodes(tree.root, root_items)

        tree.root.expand()

        # 통계 업데이트
        stats = self.query_one("#stats", Static)
        stats.update(self._get_stats())

        # 진행중 항목 업데이트
        in_progress = self.query_one("#in-progress", Static)
        in_progress.update(self._get_in_progress())

    def _build_tree_nodes(self, parent_node, items: List[TodoItem]):
        """재귀적으로 트리 노드 빌드"""
        # 타입 및 우선순위로 정렬
        items = sorted(items, key=lambda t: (
            TodoManager.TYPE_ORDER.get(t.type, 99),
            {"high": 0, "medium": 1, "low": 2}.get(t.priority, 1)
        ))

        for todo in items:
            # 아이콘 설정
            type_icons = {"epic": "📁", "story": "📖", "task": "✅"}
            priority_icons = {"high": "🔴", "medium": "🟡", "low": "🟢"}
            status_icons = {"todo": "○", "in_progress": "◐", "done": "●"}

            type_icon = type_icons.get(todo.type, "📌")
            priority_icon = priority_icons.get(todo.priority, "🟡")
            status_icon = status_icons.get(todo.status, "○")

            due_str = f" (due: {todo.due_date})" if todo.due_date else ""
            label = f"{status_icon} {type_icon} {priority_icon} [{todo.category}] {todo.content}{due_str}"

            # 노드 데이터 생성
            node_data = type('NodeData', (), {
                'todo_id': todo.id,
                'todo_type': todo.type,
                'todo_status': todo.status
            })()

            node = parent_node.add(label, data=node_data, expand=False)

            # 하위 항목 재귀적으로 추가
            children = self.app.manager.get_children(todo.id)
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

    def action_delete(self):
        """삭제"""
        if self.selected_todo_id:
            self.app.manager.delete_todo(self.selected_todo_id)
            self.selected_todo_id = None
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
    }

    BINDINGS = [
        Binding("q", "quit", "종료"),
    ]

    def __init__(self):
        self.manager = TodoManager()
        super().__init__()

    def on_mount(self):
        self.push_screen("main")


def main():
    """메인 함수"""
    app = TodoApp()
    app.run()


if __name__ == "__main__":
    main()
