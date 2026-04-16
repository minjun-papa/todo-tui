"""Report screen: Today / Sprint / Season reports."""

from datetime import datetime

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Button, Static


class ReportScreen(Screen):
    """Report view with Today, Sprint, and Season tabs."""

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

    .stats {
        margin-bottom: 1;
        padding: 1;
        background: $panel;
    }

    .section-title {
        text-style: bold;
        color: yellow;
        margin-top: 1;
        margin-bottom: 1;
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

    .button-row {
        align: center middle;
        margin-top: 1;
    }

    .button-row Button {
        margin: 0 1;
    }
    """

    BINDINGS = [
        Binding("escape", "back", "Back"),
        Binding("1", "show_today", "Today"),
        Binding("2", "show_sprint", "Sprint"),
        Binding("3", "show_season", "Season"),
    ]

    report_type = reactive("today")

    def compose(self) -> ComposeResult:
        with Container(classes="report-container"):
            yield Static("Report", classes="title")
            yield Static("", id="period", classes="period")

            with Horizontal(classes="button-row"):
                yield Button("Today", id="btn_today", variant="primary")
                yield Button("Sprint", id="btn_sprint")
                yield Button("Season", id="btn_season")

            yield Static("", id="stats", classes="stats")
            yield Static("Details", classes="section-title")
            with Vertical(classes="task-list", id="task_list"):
                pass

            with Horizontal(classes="button-row"):
                yield Button("Close", id="close", variant="error")

    def on_mount(self):
        self._update_report()

    def _update_report(self):
        task_list = self.query_one("#task_list", Vertical)
        period_widget = self.query_one("#period", Static)
        stats_widget = self.query_one("#stats", Static)

        task_list.remove_children()

        # Update button states
        self.query_one("#btn_today", Button).variant = "primary" if self.report_type == "today" else "default"
        self.query_one("#btn_sprint", Button).variant = "primary" if self.report_type == "sprint" else "default"
        self.query_one("#btn_season", Button).variant = "primary" if self.report_type == "season" else "default"

        status_icons = {"todo": "[ ]", "in_progress": "[~]", "done": "[x]"}

        if self.report_type == "today":
            today = datetime.now().strftime("%Y-%m-%d")
            period_widget.update(f"Today: {today}")
            tasks = self.app.task_mgr.get_today_tasks()
            stats = self._calc_stats(tasks)
            stats_widget.update(self._format_stats(stats))
            for task in tasks[:20]:
                icon = status_icons.get(task.status, "[ ]")
                task_list.mount(Static(f"{icon} {task.content}", classes=f"task-item {task.status}"))

        elif self.report_type == "sprint":
            season = self.app.season_mgr.get_current()
            if season:
                sprint = self.app.sprint_mgr.get_current_sprint(season.id)
                if sprint:
                    period_widget.update(f"Sprint: {sprint.name}")
                    tasks = self.app.task_mgr.get_by_sprint(sprint.id)
                    stats = self.app.sprint_mgr.get_stats(sprint.id, self.app.task_mgr)
                    stats_widget.update(self._format_stats(stats))
                    for task in tasks:
                        icon = status_icons.get(task.status, "[ ]")
                        task_list.mount(Static(f"{icon} {task.content}", classes=f"task-item {task.status}"))
                else:
                    period_widget.update("No current sprint")
                    stats_widget.update("N/A")
            else:
                period_widget.update("No active season")
                stats_widget.update("N/A")

        elif self.report_type == "season":
            season = self.app.season_mgr.get_current()
            if season:
                progress = season.get_progress()
                period_widget.update(f"Season: {season.name} [{progress:.0f}%]")
                tasks = self.app.task_mgr.get_by_season(season.id)
                stats = self.app.task_mgr.get_stats(season_id=season.id)
                stats_widget.update(self._format_stats(stats))
                for task in tasks[:30]:
                    icon = status_icons.get(task.status, "[ ]")
                    task_list.mount(Static(f"{icon} {task.content}", classes=f"task-item {task.status}"))
            else:
                period_widget.update("No active season")
                stats_widget.update("N/A")

        if not task_list.children:
            task_list.mount(Static("No tasks found"))

    def _calc_stats(self, tasks) -> dict:
        total = len(tasks)
        done = sum(1 for t in tasks if t.status == "done")
        return {
            "total": total,
            "todo": sum(1 for t in tasks if t.status == "todo"),
            "in_progress": sum(1 for t in tasks if t.status == "in_progress"),
            "done": done,
            "completion_rate": round((done / total) * 100, 1) if total > 0 else 0,
        }

    def _format_stats(self, stats: dict) -> str:
        return (
            f"Total: {stats['total']} | Todo: {stats['todo']} | "
            f"In Progress: {stats['in_progress']} | Done: {stats['done']} | "
            f"Rate: {stats['completion_rate']}%"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_today":
            self.report_type = "today"
            self._update_report()
        elif event.button.id == "btn_sprint":
            self.report_type = "sprint"
            self._update_report()
        elif event.button.id == "btn_season":
            self.report_type = "season"
            self._update_report()
        elif event.button.id == "close":
            self.app.pop_screen()

    def action_show_today(self):
        self.report_type = "today"
        self._update_report()

    def action_show_sprint(self):
        self.report_type = "sprint"
        self._update_report()

    def action_show_season(self):
        self.report_type = "season"
        self._update_report()

    def action_back(self):
        self.app.pop_screen()
