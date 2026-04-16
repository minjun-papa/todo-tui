"""Main WorkbenchScreen: Season > Sprint > Task tree view."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.events import Key
from textual.message import Message
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Static, Tree

from ..managers import SeasonManager, SprintManager, TaskManager
from ..models import Season, Sprint, Task


class WorkbenchTree(Tree):
    """Custom tree that prevents space from toggling node expand/collapse."""

    class TaskAction(Message):
        """Posted when user triggers action on a task node."""

        def __init__(self, action: str, task_id: int) -> None:
            super().__init__()
            self.action = action
            self.task_id = task_id

    def key_space(self, event: Key) -> None:
        """Override parent's space -> toggle_node. Instead toggle task check."""
        event.prevent_default()
        event.stop()
        node = self.cursor_node
        if node and hasattr(node, "data") and node.data and node.data.item_type == "task":
            self.post_message(self.TaskAction("toggle", node.data.item_id))


class WorkbenchScreen(Screen):
    """Main workbench: Season > Sprint > Task tree."""

    CSS = """
    .workbench-container {
        height: 100%;
    }

    Tree {
        height: 1fr;
    }

    .status-bar {
        dock: top;
        height: 3;
        background: $primary;
        color: $text;
        padding: 0 1;
    }
    """

    BINDINGS = [
        Binding("a", "add", "Add"),
        Binding("e", "edit", "Edit"),
        Binding("d", "delete", "Del"),
        Binding("s", "cycle_status", "Status"),
        Binding("m", "memo", "Memo"),
        Binding("t", "go_today", "Today"),
        Binding("x", "expand_all", "ExpandAll"),
        Binding("c", "collapse_all", "Collapse"),
        Binding("S", "season", "Season"),
        Binding("p", "prev_sprint", "Prev"),
        Binding("n", "next_sprint", "Next"),
        Binding("r", "report", "Report"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self, season_mgr: SeasonManager, sprint_mgr: SprintManager, task_mgr: TaskManager):
        super().__init__()
        self.season_mgr = season_mgr
        self.sprint_mgr = sprint_mgr
        self.task_mgr = task_mgr
        self._expanded_ids: set = set()

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(classes="workbench-container"):
            yield Static(self._render_status(), id="status-bar", classes="status-bar")
            yield WorkbenchTree("todo-tui v2", id="workbench-tree")
        yield Footer()

    def on_mount(self) -> None:
        self._refresh()

    def on_workbench_tree_task_action(self, event: WorkbenchTree.TaskAction) -> None:
        """Handle task actions from the tree (space key)."""
        if event.action == "toggle":
            self.task_mgr.toggle_check(event.task_id)
            self._update_task_node(event.task_id)
            self._update_status_bar()

    def _update_task_node(self, task_id: int) -> None:
        """Update a single task node label without rebuilding the tree."""
        tree = self.query_one("#workbench-tree", WorkbenchTree)
        task = self.task_mgr.get(task_id)
        if not task:
            return
        node = self._find_node_by_id(tree.root, task_id)
        if node:
            node.set_label(self._task_label(task))

    def _find_node_by_id(self, node, task_id: int):
        if hasattr(node, "data") and node.data and hasattr(node.data, "item_id"):
            if node.data.item_type == "task" and node.data.item_id == task_id:
                return node
        for child in node.children:
            result = self._find_node_by_id(child, task_id)
            if result:
                return result
        return None

    def _get_cursor_task_id(self) -> Optional[int]:
        """Get task_id from current cursor position."""
        tree = self.query_one("#workbench-tree", WorkbenchTree)
        node = tree.cursor_node
        if node and hasattr(node, "data") and node.data and node.data.item_type == "task":
            return node.data.item_id
        return None

    def _require_task(self) -> Optional[int]:
        tid = self._get_cursor_task_id()
        if tid:
            return tid
        self.notify("Move cursor to a task first (arrow keys)", severity="warning")
        return None

    # --- Tree rendering ---

    def _render_status(self) -> str:
        season = self.season_mgr.get_current()
        lines = []
        if season:
            progress = season.get_progress()
            lines.append(f"Season: {season.name} ({season.start_date} ~ {season.end_date}) [{progress:.0f}%]")
            sprint = self.sprint_mgr.get_current_sprint(season.id)
            if sprint:
                stats = self.sprint_mgr.get_stats(sprint.id, self.task_mgr)
                lines.append(f"Sprint: {sprint.name} | {stats['done']}/{stats['total']} done")
            else:
                lines.append("Sprint: none (press 't' to create)")
        else:
            lines.append("No active season (press 'S' to create)")
        return "\n".join(lines)

    def _refresh(self) -> None:
        tree = self.query_one("#workbench-tree", WorkbenchTree)
        self._save_expanded(tree.root)
        tree.clear()

        seasons = self.season_mgr.get_all()
        if not seasons:
            tree.root.add("No seasons yet - press S to create one")
            tree.root.expand()
            self._update_status_bar()
            return

        for season in seasons:
            sn = tree.root.add(self._season_label(season), data=_NodeData(season.id, "season"), expand=season.id in self._expanded_ids)
            for sprint in self.sprint_mgr.get_for_season(season.id):
                spn = sn.add(self._sprint_label(sprint), data=_NodeData(sprint.id, "sprint"), expand=sprint.id in self._expanded_ids)
                for task in self.task_mgr.get_by_sprint(sprint.id):
                    spn.add(self._task_label(task), data=_NodeData(task.id, "task"))
            unassigned = [t for t in self.task_mgr.get_by_season(season.id) if t.sprint_id is None]
            if unassigned:
                un = sn.add("  Unassigned", data=_NodeData(0, "unassigned"), expand=True)
                for task in unassigned:
                    un.add(self._task_label(task), data=_NodeData(task.id, "task"))

        tree.root.expand()
        self._update_status_bar()

    def _save_expanded(self, node) -> None:
        if hasattr(node, "data") and node.data and hasattr(node.data, "item_id"):
            if node.is_expanded:
                self._expanded_ids.add(node.data.item_id)
            elif node.data.item_id in self._expanded_ids:
                self._expanded_ids.discard(node.data.item_id)
        for child in node.children:
            self._save_expanded(child)

    def _update_status_bar(self) -> None:
        self.query_one("#status-bar", Static).update(self._render_status())

    def _season_label(self, s: Season) -> str:
        tag = "[archived]" if s.status != "active" else ""
        return f"{tag} {s.name} ({s.start_date} ~ {s.end_date}) [{s.get_progress():.0f}%]"

    def _sprint_label(self, sp: Sprint) -> str:
        st = self.sprint_mgr.get_stats(sp.id, self.task_mgr)
        tag = "[done]" if sp.status != "active" else ""
        return f"{tag} {sp.name} | {st['done']}/{st['total']}"

    def _task_label(self, t: Task) -> str:
        si = {"todo": "[ ]", "in_progress": "[~]", "done": "[x]"}.get(t.status, "[ ]")
        pi = {"high": "!", "medium": "-", "low": "."}.get(t.priority, "-")
        mi = "+" if t.memo else ""
        di = f" due:{t.due_date}" if t.due_date else ""
        return f"{si} {pi} {t.content}{di} {mi}"

    # --- Actions ---

    def action_add(self) -> None:
        from .add_task import AddTaskScreen
        season = self.season_mgr.get_current()
        if not season:
            self.notify("No active season. Press S.", severity="warning")
            return
        sprint = self.sprint_mgr.get_current_sprint(season.id)
        if not sprint:
            sprint = self.sprint_mgr.auto_create_weekly_sprint(season.id)
        self.app.push_screen(AddTaskScreen(sprint.id, season.id))

    def action_edit(self) -> None:
        tid = self._require_task()
        if tid is None:
            return
        from .add_task import EditTaskScreen
        self.app.push_screen(EditTaskScreen(tid))

    def action_cycle_status(self) -> None:
        tid = self._require_task()
        if tid is None:
            return
        self.task_mgr.toggle_status(tid)
        self._update_task_node(tid)
        self._update_status_bar()

    def action_delete(self) -> None:
        tid = self._require_task()
        if tid is None:
            return
        task = self.task_mgr.get(tid)
        if not task:
            return
        self.app.push_screen(
            ConfirmScreen(f"Delete '{task.content}'?", lambda t=tid: self._do_delete(t))
        )

    def _do_delete(self, task_id: int) -> None:
        self.task_mgr.delete(task_id)
        self._refresh()

    def action_memo(self) -> None:
        tid = self._require_task()
        if tid is None:
            return
        from .memo import MemoScreen
        self.app.push_screen(MemoScreen(tid))

    def action_go_today(self) -> None:
        season = self.season_mgr.get_current()
        if not season:
            self.notify("No active season. Press S.", severity="warning")
            return
        sprint = self.sprint_mgr.get_current_sprint(season.id)
        if not sprint:
            sprint = self.sprint_mgr.auto_create_weekly_sprint(season.id)
        self._expanded_ids.add(season.id)
        self._expanded_ids.add(sprint.id)
        self._refresh()

    def action_season(self) -> None:
        from .season_select import SeasonSelectScreen
        self.app.push_screen(SeasonSelectScreen())

    def action_prev_sprint(self) -> None:
        self._navigate_sprint(-1)

    def action_next_sprint(self) -> None:
        self._navigate_sprint(1)

    def _navigate_sprint(self, direction: int) -> None:
        season = self.season_mgr.get_current()
        if not season:
            return
        sprints = self.sprint_mgr.get_for_season(season.id)
        if not sprints:
            return
        current = self.sprint_mgr.get_current_sprint(season.id)
        if current:
            idx = next((i for i, s in enumerate(sprints) if s.id == current.id), 0)
            target = sprints[max(0, min(len(sprints) - 1, idx + direction))]
            self._expanded_ids.add(season.id)
            self._expanded_ids.add(target.id)
        self._refresh()

    def action_report(self) -> None:
        from .report import ReportScreen
        self.app.push_screen(ReportScreen())

    def action_expand_all(self) -> None:
        tree = self.query_one("#workbench-tree", WorkbenchTree)
        tree.root.expand_all()

    def action_collapse_all(self) -> None:
        tree = self.query_one("#workbench-tree", WorkbenchTree)
        for child in tree.root.children:
            child.collapse()
        tree.root.expand()

    def on_screen_resume(self) -> None:
        self._refresh()


class ConfirmScreen(Screen):
    """Simple yes/no confirmation dialog."""

    CSS = """
    ConfirmScreen {
        align: center middle;
    }
    .confirm-container {
        width: 50;
        height: auto;
        border: solid red;
        padding: 1 2;
        background: $surface;
    }
    .confirm-msg { margin-bottom: 1; }
    .confirm-btns { align: center middle; margin-top: 1; }
    .confirm-btns Button { margin: 0 2; }
    """

    BINDINGS = [
        Binding("escape", "cancel", "No"),
        Binding("y", "yes", "Yes"),
        Binding("n", "cancel", "No"),
    ]

    def __init__(self, message: str, on_yes: callable):
        super().__init__()
        self.message = message
        self.on_yes = on_yes

    def compose(self) -> ComposeResult:
        with Container(classes="confirm-container"):
            yield Static(self.message, classes="confirm-msg")
            with Horizontal(classes="confirm-btns"):
                yield Button("Yes (y)", variant="error", id="yes")
                yield Button("No (n/esc)", variant="primary", id="no")

    def on_button_pressed(self, event) -> None:
        if event.button.id == "yes":
            self.on_yes()
        self.app.pop_screen()

    def action_yes(self) -> None:
        self.on_yes()
        self.app.pop_screen()

    def action_cancel(self) -> None:
        self.app.pop_screen()


class _NodeData:
    __slots__ = ("item_id", "item_type")

    def __init__(self, item_id: int, item_type: str):
        self.item_id = item_id
        self.item_type = item_type
