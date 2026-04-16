#!/usr/bin/env python3
"""Todo TUI MCP Server - Claude와 Todo 앱 연동

MCP(Model Context Protocol) 서버를 통해 Claude가 Todo 앱을 직접 제어할 수 있게 합니다.
"""

import sys
import json
from pathlib import Path
from typing import Optional

# MCP 라이브러리
try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print("mcp 라이브러리가 필요합니다.")
    print("설치: pip install mcp")
    sys.exit(1)

# 기존 TodoManager 임포트
sys.path.insert(0, str(Path(__file__).parent))
from todo import TodoManager, SeasonManager, TodoItem, PlanManager, Plan, HistoryManager


# FastMCP 서버 인스턴스
mcp = FastMCP("todo-tui")

# 매니저 인스턴스 (모듈 레벨에서 초기화)
_manager = TodoManager()
_season_manager = SeasonManager(Path(__file__).parent / "config.json")
_manager.set_season_manager(_season_manager)
_plan_manager = PlanManager(_manager.todo_file)
_history_manager = HistoryManager(_manager.todo_file)


# ─── Todo 도구 ────────────────────────────────────────────────

@mcp.tool()
def todo_add(
    content: str,
    type: str = "task",
    parent_id: Optional[int] = None,
    priority: str = "medium",
    description: Optional[str] = None,
    due_date: Optional[str] = None,
    plan_id: Optional[int] = None,
) -> str:
    """새 Todo 항목 추가. Epic > Story > Task 계층 구조 지원.

    Args:
        content: 항목 내용 (필수)
        type: 항목 유형 - epic(최상위), story(epic 하위), task(story/epic 하위)
        parent_id: 부모 항목 ID (story는 epic ID, task는 story 또는 epic ID)
        priority: 우선순위 (high, medium, low)
        description: 상세 설명
        due_date: 마감일 (YYYY-MM-DD 형식)
        plan_id: 연결할 Plan ID (선택사항)
    """
    if not content:
        return "오류: content는 필수 항목입니다."

    todo = _manager.add_todo(
        content=content,
        type=type,
        priority=priority,
        parent_id=parent_id,
        description=description,
        due_date=due_date,
    )

    # plan_id 설정
    if plan_id:
        todo.plan_id = plan_id
        _manager._save_todos()

    result = {
        "id": todo.id,
        "content": todo.content,
        "type": todo.type,
        "status": todo.status,
        "priority": todo.priority,
        "parent_id": todo.parent_id,
    }

    return f"Created {todo.type} id={todo.id}: {todo.content}\n{json.dumps(result, ensure_ascii=False, indent=2)}"


@mcp.tool()
def todo_done(todo_id: int) -> str:
    """Todo 항목을 완료 상태로 변경.

    Args:
        todo_id: 완료 처리할 항목 ID
    """
    if not todo_id:
        return "오류: todo_id는 필수 항목입니다."

    todo = _manager.get_todo_by_id(todo_id)
    if not todo:
        return f"오류: ID {todo_id}인 항목을 찾을 수 없습니다."

    todo.status = "done"
    from datetime import datetime
    todo.completed_at = datetime.now().strftime("%Y-%m-%d")
    _manager._save_todos()

    return f"Completed: [{todo.id}] {todo.content}"


@mcp.tool()
def todo_start(todo_id: int) -> str:
    """Todo 항목을 진행중(in_progress) 상태로 변경.

    Args:
        todo_id: 진행중으로 변경할 항목 ID
    """
    if not todo_id:
        return "오류: todo_id는 필수 항목입니다."

    todo = _manager.get_todo_by_id(todo_id)
    if not todo:
        return f"오류: ID {todo_id}인 항목을 찾을 수 없습니다."

    todo.status = "in_progress"
    _manager._save_todos()

    return f"Started: [{todo.id}] {todo.content}"


@mcp.tool()
def todo_list(
    season_id: Optional[int] = None,
    status: Optional[str] = None,
    type: Optional[str] = None,
) -> str:
    """Todo 항목 목록 조회. 시즌별 필터링 가능.

    Args:
        season_id: 시즌 ID (선택사항, 없으면 전체 목록)
        status: 상태 필터 - todo, in_progress, done (선택사항)
        type: 유형 필터 - epic, story, task (선택사항)
    """
    # 시즌 필터링
    if season_id:
        todos = _manager.get_todos_by_season(season_id)
    elif _manager.season_manager and _manager.season_manager.current_season_id:
        todos = _manager.get_todos_by_season(_manager.season_manager.current_season_id)
    else:
        todos = _manager.todos

    # 추가 필터링
    if status:
        todos = [t for t in todos if t.status == status]
    if type:
        todos = [t for t in todos if t.type == type]

    if not todos:
        return "표시할 항목이 없습니다."

    # 트리 구조로 표시
    result_lines = ["Todo 목록:", ""]

    def format_todo(todo: TodoItem, indent: int = 0) -> list:
        status_icons = {"todo": "[ ]", "in_progress": "[~]", "done": "[x]"}
        type_icons = {"epic": "E", "story": "S", "task": "T"}
        priority_icons = {"high": "!", "medium": "-", "low": "."}

        icon = status_icons.get(todo.status, "[ ]")
        type_icon = type_icons.get(todo.type, "T")
        priority_icon = priority_icons.get(todo.priority, "-")

        prefix = "  " * indent
        line = f"{prefix}{icon} {type_icon} {priority_icon} [{todo.id}] {todo.content}"

        if todo.description:
            line += " (desc)"
        if todo.due_date:
            line += f" (due: {todo.due_date})"

        lines = [line]

        # 하위 항목
        children = [t for t in _manager.todos if t.parent_id == todo.id]
        children_sorted = sorted(children, key=lambda t: t.order)
        for child in children_sorted:
            lines.extend(format_todo(child, indent + 1))

        return lines

    # 최상위 항목만 표시
    root_todos = [t for t in todos if t.parent_id is None]
    root_todos_sorted = sorted(
        root_todos,
        key=lambda t: ({"epic": 0, "story": 1, "task": 2}.get(t.type, 99), t.order),
    )

    for todo in root_todos_sorted:
        result_lines.extend(format_todo(todo))

    # 통계 추가
    stats = _manager.get_stats()
    result_lines.append("")
    result_lines.append(
        f"전체: {stats['total']} | 대기: {stats['todo']} | 진행중: {stats['in_progress']} | 완료: {stats['done']}"
    )

    return "\n".join(result_lines)


@mcp.tool()
def todo_get(todo_id: int) -> str:
    """특정 Todo 항목 상세 조회.

    Args:
        todo_id: 조회할 항목 ID
    """
    if not todo_id:
        return "오류: todo_id는 필수 항목입니다."

    todo = _manager.get_todo_by_id(todo_id)
    if not todo:
        return f"오류: ID {todo_id}인 항목을 찾을 수 없습니다."

    result = {
        "id": todo.id,
        "content": todo.content,
        "type": todo.type,
        "status": todo.status,
        "priority": todo.priority,
        "category": todo.category,
        "description": todo.description,
        "due_date": todo.due_date,
        "created_at": todo.created_at,
        "completed_at": todo.completed_at,
        "parent_id": todo.parent_id,
        "season_id": todo.season_id,
        "jira_key": todo.jira_key,
    }

    # 하위 항목 정보
    children = [t for t in _manager.todos if t.parent_id == todo.id]
    if children:
        result["children"] = [
            {"id": c.id, "content": c.content, "status": c.status, "type": c.type}
            for c in sorted(children, key=lambda t: t.order)
        ]

    return f"Todo 상세 정보:\n{json.dumps(result, ensure_ascii=False, indent=2)}"


@mcp.tool()
def todo_delete(todo_id: int) -> str:
    """Todo 항목 삭제 (하위 항목도 함께 삭제됨).

    Args:
        todo_id: 삭제할 항목 ID
    """
    if not todo_id:
        return "오류: todo_id는 필수 항목입니다."

    todo = _manager.get_todo_by_id(todo_id)
    if not todo:
        return f"오류: ID {todo_id}인 항목을 찾을 수 없습니다."

    content = todo.content
    _manager.delete_todo(todo_id)

    return f"Deleted: [{todo_id}] {content}"


@mcp.tool()
def todo_update_description(todo_id: int, description: str) -> str:
    """Todo 항목의 설명 수정.

    Args:
        todo_id: 수정할 항목 ID
        description: 새 설명 내용
    """
    if not todo_id:
        return "오류: todo_id는 필수 항목입니다."

    todo = _manager.get_todo_by_id(todo_id)
    if not todo:
        return f"오류: ID {todo_id}인 항목을 찾을 수 없습니다."

    _manager.update_description(todo_id, description)

    return f"Updated description for [{todo_id}] {todo.content}"


@mcp.tool()
def todo_stats() -> str:
    """Todo 통계 조회 (전체/완료/진행중/대기 개수)."""
    stats = _manager.get_stats()

    result = {
        "total": stats["total"],
        "todo": stats["todo"],
        "in_progress": stats["in_progress"],
        "done": stats["done"],
        "epics": stats["epics"],
        "stories": stats["stories"],
        "tasks": stats["tasks"],
        "completion_rate": round((stats["done"] / stats["total"]) * 100, 1)
        if stats["total"] > 0
        else 0,
    }

    lines = [
        "Todo 통계",
        "",
        f"전체: {result['total']}",
        f"대기: {result['todo']}",
        f"진행중: {result['in_progress']}",
        f"완료: {result['done']}",
        f"완료율: {result['completion_rate']}%",
        "",
        f"Epic: {result['epics']}",
        f"Story: {result['stories']}",
        f"Task: {result['tasks']}",
    ]

    return "\n".join(lines)


@mcp.tool()
def todo_set_status(todo_id: int, status: str) -> str:
    """Todo 항목의 상태를 직접 설정.

    Args:
        todo_id: 상태를 변경할 항목 ID
        status: 설정할 상태 (todo, in_progress, done)
    """
    if not todo_id:
        return "오류: todo_id는 필수 항목입니다."
    if not status:
        return "오류: status는 필수 항목입니다."

    todo = _manager.get_todo_by_id(todo_id)
    if not todo:
        return f"오류: ID {todo_id}인 항목을 찾을 수 없습니다."

    old_status = todo.status
    todo.status = status

    from datetime import datetime

    if status == "done":
        todo.completed_at = datetime.now().strftime("%Y-%m-%d")
    elif status == "todo" and old_status == "done":
        todo.completed_at = None

    _manager._save_todos()

    return f"Status changed: [{todo_id}] {todo.content} ({old_status} -> {status})"


# ─── Season 도구 ──────────────────────────────────────────────

@mcp.tool()
def season_list() -> str:
    """시즌 목록 조회."""
    if not _manager.season_manager:
        return "시즌 관리자가 설정되지 않았습니다."

    seasons = _manager.season_manager.get_all_seasons()
    if not seasons:
        return "등록된 시즌이 없습니다."

    lines = ["시즌 목록:", ""]
    current_id = _manager.season_manager.current_season_id

    for season in seasons:
        current_mark = "* " if season.id == current_id else "  "
        progress = season.get_progress()
        lines.append(
            f"{current_mark}[{season.id}] {season.name} ({season.start_date} ~ {season.end_date}) [{progress}%] - {season.status}"
        )

    return "\n".join(lines)


@mcp.tool()
def season_current() -> str:
    """현재 시즌 정보 조회."""
    if not _manager.season_manager:
        return "시즌 관리자가 설정되지 않았습니다."

    season = _manager.season_manager.get_current_season()
    if not season:
        return "현재 설정된 시즌이 없습니다."

    # 현재 시즌의 통계
    todos = _manager.get_todos_by_season(season.id)
    stats = {
        "total": len(todos),
        "todo": sum(1 for t in todos if t.status == "todo"),
        "in_progress": sum(1 for t in todos if t.status == "in_progress"),
        "done": sum(1 for t in todos if t.status == "done"),
    }

    result = {
        "id": season.id,
        "name": season.name,
        "start_date": season.start_date,
        "end_date": season.end_date,
        "status": season.status,
        "progress": season.get_progress(),
        "stats": stats,
    }

    return f"현재 시즌:\n{json.dumps(result, ensure_ascii=False, indent=2)}"


# ─── Plan 도구 ────────────────────────────────────────────────

@mcp.tool()
def plan_create(
    name: str,
    working_dir: Optional[str] = None,
    model: Optional[str] = None,
    prompt: Optional[str] = None,
) -> str:
    """새 Plan 생성. Claude Code 작업 단위를 관리.

    Args:
        name: Plan 이름 (필수)
        working_dir: 작업 디렉토리 경로
        model: 사용 모델명
        prompt: Plan 목적/프롬프트
    """
    if not name:
        return "오류: name은 필수 항목입니다."

    plan = _plan_manager.create_plan(
        name=name,
        working_dir=working_dir,
        model=model,
        prompt=prompt,
    )

    result = plan.to_dict()
    return f"Created plan id={plan.id}: {plan.name}\n{json.dumps(result, ensure_ascii=False, indent=2)}"


@mcp.tool()
def plan_end(plan_id: int) -> str:
    """Plan을 완료 상태로 종료.

    Args:
        plan_id: 종료할 Plan ID
    """
    if not plan_id:
        return "오류: plan_id는 필수 항목입니다."

    plan = _plan_manager.end_plan(plan_id)
    if not plan:
        return f"오류: ID {plan_id}인 Plan을 찾을 수 없습니다."

    return f"Completed plan [{plan.id}] {plan.name}"


@mcp.tool()
def plan_list(status: Optional[str] = None) -> str:
    """Plan 목록 조회.

    Args:
        status: 상태 필터 - active, completed, cancelled (선택사항)
    """
    plans = _plan_manager.list_plans(status)

    if not plans:
        return "표시할 Plan이 없습니다."

    lines = ["Plan 목록:", ""]
    for plan in plans:
        stats = _plan_manager.get_plan_stats(plan.id, _manager.todos)
        status_icon = (
            {"active": "[~]", "completed": "[x]", "cancelled": "[!]"}
            .get(plan.status, "[ ]")
        )
        lines.append(
            f"  {status_icon} [{plan.id}] {plan.name} ({plan.status}) - {stats['completion_rate']}% ({stats['done']}/{stats['total']})"
        )
        if plan.working_dir:
            lines.append(f"     dir: {plan.working_dir}")
        if plan.model:
            lines.append(f"     model: {plan.model}")
        lines.append(f"     started: {plan.started_at}")

    return "\n".join(lines)


@mcp.tool()
def plan_get(plan_id: int) -> str:
    """특정 Plan 상세 조회 (연관된 Todo 통계 포함).

    Args:
        plan_id: 조회할 Plan ID
    """
    if not plan_id:
        return "오류: plan_id는 필수 항목입니다."

    plan = _plan_manager.get_plan(plan_id)
    if not plan:
        return f"오류: ID {plan_id}인 Plan을 찾을 수 없습니다."

    stats = _plan_manager.get_plan_stats(plan.id, _manager.todos)
    plan_todos = _manager.get_todos_by_plan(plan_id)

    result = plan.to_dict()
    result["stats"] = stats
    result["todos"] = [
        {"id": t.id, "content": t.content, "status": t.status, "type": t.type}
        for t in plan_todos
    ]

    return f"Plan 상세:\n{json.dumps(result, ensure_ascii=False, indent=2)}"


@mcp.tool()
def plan_update(
    plan_id: int,
    name: Optional[str] = None,
    status: Optional[str] = None,
    working_dir: Optional[str] = None,
    model: Optional[str] = None,
) -> str:
    """Plan 정보 수정.

    Args:
        plan_id: 수정할 Plan ID
        name: 새 Plan 이름
        status: 새 상태 (active, completed, cancelled)
        working_dir: 작업 디렉토리
        model: 모델명
    """
    if not plan_id:
        return "오류: plan_id는 필수 항목입니다."

    updates = {k: v for k, v in locals().items() if k != "plan_id" and v is not None}
    plan = _plan_manager.update_plan(plan_id, **updates)
    if not plan:
        return f"오류: ID {plan_id}인 Plan을 찾을 수 없습니다."

    return f"Updated plan [{plan.id}] {plan.name}\n{json.dumps(plan.to_dict(), ensure_ascii=False, indent=2)}"


@mcp.tool()
def plan_delete(plan_id: int) -> str:
    """Plan 삭제.

    Args:
        plan_id: 삭제할 Plan ID
    """
    if not plan_id:
        return "오류: plan_id는 필수 항목입니다."

    plan = _plan_manager.get_plan(plan_id)
    if not plan:
        return f"오류: ID {plan_id}인 Plan을 찾을 수 없습니다."

    _plan_manager.delete_plan(plan_id)
    return f"Deleted plan [{plan_id}] {plan.name}"


@mcp.tool()
def plan_log(
    plan_id: int,
    content: str,
    entry_type: str = "progress",
    role: str = "assistant",
) -> str:
    """Plan에 작업 로그/히스토리 기록. 중요한 결정, 진행 상황, 이슈 등을 기록.

    Args:
        plan_id: Plan ID
        content: 로그 내용 (필수)
        entry_type: 로그 타입 - progress(진행상황), issue(이슈), decision(결정), summary(요약), note(메모)
        role: 발화자 (user, assistant, system)
    """
    if not plan_id or not content:
        return "오류: plan_id와 content는 필수 항목입니다."

    plan = _plan_manager.get_plan(plan_id)
    if not plan:
        return f"오류: ID {plan_id}인 Plan을 찾을 수 없습니다."

    entry = _history_manager.add_entry(
        plan_id=plan_id,
        content=content,
        role=role,
        entry_type=entry_type,
    )

    return f"Logged [{entry.entry_type}] to plan {plan_id}: {content[:80]}"


@mcp.tool()
def plan_logs(plan_id: int) -> str:
    """Plan의 작업 로그/히스토리 목록 조회.

    Args:
        plan_id: Plan ID
    """
    if not plan_id:
        return "오류: plan_id는 필수 항목입니다."

    entries = _history_manager.get_entries(plan_id)
    if not entries:
        return f"Plan {plan_id}에 기록된 로그가 없습니다."

    type_labels = {
        "progress": "[progress]",
        "issue": "[issue]",
        "decision": "[decision]",
        "summary": "[summary]",
        "note": "[note]",
    }
    lines = [f"Plan {plan_id} 작업 로그 ({len(entries)}건):", ""]
    for e in entries:
        label = type_labels.get(e.entry_type, "[note]")
        lines.append(f"  {label} [{e.role}] {e.content}")
        if e.created_at:
            lines.append(f"     {e.created_at}")

    return "\n".join(lines)


# ─── 메인 ─────────────────────────────────────────────────────

def main():
    """메인 함수"""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
