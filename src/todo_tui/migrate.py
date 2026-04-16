"""Migration script: v1 (todos.json) -> v2 (sprints.json + tasks.json).

Usage: python -m todo_tui.migrate
"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional


def _get_save_dir() -> Path:
    """Read save_dir from config."""
    config_path = Path.home() / ".todo-tui" / "config.json"
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
            return Path(config.get("save_path", "~/todos")).expanduser()
    return Path.home() / "todos"


def migrate(dry_run: bool = False) -> dict:
    """Migrate v1 data to v2 format.

    Returns a summary dict with counts.
    """
    save_dir = _get_save_dir()
    todos_file = save_dir / "todos.json"
    seasons_dir = save_dir / "seasons"

    if not todos_file.exists():
        return {"error": f"No todos.json found at {todos_file}"}

    # Load v1 data
    with open(todos_file, "r", encoding="utf-8") as f:
        v1_items = json.load(f)

    # Load existing seasons
    seasons_file = seasons_dir / "seasons.json"
    seasons = []
    if seasons_file.exists():
        with open(seasons_file, "r", encoding="utf-8") as f:
            seasons = json.load(f)

    # Build v2 data
    sprints = []
    tasks = []
    sprint_count = 0
    task_count = 0
    unmapped = 0

    # Map v1 epics to sprints
    epic_to_sprint = {}
    for item in v1_items:
        item_type = item.get("type", "task")
        if item_type == "epic":
            # Epic -> Sprint
            sprint_count += 1
            season_id = item.get("season_id")

            # Use epic dates or default to its creation date's week
            created = item.get("created_at", "")
            if created:
                created_dt = datetime.strptime(created.split(" ")[0], "%Y-%m-%d")
                from datetime import timedelta
                start = (created_dt - timedelta(days=created_dt.weekday()))
                end = start + timedelta(days=6)
                start_str = start.strftime("%Y-%m-%d")
                end_str = end.strftime("%Y-%m-%d")
            else:
                today = datetime.now()
                start_str = today.strftime("%Y-%m-%d")
                end_str = start_str

            sprint = {
                "id": sprint_count,
                "season_id": season_id,
                "name": item.get("content", f"Sprint {sprint_count}"),
                "start_date": start_str,
                "end_date": end_str,
                "status": "completed" if item.get("status") == "done" else "active",
                "goal": item.get("description", ""),
                "created_at": item.get("created_at", ""),
            }
            sprints.append(sprint)
            epic_to_sprint[item["id"]] = sprint_count

    # Map v1 tasks (type=task or type=story) to v2 tasks
    for item in v1_items:
        item_type = item.get("type", "task")
        if item_type in ("task", "story"):
            task_count += 1
            parent_id = item.get("parent_id")
            sprint_id = epic_to_sprint.get(parent_id) if parent_id else None
            season_id = item.get("season_id")

            if not sprint_id and not season_id:
                unmapped += 1

            task = {
                "id": task_count,
                "content": item.get("content", ""),
                "sprint_id": sprint_id,
                "season_id": season_id,
                "status": item.get("status", "todo"),
                "priority": item.get("priority", "medium"),
                "memo": item.get("description", ""),
                "due_date": item.get("due_date"),
                "created_at": item.get("created_at", ""),
                "completed_at": item.get("completed_at"),
                "order": item.get("order", task_count),
            }
            tasks.append(task)

    summary = {
        "v1_items": len(v1_items),
        "sprints_created": sprint_count,
        "tasks_created": task_count,
        "unmapped_tasks": unmapped,
        "seasons_preserved": len(seasons),
    }

    if dry_run:
        summary["dry_run"] = True
        return summary

    # Backup original files
    backup_dir = save_dir / "backup"
    backup_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if todos_file.exists():
        shutil.copy2(todos_file, backup_dir / f"todos_{timestamp}.json")
    if seasons_file.exists():
        shutil.copy2(seasons_file, backup_dir / f"seasons_{timestamp}.json")

    # Write v2 data
    with open(save_dir / "sprints.json", "w", encoding="utf-8") as f:
        json.dump(sprints, f, indent=2, ensure_ascii=False)

    with open(save_dir / "tasks.json", "w", encoding="utf-8") as f:
        json.dump(tasks, f, indent=2, ensure_ascii=False)

    summary["backup_dir"] = str(backup_dir)
    return summary


def main():
    """CLI entry point."""
    print("todo-tui v1 -> v2 Migration")
    print("=" * 40)

    # Dry run first
    print("\n[Dry Run]")
    result = migrate(dry_run=True)
    for key, value in result.items():
        print(f"  {key}: {value}")

    # Confirm
    answer = input("\nProceed with migration? (y/N): ").strip().lower()
    if answer == "y":
        result = migrate(dry_run=False)
        print("\n[Migration Complete]")
        for key, value in result.items():
            print(f"  {key}: {value}")
        print("\nBackup saved to:", result.get("backup_dir", "N/A"))
    else:
        print("Migration cancelled.")


if __name__ == "__main__":
    main()
