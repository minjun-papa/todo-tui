"""Add/Edit Task screens."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.screen import Screen
from textual.widgets import Button, Input, Label, Select, Static


class AddTaskScreen(Screen):
    """Simplified task addition dialog."""

    CSS = """
    AddTaskScreen {
        align: center middle;
    }

    .add-container {
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

    Input, Select {
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
        margin: 0 2;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(self, sprint_id: int, season_id: int):
        super().__init__()
        self.sprint_id = sprint_id
        self.season_id = season_id

    def compose(self) -> ComposeResult:
        with Container(classes="add-container"):
            yield Static("Add Task", classes="title")
            yield Label("Task content *")
            yield Input(placeholder="What needs to be done?", id="content")
            yield Label("Priority")
            yield Select(
                [("High", "high"), ("Medium", "medium"), ("Low", "low")],
                id="priority",
                value="medium",
            )
            yield Label("Due date")
            yield Input(placeholder="YYYY-MM-DD", id="due_date")
            with Horizontal(classes="button-row"):
                yield Button("Add (Enter)", variant="success", id="add")
                yield Button("Cancel (Esc)", variant="error", id="cancel")

    def on_mount(self) -> None:
        self.query_one("#content", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "add":
            self.action_submit()
        elif event.button.id == "cancel":
            self.app.pop_screen()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "content":
            self.action_submit()

    def action_submit(self) -> None:
        content = self.query_one("#content", Input).value.strip()
        if not content:
            self.notify("Content is required", severity="warning")
            return

        priority = self.query_one("#priority", Select).value or "medium"
        due_date = self.query_one("#due_date", Input).value.strip() or None

        self.app.task_mgr.create(
            content=content,
            sprint_id=self.sprint_id,
            season_id=self.season_id,
            priority=priority,
            due_date=due_date,
        )
        self.app.pop_screen()

    def action_cancel(self) -> None:
        self.app.pop_screen()


class EditTaskScreen(Screen):
    """Edit existing task dialog."""

    CSS = """
    EditTaskScreen {
        align: center middle;
    }

    .edit-container {
        width: 60;
        height: auto;
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

    Input, Select {
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
        margin: 0 2;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(self, task_id: int):
        super().__init__()
        self.task_id = task_id

    def compose(self) -> ComposeResult:
        with Container(classes="edit-container"):
            yield Static("Edit Task", classes="title")
            yield Label("Task content *")
            yield Input(id="content")
            yield Label("Priority")
            yield Select(
                [("High", "high"), ("Medium", "medium"), ("Low", "low")],
                id="priority",
                value="medium",
            )
            yield Label("Due date")
            yield Input(id="due_date")
            yield Label("Memo (markdown)")
            yield Input(id="memo")
            with Horizontal(classes="button-row"):
                yield Button("Save (Enter)", variant="success", id="save")
                yield Button("Cancel (Esc)", variant="error", id="cancel")

    def on_mount(self) -> None:
        task = self.app.task_mgr.get(self.task_id)
        if not task:
            self.app.pop_screen()
            return

        content_input = self.query_one("#content", Input)
        content_input.value = task.content
        content_input.focus()

        self.query_one("#priority", Select).value = task.priority

        if task.due_date:
            self.query_one("#due_date", Input).value = task.due_date
        if task.memo:
            self.query_one("#memo", Input).value = task.memo

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":
            self.action_save()
        elif event.button.id == "cancel":
            self.app.pop_screen()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "content":
            self.action_save()

    def action_save(self) -> None:
        content = self.query_one("#content", Input).value.strip()
        if not content:
            self.notify("Content is required", severity="warning")
            return

        priority = self.query_one("#priority", Select).value or "medium"
        due_date = self.query_one("#due_date", Input).value.strip() or None
        memo = self.query_one("#memo", Input).value

        self.app.task_mgr.update(
            self.task_id,
            content=content,
            priority=priority,
            due_date=due_date,
            memo=memo,
        )
        self.app.pop_screen()

    def action_cancel(self) -> None:
        self.app.pop_screen()
