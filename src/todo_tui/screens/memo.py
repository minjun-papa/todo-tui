"""Memo editing screen for tasks."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Static, TextArea


class MemoScreen(Screen):
    """View and edit task memo (markdown supported)."""

    CSS = """
    MemoScreen {
        align: center middle;
    }

    .memo-container {
        width: 70;
        height: 30;
        border: solid cyan;
        padding: 1 2;
        background: $surface;
    }

    .memo-title {
        text-style: bold;
        color: cyan;
        margin-bottom: 1;
    }

    TextArea {
        height: 1fr;
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
        Binding("ctrl+s", "save", "Save"),
    ]

    def __init__(self, task_id: int):
        super().__init__()
        self.task_id = task_id

    def compose(self) -> ComposeResult:
        with Container(classes="memo-container"):
            yield Static("Memo Editor", classes="memo-title")
            task = self.app.task_mgr.get(self.task_id)
            memo_text = task.memo if task else ""
            task_name = task.content if task else "Unknown"
            yield Static(f"Task: {task_name}")
            yield TextArea(memo_text, id="memo_area", language="markdown")
            with Horizontal(classes="button-row"):
                yield Button("Save", variant="success", id="save")
                yield Button("Cancel", variant="error", id="cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":
            self.action_save()
        elif event.button.id == "cancel":
            self.app.pop_screen()

    def action_save(self):
        memo = self.query_one("#memo_area", TextArea).text
        self.app.task_mgr.update_memo(self.task_id, memo)
        self.app.pop_screen()

    def action_cancel(self):
        self.app.pop_screen()
