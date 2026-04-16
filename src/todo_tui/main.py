#!/usr/bin/env python3
"""todo-tui v2: WorkbenchApp - thin orchestration layer.

Imports models, managers, and screens from separate modules.
"""

import json
from pathlib import Path

from textual.app import App

from .managers import SeasonManager, SprintManager, TaskManager
from .screens.workbench import WorkbenchScreen


class WorkbenchApp(App):
    """Main application: Season > Sprint > Task workbench."""

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

    def __init__(self):
        self.save_dir = self._get_save_dir()
        self.season_mgr = SeasonManager(self.save_dir)
        self.sprint_mgr = SprintManager(self.save_dir, self.season_mgr)
        self.task_mgr = TaskManager(self.save_dir)
        super().__init__()

    @staticmethod
    def _get_save_dir() -> Path:
        """Read save path from config."""
        config_path = Path.home() / ".todo-tui" / "config.json"
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                return Path(config.get("save_path", "~/todos")).expanduser()
        default = Path.home() / "todos"
        default.mkdir(parents=True, exist_ok=True)
        return default

    def on_mount(self):
        self.push_screen(WorkbenchScreen(self.season_mgr, self.sprint_mgr, self.task_mgr))


def main():
    """CLI entry point."""
    app = WorkbenchApp()
    app.run()


if __name__ == "__main__":
    main()
