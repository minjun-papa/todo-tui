"""Season selection and management screen."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.widgets import Button, Input, Label, Static


class SeasonButton(Button):
    """Button that carries season id as an attribute instead of in the ID."""

    def __init__(self, label: str, season_id: int, **kwargs):
        super().__init__(label, **kwargs)
        self.season_id = season_id


class SeasonSelectScreen(Screen):
    """Season selection, creation, and management."""

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
        width: 100%;
    }

    .no-season {
        color: $text-muted;
        text-align: center;
        margin-top: 1;
    }

    Input {
        width: 100%;
        margin-bottom: 1;
    }

    Label {
        text-style: bold;
        margin-bottom: 1;
    }

    Button {
        margin-bottom: 1;
    }

    .create-section {
        margin-top: 1;
        padding-top: 1;
        border-top: solid $primary;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    def compose(self) -> ComposeResult:
        with Container(classes="select-container"):
            yield Static("Season Management", classes="title")

            yield Static("Active Seasons", classes="section-title")
            with Vertical(id="active-seasons"):
                pass

            yield Static("Archived Seasons", classes="section-title")
            with Vertical(id="archived-seasons"):
                pass

            with Container(classes="create-section"):
                yield Static("Create New Season", classes="section-title")
                yield Label("Name")
                yield Input(placeholder="e.g. 2026 Spring", id="season_name")
                yield Label("Start date")
                yield Input(placeholder="YYYY-MM-DD", id="start_date")
                yield Label("End date")
                yield Input(placeholder="YYYY-MM-DD", id="end_date")
                yield Button("Create Season", variant="success", id="create_season")

            yield Button("Cancel", id="cancel", variant="error")

    def on_mount(self):
        self._populate_lists()

    def _populate_lists(self):
        active = self.query_one("#active-seasons", Vertical)
        archived = self.query_one("#archived-seasons", Vertical)
        active.remove_children()
        archived.remove_children()

        for season in self.app.season_mgr.get_active():
            is_current = season.id == self.app.season_mgr.current_season_id
            progress = season.get_progress()
            marker = "* " if is_current else ""
            label = f"{marker}{season.name} ({season.start_date} ~ {season.end_date}) [{progress:.0f}%]"
            btn = SeasonButton(label, season.id, classes="season-item")
            if is_current:
                btn.variant = "success"
            active.mount(btn)

        if not self.app.season_mgr.get_active():
            active.mount(Static("No active seasons", classes="no-season"))

        for season in self.app.season_mgr.get_archived():
            label = f"{season.name} ({season.start_date} ~ {season.end_date}) [{season.status}]"
            archived.mount(SeasonButton(label, season.id, classes="season-item"))

        if not self.app.season_mgr.get_archived():
            archived.mount(Static("No archived seasons", classes="no-season"))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn = event.button
        if btn.id == "create_season":
            self._create_season()
        elif btn.id == "cancel":
            self.app.pop_screen()
        elif isinstance(btn, SeasonButton):
            self.app.season_mgr.set_current(btn.season_id)
            self.app.pop_screen()

    def _create_season(self):
        from datetime import datetime

        name = self.query_one("#season_name", Input).value.strip()
        start = self.query_one("#start_date", Input).value.strip()
        end = self.query_one("#end_date", Input).value.strip()

        if not name or not start or not end:
            self.notify("All fields required", severity="warning")
            return

        try:
            datetime.strptime(start, "%Y-%m-%d")
            datetime.strptime(end, "%Y-%m-%d")
        except ValueError:
            self.notify("Invalid date format (YYYY-MM-DD)", severity="error")
            return

        season = self.app.season_mgr.create(name, start, end)
        self.app.season_mgr.set_current(season.id)
        self.notify(f"Season '{name}' created")
        self.app.pop_screen()

    def action_cancel(self):
        self.app.pop_screen()
