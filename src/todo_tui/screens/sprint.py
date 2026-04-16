"""Sprint detail and management screen."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.widgets import Button, Static


class SprintScreen(Screen):
    """Sprint detail view with task list and stats."""

    CSS = """
    SprintScreen {
        align: center middle;
    }

    .sprint-container {
        width: 60;
        height: auto;
        max-height: 30;
        border: solid yellow;
        padding: 1 2;
        background: $surface;
    }

    .title {
        text-align: center;
        text-style: bold;
        color: yellow;
        margin-bottom: 1;
    }

    .stats {
        margin-bottom: 1;
        padding: 1;
        background: $panel;
    }

    .task-item {
        padding: 0 1;
    }

    .task-item.done { color: green; }
    .task-item.in_progress { color: yellow; }
    .task-item.todo { color: $text-muted; }

    .task-list {
        max-height: 12;
        overflow: auto;
    }
    """

    BINDINGS = [
        Binding("escape", "back", "Back"),
    ]

    def __init__(self, sprint_id: int):
        super().__init__()
        self.sprint_id = sprint_id

    def compose(self) -> ComposeResult:
        with Container(classes="sprint-container"):
            yield Static("Sprint Detail", classes="title")
            yield Static("", id="sprint_info")
            yield Static("", id="stats", classes="stats")
            yield Static("Tasks", classes="title")
            with Vertical(classes="task-list", id="task_list"):
                pass
            yield Button("Close", id="close", variant="error")

    def on_mount(self):
        self._refresh()

    def _refresh(self):
        sprint = self.app.sprint_mgr.get(self.sprint_id)
        if not sprint:
            return

        info = self.query_one("#sprint_info", Static)
        info.update(f"{sprint.name}\n{sprint.start_date} ~ {sprint.end_date}\nGoal: {sprint.goal or 'N/A'}")

        stats_widget = self.query_one("#stats", Static)
        stats = self.app.sprint_mgr.get_stats(self.sprint_id, self.app.task_mgr)
        stats_widget.update(
            f"Total: {stats['total']} | Todo: {stats['todo']} | "
            f"In Progress: {stats['in_progress']} | Done: {stats['done']} | "
            f"Rate: {stats['completion_rate']}%"
        )

        task_list = self.query_one("#task_list", Vertical)
        task_list.remove_children()

        tasks = self.app.task_mgr.get_by_sprint(self.sprint_id)
        status_icons = {"todo": "[ ]", "in_progress": "[~]", "done": "[x]"}
        for task in tasks:
            icon = status_icons.get(task.status, "[ ]")
            task_list.mount(Static(f"{icon} {task.content}", classes=f"task-item {task.status}"))

        if not tasks:
            task_list.mount(Static("No tasks in this sprint"))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "close":
            self.app.pop_screen()

    def action_back(self):
        self.app.pop_screen()
