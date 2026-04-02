#!/usr/bin/env python3
"""Todo TUI MCP Server - Claude와 Todo 앱 연동

MCP(Model Context Protocol) 서버를 통해 Claude가 Todo 앱을 직접 제어할 수 있게 합니다.
"""

import sys
import json
import asyncio
from pathlib import Path
from typing import Optional, List, Any

# MCP 라이브러리
try:
    from mcp.server import Server
    from mcp.types import Tool, TextContent
    from mcp.server.stdio import stdio_server
except ImportError:
    print("mcp 라이브러리가 필요합니다.")
    print("설치: pip install mcp")
    sys.exit(1)

# 기존 TodoManager 임포트
sys.path.insert(0, str(Path(__file__).parent))
from todo import TodoManager, SeasonManager, TodoItem, PlanManager, Plan, HistoryManager


class TodoMCPServer:
    """Todo MCP 서버 클래스"""

    def __init__(self):
        self.server = Server("todo-tui")
        self.manager = TodoManager()
        season_manager = SeasonManager(Path(__file__).parent / "config.json")
        self.manager.set_season_manager(season_manager)
        self.plan_manager = PlanManager(self.manager.todo_file)
        self.history_manager = HistoryManager(self.manager.todo_file)
        self._setup_handlers()

    def _setup_handlers(self):
        """MCP 핸들러 설정"""

        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            return [
                Tool(
                    name="todo_add",
                    description="새 Todo 항목 추가. Epic > Story > Task 계층 구조 지원.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "content": {
                                "type": "string",
                                "description": "항목 내용 (필수)"
                            },
                            "type": {
                                "type": "string",
                                "enum": ["epic", "story", "task"],
                                "default": "task",
                                "description": "항목 유형 (epic: 최상위, story: epic 하위, task: story/epic 하위)"
                            },
                            "parent_id": {
                                "type": "integer",
                                "description": "부모 항목 ID (story는 epic ID, task는 story 또는 epic ID)"
                            },
                            "priority": {
                                "type": "string",
                                "enum": ["high", "medium", "low"],
                                "default": "medium",
                                "description": "우선순위"
                            },
                            "description": {
                                "type": "string",
                                "description": "상세 설명"
                            },
                            "due_date": {
                                "type": "string",
                                "description": "마감일 (YYYY-MM-DD 형식)"
                            },
                            "plan_id": {
                                "type": "integer",
                                "description": "연결할 Plan ID (선택사항)"
                            }
                        },
                        "required": ["content"]
                    }
                ),
                Tool(
                    name="todo_done",
                    description="Todo 항목을 완료 상태로 변경",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "todo_id": {
                                "type": "integer",
                                "description": "완료 처리할 항목 ID"
                            }
                        },
                        "required": ["todo_id"]
                    }
                ),
                Tool(
                    name="todo_start",
                    description="Todo 항목을 진행중(in_progress) 상태로 변경",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "todo_id": {
                                "type": "integer",
                                "description": "진행중으로 변경할 항목 ID"
                            }
                        },
                        "required": ["todo_id"]
                    }
                ),
                Tool(
                    name="todo_list",
                    description="Todo 항목 목록 조회. 시즌별 필터링 가능.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "season_id": {
                                "type": "integer",
                                "description": "시즌 ID (선택사항, 없으면 전체 목록)"
                            },
                            "status": {
                                "type": "string",
                                "enum": ["todo", "in_progress", "done"],
                                "description": "상태 필터 (선택사항)"
                            },
                            "type": {
                                "type": "string",
                                "enum": ["epic", "story", "task"],
                                "description": "유형 필터 (선택사항)"
                            }
                        }
                    }
                ),
                Tool(
                    name="todo_get",
                    description="특정 Todo 항목 상세 조회",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "todo_id": {
                                "type": "integer",
                                "description": "조회할 항목 ID"
                            }
                        },
                        "required": ["todo_id"]
                    }
                ),
                Tool(
                    name="todo_delete",
                    description="Todo 항목 삭제 (하위 항목도 함께 삭제됨)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "todo_id": {
                                "type": "integer",
                                "description": "삭제할 항목 ID"
                            }
                        },
                        "required": ["todo_id"]
                    }
                ),
                Tool(
                    name="todo_update_description",
                    description="Todo 항목의 설명 수정",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "todo_id": {
                                "type": "integer",
                                "description": "수정할 항목 ID"
                            },
                            "description": {
                                "type": "string",
                                "description": "새 설명 내용"
                            }
                        },
                        "required": ["todo_id", "description"]
                    }
                ),
                Tool(
                    name="todo_stats",
                    description="Todo 통계 조회 (전체/완료/진행중/대기 개수)",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="todo_set_status",
                    description="Todo 항목의 상태를 직접 설정",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "todo_id": {
                                "type": "integer",
                                "description": "상태를 변경할 항목 ID"
                            },
                            "status": {
                                "type": "string",
                                "enum": ["todo", "in_progress", "done"],
                                "description": "설정할 상태"
                            }
                        },
                        "required": ["todo_id", "status"]
                    }
                ),
                Tool(
                    name="season_list",
                    description="시즌 목록 조회",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="season_current",
                    description="현재 시즌 정보 조회",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="plan_create",
                    description="새 Plan 생성. Claude Code 작업 단위를 관리.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Plan 이름 (필수)"
                            },
                            "working_dir": {
                                "type": "string",
                                "description": "작업 디렉토리 경로"
                            },
                            "model": {
                                "type": "string",
                                "description": "사용 모델명"
                            },
                            "prompt": {
                                "type": "string",
                                "description": "Plan 목적/프롬프트"
                            }
                        },
                        "required": ["name"]
                    }
                ),
                Tool(
                    name="plan_end",
                    description="Plan을 완료 상태로 종료",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "plan_id": {
                                "type": "integer",
                                "description": "종료할 Plan ID"
                            }
                        },
                        "required": ["plan_id"]
                    }
                ),
                Tool(
                    name="plan_list",
                    description="Plan 목록 조회",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "status": {
                                "type": "string",
                                "enum": ["active", "completed", "cancelled"],
                                "description": "상태 필터 (선택사항)"
                            }
                        }
                    }
                ),
                Tool(
                    name="plan_get",
                    description="특정 Plan 상세 조회 (연관된 Todo 통계 포함)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "plan_id": {
                                "type": "integer",
                                "description": "조회할 Plan ID"
                            }
                        },
                        "required": ["plan_id"]
                    }
                ),
                Tool(
                    name="plan_update",
                    description="Plan 정보 수정",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "plan_id": {
                                "type": "integer",
                                "description": "수정할 Plan ID"
                            },
                            "name": {
                                "type": "string",
                                "description": "새 Plan 이름"
                            },
                            "status": {
                                "type": "string",
                                "enum": ["active", "completed", "cancelled"],
                                "description": "새 상태"
                            },
                            "working_dir": {
                                "type": "string",
                                "description": "작업 디렉토리"
                            },
                            "model": {
                                "type": "string",
                                "description": "모델명"
                            }
                        },
                        "required": ["plan_id"]
                    }
                ),
                Tool(
                    name="plan_delete",
                    description="Plan 삭제",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "plan_id": {
                                "type": "integer",
                                "description": "삭제할 Plan ID"
                            }
                        },
                        "required": ["plan_id"]
                    }
                ),
                Tool(
                    name="plan_log",
                    description="Plan에 작업 로그/히스토리 기록. 중요한 결정, 진행 상황, 이슈 등을 기록.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "plan_id": {
                                "type": "integer",
                                "description": "Plan ID"
                            },
                            "content": {
                                "type": "string",
                                "description": "로그 내용 (필수)"
                            },
                            "entry_type": {
                                "type": "string",
                                "enum": ["progress", "issue", "decision", "summary", "note"],
                                "default": "progress",
                                "description": "로그 타입: progress(진행상황), issue(이슈), decision(결정), summary(요약), note(메모)"
                            },
                            "role": {
                                "type": "string",
                                "enum": ["user", "assistant", "system"],
                                "default": "assistant",
                                "description": "발화자"
                            }
                        },
                        "required": ["plan_id", "content"]
                    }
                ),
                Tool(
                    name="plan_logs",
                    description="Plan의 작업 로그/히스토리 목록 조회",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "plan_id": {
                                "type": "integer",
                                "description": "Plan ID"
                            }
                        },
                        "required": ["plan_id"]
                    }
                )
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> List[TextContent]:
            try:
                if name == "todo_add":
                    return await self._todo_add(arguments)
                elif name == "todo_done":
                    return await self._todo_done(arguments)
                elif name == "todo_start":
                    return await self._todo_start(arguments)
                elif name == "todo_list":
                    return await self._todo_list(arguments)
                elif name == "todo_get":
                    return await self._todo_get(arguments)
                elif name == "todo_delete":
                    return await self._todo_delete(arguments)
                elif name == "todo_update_description":
                    return await self._todo_update_description(arguments)
                elif name == "todo_stats":
                    return await self._todo_stats(arguments)
                elif name == "todo_set_status":
                    return await self._todo_set_status(arguments)
                elif name == "season_list":
                    return await self._season_list(arguments)
                elif name == "season_current":
                    return await self._season_current(arguments)
                elif name == "plan_create":
                    return await self._plan_create(arguments)
                elif name == "plan_end":
                    return await self._plan_end(arguments)
                elif name == "plan_list":
                    return await self._plan_list(arguments)
                elif name == "plan_get":
                    return await self._plan_get(arguments)
                elif name == "plan_update":
                    return await self._plan_update(arguments)
                elif name == "plan_delete":
                    return await self._plan_delete(arguments)
                elif name == "plan_log":
                    return await self._plan_log(arguments)
                elif name == "plan_logs":
                    return await self._plan_logs(arguments)
                else:
                    return [TextContent(type="text", text=f"알 수 없는 도구: {name}")]
            except Exception as e:
                return [TextContent(type="text", text=f"오류 발생: {str(e)}")]

    async def _todo_add(self, args: dict) -> List[TextContent]:
        """새 Todo 항목 추가"""
        content = args.get("content")
        if not content:
            return [TextContent(type="text", text="오류: content는 필수 항목입니다.")]

        todo = self.manager.add_todo(
            content=content,
            type=args.get("type", "task"),
            priority=args.get("priority", "medium"),
            parent_id=args.get("parent_id"),
            description=args.get("description"),
            due_date=args.get("due_date")
        )

        # plan_id 설정
        plan_id = args.get("plan_id")
        if plan_id:
            todo.plan_id = plan_id
            self.manager._save_todos()

        result = {
            "id": todo.id,
            "content": todo.content,
            "type": todo.type,
            "status": todo.status,
            "priority": todo.priority,
            "parent_id": todo.parent_id
        }

        return [TextContent(
            type="text",
            text=f"Created {todo.type} id={todo.id}: {todo.content}\n{json.dumps(result, ensure_ascii=False, indent=2)}"
        )]

    async def _todo_done(self, args: dict) -> List[TextContent]:
        """Todo 항목 완료 처리"""
        todo_id = args.get("todo_id")
        if not todo_id:
            return [TextContent(type="text", text="오류: todo_id는 필수 항목입니다.")]

        todo = self.manager.get_todo_by_id(todo_id)
        if not todo:
            return [TextContent(type="text", text=f"오류: ID {todo_id}인 항목을 찾을 수 없습니다.")]

        # 상태를 done으로 변경
        todo.status = "done"
        from datetime import datetime
        todo.completed_at = datetime.now().strftime("%Y-%m-%d")
        self.manager._save_todos()

        return [TextContent(
            type="text",
            text=f"Completed: [{todo.id}] {todo.content}"
        )]

    async def _todo_start(self, args: dict) -> List[TextContent]:
        """Todo 항목 진행중으로 변경"""
        todo_id = args.get("todo_id")
        if not todo_id:
            return [TextContent(type="text", text="오류: todo_id는 필수 항목입니다.")]

        todo = self.manager.get_todo_by_id(todo_id)
        if not todo:
            return [TextContent(type="text", text=f"오류: ID {todo_id}인 항목을 찾을 수 없습니다.")]

        # 상태를 in_progress로 변경
        todo.status = "in_progress"
        self.manager._save_todos()

        return [TextContent(
            type="text",
            text=f"Started: [{todo.id}] {todo.content}"
        )]

    async def _todo_list(self, args: dict) -> List[TextContent]:
        """Todo 목록 조회"""
        season_id = args.get("season_id")
        status_filter = args.get("status")
        type_filter = args.get("type")

        # 시즌 필터링
        if season_id:
            todos = self.manager.get_todos_by_season(season_id)
        elif self.manager.season_manager and self.manager.season_manager.current_season_id:
            todos = self.manager.get_todos_by_season(self.manager.season_manager.current_season_id)
        else:
            todos = self.manager.todos

        # 추가 필터링
        if status_filter:
            todos = [t for t in todos if t.status == status_filter]
        if type_filter:
            todos = [t for t in todos if t.type == type_filter]

        if not todos:
            return [TextContent(type="text", text="표시할 항목이 없습니다.")]

        # 트리 구조로 표시
        result_lines = ["📋 Todo 목록:", ""]

        def format_todo(todo: TodoItem, indent: int = 0) -> List[str]:
            status_icons = {"todo": "⬜", "in_progress": "🔄", "done": "✅"}
            type_icons = {"epic": "📁", "story": "📖", "task": "📌"}
            priority_icons = {"high": "🔴", "medium": "🟡", "low": "🟢"}

            icon = status_icons.get(todo.status, "⬜")
            type_icon = type_icons.get(todo.type, "📌")
            priority_icon = priority_icons.get(todo.priority, "🟡")

            prefix = "  " * indent
            line = f"{prefix}{icon} {type_icon} {priority_icon} [{todo.id}] {todo.content}"

            if todo.description:
                line += " 📝"
            if todo.due_date:
                line += f" (due: {todo.due_date})"

            lines = [line]

            # 하위 항목
            children = [t for t in self.manager.todos if t.parent_id == todo.id]
            children_sorted = sorted(children, key=lambda t: t.order)
            for child in children_sorted:
                lines.extend(format_todo(child, indent + 1))

            return lines

        # 최상위 항목만 표시
        root_todos = [t for t in todos if t.parent_id is None]
        root_todos_sorted = sorted(root_todos, key=lambda t: (
            {"epic": 0, "story": 1, "task": 2}.get(t.type, 99),
            t.order
        ))

        for todo in root_todos_sorted:
            result_lines.extend(format_todo(todo))

        # 통계 추가
        stats = self.manager.get_stats()
        result_lines.append("")
        result_lines.append(f"📊 전체: {stats['total']} | 대기: {stats['todo']} | 진행중: {stats['in_progress']} | 완료: {stats['done']}")

        return [TextContent(type="text", text="\n".join(result_lines))]

    async def _todo_get(self, args: dict) -> List[TextContent]:
        """특정 Todo 항목 조회"""
        todo_id = args.get("todo_id")
        if not todo_id:
            return [TextContent(type="text", text="오류: todo_id는 필수 항목입니다.")]

        todo = self.manager.get_todo_by_id(todo_id)
        if not todo:
            return [TextContent(type="text", text=f"오류: ID {todo_id}인 항목을 찾을 수 없습니다.")]

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
            "jira_key": todo.jira_key
        }

        # 하위 항목 정보
        children = [t for t in self.manager.todos if t.parent_id == todo.id]
        if children:
            result["children"] = [
                {"id": c.id, "content": c.content, "status": c.status, "type": c.type}
                for c in sorted(children, key=lambda t: t.order)
            ]

        return [TextContent(
            type="text",
            text=f"📝 Todo 상세 정보:\n{json.dumps(result, ensure_ascii=False, indent=2)}"
        )]

    async def _todo_delete(self, args: dict) -> List[TextContent]:
        """Todo 항목 삭제"""
        todo_id = args.get("todo_id")
        if not todo_id:
            return [TextContent(type="text", text="오류: todo_id는 필수 항목입니다.")]

        todo = self.manager.get_todo_by_id(todo_id)
        if not todo:
            return [TextContent(type="text", text=f"오류: ID {todo_id}인 항목을 찾을 수 없습니다.")]

        content = todo.content
        self.manager.delete_todo(todo_id)

        return [TextContent(
            type="text",
            text=f"Deleted: [{todo_id}] {content}"
        )]

    async def _todo_update_description(self, args: dict) -> List[TextContent]:
        """Todo 설명 수정"""
        todo_id = args.get("todo_id")
        description = args.get("description")

        if not todo_id:
            return [TextContent(type="text", text="오류: todo_id는 필수 항목입니다.")]

        todo = self.manager.get_todo_by_id(todo_id)
        if not todo:
            return [TextContent(type="text", text=f"오류: ID {todo_id}인 항목을 찾을 수 없습니다.")]

        self.manager.update_description(todo_id, description)

        return [TextContent(
            type="text",
            text=f"Updated description for [{todo_id}] {todo.content}"
        )]

    async def _todo_stats(self, args: dict) -> List[TextContent]:
        """Todo 통계 조회"""
        stats = self.manager.get_stats()

        result = {
            "total": stats["total"],
            "todo": stats["todo"],
            "in_progress": stats["in_progress"],
            "done": stats["done"],
            "epics": stats["epics"],
            "stories": stats["stories"],
            "tasks": stats["tasks"],
            "completion_rate": round((stats["done"] / stats["total"]) * 100, 1) if stats["total"] > 0 else 0
        }

        lines = [
            "📊 Todo 통계",
            "",
            f"전체: {result['total']}",
            f"대기: {result['todo']}",
            f"진행중: {result['in_progress']}",
            f"완료: {result['done']}",
            f"완료율: {result['completion_rate']}%",
            "",
            f"Epic: {result['epics']}",
            f"Story: {result['stories']}",
            f"Task: {result['tasks']}"
        ]

        return [TextContent(type="text", text="\n".join(lines))]

    async def _todo_set_status(self, args: dict) -> List[TextContent]:
        """Todo 상태 직접 설정"""
        todo_id = args.get("todo_id")
        status = args.get("status")

        if not todo_id:
            return [TextContent(type="text", text="오류: todo_id는 필수 항목입니다.")]
        if not status:
            return [TextContent(type="text", text="오류: status는 필수 항목입니다.")]

        todo = self.manager.get_todo_by_id(todo_id)
        if not todo:
            return [TextContent(type="text", text=f"오류: ID {todo_id}인 항목을 찾을 수 없습니다.")]

        old_status = todo.status
        todo.status = status

        from datetime import datetime
        if status == "done":
            todo.completed_at = datetime.now().strftime("%Y-%m-%d")
        elif status == "todo" and old_status == "done":
            todo.completed_at = None

        self.manager._save_todos()

        return [TextContent(
            type="text",
            text=f"Status changed: [{todo_id}] {todo.content} ({old_status} -> {status})"
        )]

    async def _season_list(self, args: dict) -> List[TextContent]:
        """시즌 목록 조회"""
        if not self.manager.season_manager:
            return [TextContent(type="text", text="시즌 관리자가 설정되지 않았습니다.")]

        seasons = self.manager.season_manager.get_all_seasons()
        if not seasons:
            return [TextContent(type="text", text="등록된 시즌이 없습니다.")]

        lines = ["📅 시즌 목록:", ""]
        current_id = self.manager.season_manager.current_season_id

        for season in seasons:
            current_mark = "✓ " if season.id == current_id else "  "
            progress = season.get_progress()
            lines.append(f"{current_mark}[{season.id}] {season.name} ({season.start_date} ~ {season.end_date}) [{progress}%] - {season.status}")

        return [TextContent(type="text", text="\n".join(lines))]

    async def _season_current(self, args: dict) -> List[TextContent]:
        """현재 시즌 정보 조회"""
        if not self.manager.season_manager:
            return [TextContent(type="text", text="시즌 관리자가 설정되지 않았습니다.")]

        season = self.manager.season_manager.get_current_season()
        if not season:
            return [TextContent(type="text", text="현재 설정된 시즌이 없습니다.")]

        # 현재 시즌의 통계
        todos = self.manager.get_todos_by_season(season.id)
        stats = {
            "total": len(todos),
            "todo": sum(1 for t in todos if t.status == "todo"),
            "in_progress": sum(1 for t in todos if t.status == "in_progress"),
            "done": sum(1 for t in todos if t.status == "done")
        }

        result = {
            "id": season.id,
            "name": season.name,
            "start_date": season.start_date,
            "end_date": season.end_date,
            "status": season.status,
            "progress": season.get_progress(),
            "stats": stats
        }

        return [TextContent(
            type="text",
            text=f"📅 현재 시즌:\n{json.dumps(result, ensure_ascii=False, indent=2)}"
        )]

    async def _plan_create(self, args: dict) -> List[TextContent]:
        """새 Plan 생성"""
        name = args.get("name")
        if not name:
            return [TextContent(type="text", text="오류: name은 필수 항목입니다.")]

        plan = self.plan_manager.create_plan(
            name=name,
            working_dir=args.get("working_dir"),
            model=args.get("model"),
            prompt=args.get("prompt")
        )

        result = plan.to_dict()
        return [TextContent(
            type="text",
            text=f"Created plan id={plan.id}: {plan.name}\n{json.dumps(result, ensure_ascii=False, indent=2)}"
        )]

    async def _plan_end(self, args: dict) -> List[TextContent]:
        """Plan 종료"""
        plan_id = args.get("plan_id")
        if not plan_id:
            return [TextContent(type="text", text="오류: plan_id는 필수 항목입니다.")]

        plan = self.plan_manager.end_plan(plan_id)
        if not plan:
            return [TextContent(type="text", text=f"오류: ID {plan_id}인 Plan을 찾을 수 없습니다.")]

        return [TextContent(
            type="text",
            text=f"Completed plan [{plan.id}] {plan.name}"
        )]

    async def _plan_list(self, args: dict) -> List[TextContent]:
        """Plan 목록 조회"""
        status_filter = args.get("status")
        plans = self.plan_manager.list_plans(status_filter)

        if not plans:
            return [TextContent(type="text", text="표시할 Plan이 없습니다.")]

        lines = ["📋 Plan 목록:", ""]
        for plan in plans:
            stats = self.plan_manager.get_plan_stats(plan.id, self.manager.todos)
            status_icon = {"active": "🔄", "completed": "✅", "cancelled": "❌"}.get(plan.status, "⬜")
            lines.append(f"  {status_icon} [{plan.id}] {plan.name} ({plan.status}) - {stats['completion_rate']}% ({stats['done']}/{stats['total']})")
            if plan.working_dir:
                lines.append(f"     dir: {plan.working_dir}")
            if plan.model:
                lines.append(f"     model: {plan.model}")
            lines.append(f"     started: {plan.started_at}")

        return [TextContent(type="text", text="\n".join(lines))]

    async def _plan_get(self, args: dict) -> List[TextContent]:
        """Plan 상세 조회"""
        plan_id = args.get("plan_id")
        if not plan_id:
            return [TextContent(type="text", text="오류: plan_id는 필수 항목입니다.")]

        plan = self.plan_manager.get_plan(plan_id)
        if not plan:
            return [TextContent(type="text", text=f"오류: ID {plan_id}인 Plan을 찾을 수 없습니다.")]

        stats = self.plan_manager.get_plan_stats(plan.id, self.manager.todos)
        plan_todos = self.manager.get_todos_by_plan(plan_id)

        result = plan.to_dict()
        result["stats"] = stats
        result["todos"] = [
            {"id": t.id, "content": t.content, "status": t.status, "type": t.type}
            for t in plan_todos
        ]

        return [TextContent(
            type="text",
            text=f"📋 Plan 상세:\n{json.dumps(result, ensure_ascii=False, indent=2)}"
        )]

    async def _plan_update(self, args: dict) -> List[TextContent]:
        """Plan 수정"""
        plan_id = args.get("plan_id")
        if not plan_id:
            return [TextContent(type="text", text="오류: plan_id는 필수 항목입니다.")]

        updates = {k: v for k, v in args.items() if k != "plan_id" and v is not None}
        plan = self.plan_manager.update_plan(plan_id, **updates)
        if not plan:
            return [TextContent(type="text", text=f"오류: ID {plan_id}인 Plan을 찾을 수 없습니다.")]

        return [TextContent(
            type="text",
            text=f"Updated plan [{plan.id}] {plan.name}\n{json.dumps(plan.to_dict(), ensure_ascii=False, indent=2)}"
        )]

    async def _plan_delete(self, args: dict) -> List[TextContent]:
        """Plan 삭제"""
        plan_id = args.get("plan_id")
        if not plan_id:
            return [TextContent(type="text", text="오류: plan_id는 필수 항목입니다.")]

        plan = self.plan_manager.get_plan(plan_id)
        if not plan:
            return [TextContent(type="text", text=f"오류: ID {plan_id}인 Plan을 찾을 수 없습니다.")]

        self.plan_manager.delete_plan(plan_id)
        return [TextContent(
            type="text",
            text=f"Deleted plan [{plan_id}] {plan.name}"
        )]

    async def _plan_log(self, args: dict) -> List[TextContent]:
        """Plan에 작업 로그 기록"""
        plan_id = args.get("plan_id")
        content = args.get("content")
        if not plan_id or not content:
            return [TextContent(type="text", text="오류: plan_id와 content는 필수 항목입니다.")]

        plan = self.plan_manager.get_plan(plan_id)
        if not plan:
            return [TextContent(type="text", text=f"오류: ID {plan_id}인 Plan을 찾을 수 없습니다.")]

        entry = self.history_manager.add_entry(
            plan_id=plan_id,
            content=content,
            role=args.get("role", "assistant"),
            entry_type=args.get("entry_type", "progress"),
        )

        return [TextContent(
            type="text",
            text=f"Logged [{entry.entry_type}] to plan {plan_id}: {content[:80]}"
        )]

    async def _plan_logs(self, args: dict) -> List[TextContent]:
        """Plan 작업 로그 조회"""
        plan_id = args.get("plan_id")
        if not plan_id:
            return [TextContent(type="text", text="오류: plan_id는 필수 항목입니다.")]

        entries = self.history_manager.get_entries(plan_id)
        if not entries:
            return [TextContent(type="text", text=f"Plan {plan_id}에 기록된 로그가 없습니다.")]

        type_icons = {"progress": "📊", "issue": "⚠️", "decision": "✅", "summary": "📝", "note": "📌"}
        lines = [f"📜 Plan {plan_id} 작업 로그 ({len(entries)}건):", ""]
        for e in entries:
            icon = type_icons.get(e.entry_type, "📌")
            lines.append(f"  {icon} [{e.role}] {e.content}")
            if e.created_at:
                lines.append(f"     {e.created_at}")

        return [TextContent(type="text", text="\n".join(lines))]

    async def run(self):
        """서버 실행"""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


def main():
    """메인 함수"""
    server = TodoMCPServer()
    asyncio.run(server.run())


if __name__ == "__main__":
    main()
