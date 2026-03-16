#!/Users/sun/Document/01_project/todo-cli/.venv/bin/python3
"""MCP 서버 테스트 스크립트"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from todo_mcp_server import TodoMCPServer


async def test_mcp_server():
    """MCP 서버 기능 테스트"""
    server = TodoMCPServer()

    print("=" * 60)
    print("MCP 서버 테스트 시작")
    print("=" * 60)

    # 1. todo_add 테스트
    print("\n1. todo_add 테스트 (Epic 생성)")
    result = await server._todo_add({
        "content": "테스트 Epic 항목",
        "type": "epic",
        "priority": "high",
        "description": "이것은 테스트용 Epic입니다."
    })
    print(result[0].text)

    # Epic ID 추출
    epic_id = None
    for line in result[0].text.split('\n'):
        if 'id=' in line:
            import re
            match = re.search(r'id=(\d+)', line)
            if match:
                epic_id = int(match.group(1))
                break

    # 2. todo_add 테스트 (Story 생성)
    print("\n2. todo_add 테스트 (Story 생성)")
    result = await server._todo_add({
        "content": "테스트 Story 항목",
        "type": "story",
        "parent_id": epic_id,
        "priority": "medium"
    })
    print(result[0].text)

    story_id = None
    for line in result[0].text.split('\n'):
        if 'id=' in line:
            import re
            match = re.search(r'id=(\d+)', line)
            if match:
                story_id = int(match.group(1))
                break

    # 3. todo_add 테스트 (Task 생성)
    print("\n3. todo_add 테스트 (Task 생성)")
    result = await server._todo_add({
        "content": "테스트 Task 항목 1",
        "type": "task",
        "parent_id": story_id,
        "priority": "low"
    })
    print(result[0].text)

    task_id = None
    for line in result[0].text.split('\n'):
        if 'id=' in line:
            import re
            match = re.search(r'id=(\d+)', line)
            if match:
                task_id = int(match.group(1))
                break

    # 4. todo_list 테스트
    print("\n4. todo_list 테스트")
    result = await server._todo_list({})
    print(result[0].text)

    # 5. todo_start 테스트
    print("\n5. todo_start 테스트")
    result = await server._todo_start({"todo_id": task_id})
    print(result[0].text)

    # 6. todo_get 테스트
    print("\n6. todo_get 테스트")
    result = await server._todo_get({"todo_id": task_id})
    print(result[0].text)

    # 7. todo_done 테스트
    print("\n7. todo_done 테스트")
    result = await server._todo_done({"todo_id": task_id})
    print(result[0].text)

    # 8. todo_update_description 테스트
    print("\n8. todo_update_description 테스트")
    result = await server._todo_update_description({
        "todo_id": story_id,
        "description": "업데이트된 Story 설명입니다."
    })
    print(result[0].text)

    # 9. todo_stats 테스트
    print("\n9. todo_stats 테스트")
    result = await server._todo_stats({})
    print(result[0].text)

    # 10. season_list 테스트
    print("\n10. season_list 테스트")
    result = await server._season_list({})
    print(result[0].text)

    # 11. season_current 테스트
    print("\n11. season_current 테스트")
    result = await server._season_current({})
    print(result[0].text)

    # 12. todo_set_status 테스트
    print("\n12. todo_set_status 테스트")
    result = await server._todo_set_status({
        "todo_id": story_id,
        "status": "in_progress"
    })
    print(result[0].text)

    # 13. 정리 - 테스트 항목 삭제
    print("\n13. 정리 - 테스트 항목 삭제")
    if epic_id:
        result = await server._todo_delete({"todo_id": epic_id})
        print(result[0].text)

    # 14. 최종 목록 확인
    print("\n14. 최종 목록 확인")
    result = await server._todo_list({})
    print(result[0].text)

    print("\n" + "=" * 60)
    print("MCP 서버 테스트 완료!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_mcp_server())
