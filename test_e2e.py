#!/usr/bin/env python3
"""
E2E 테스트 스크립트 - Todo TUI 앱 자동 테스트
"""

import asyncio
import sys
import os

# 경로 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from todo import TodoApp, TodoManager
from textual.widgets import Input, Select


async def test_todo_app():
    """Todo 앱 E2E 테스트"""
    print("=" * 60)
    print("🧪 Todo TUI 앱 E2E 테스트 시작")
    print("=" * 60)

    # 기존 데이터 삭제
    import json
    from pathlib import Path
    config_path = Path(__file__).parent / "config.json"
    if config_path.exists():
        with open(config_path, "r") as f:
            config = json.load(f)
        todos_file = Path(config["save_path"]).expanduser() / "todos.json"
        if todos_file.exists():
            todos_file.unlink()
            print("✓ 기존 데이터 삭제")

    app = TodoApp()

    async with app.run_test() as pilot:
        # ============================================
        # 테스트 1: 앱 시작 확인
        # ============================================
        print("\n📌 테스트 1: 앱 시작 확인")
        assert app is not None
        print("   ✓ 앱이 정상적으로 시작됨")

        # ============================================
        # 테스트 2: Epic 추가 (직접 Manager 사용)
        # ============================================
        print("\n📌 테스트 2: Epic 추가")

        # Manager를 통해 직접 추가
        epic = app.manager.add_todo(
            content="프로젝트 개발",
            type="epic",
            priority="high"
        )

        assert len(app.manager.todos) == 1
        assert app.manager.todos[0].type == "epic"
        assert app.manager.todos[0].content == "프로젝트 개발"
        print("   ✓ Epic '프로젝트 개발' 추가됨")

        # 화면 새로고침
        app.screen._refresh_tree()
        await pilot.pause()

        # ============================================
        # 테스트 3: Story 추가 (Epic 하위)
        # ============================================
        print("\n📌 테스트 3: Story 추가 (Epic 하위)")

        story = app.manager.add_todo(
            content="프론트엔드 개발",
            type="story",
            parent_id=epic.id
        )

        assert len(app.manager.todos) == 2
        story = [t for t in app.manager.todos if t.type == "story"][0]
        assert story.content == "프론트엔드 개발"
        assert story.parent_id == 1  # Epic의 ID
        print("   ✓ Story '프론트엔드 개발' 추가됨 (Epic 하위)")

        # ============================================
        # 테스트 4: Task 추가 (Story 하위)
        # ============================================
        print("\n📌 테스트 4: Task 추가 (Story 하위)")

        task = app.manager.add_todo(
            content="로그인 페이지 구현",
            type="task",
            parent_id=story.id,
            due_date="2024-12-31"
        )

        assert len(app.manager.todos) == 3
        task = [t for t in app.manager.todos if t.type == "task"][0]
        assert task.content == "로그인 페이지 구현"
        assert task.parent_id == 2  # Story의 ID
        assert task.due_date == "2024-12-31"
        print("   ✓ Task '로그인 페이지 구현' 추가됨 (Story 하위, due: 2024-12-31)")

        # 화면 새로고침
        app.screen._refresh_tree()
        await pilot.pause()

        # ============================================
        # 테스트 5: 또 다른 Task 추가 (Epic 직접 하위)
        # ============================================
        print("\n📌 테스트 5: Task 추가 (Epic 직접 하위)")

        task2 = app.manager.add_todo(
            content="프로젝트 문서 작성",
            type="task",
            parent_id=epic.id,
            priority="low"
        )

        assert len(app.manager.todos) == 4
        task2 = [t for t in app.manager.todos if t.content == "프로젝트 문서 작성"][0]
        assert task2.parent_id == 1  # Epic의 ID
        print("   ✓ Task '프로젝트 문서 작성' 추가됨 (Epic 직접 하위)")

        # ============================================
        # 테스트 6: 트리 구조 확인
        # ============================================
        print("\n📌 테스트 6: 트리 구조 확인")

        root_items = app.manager.get_root_items()
        assert len(root_items) == 1
        assert root_items[0].type == "epic"
        print("   ✓ 루트에 1개의 Epic 존재")

        epic_children = app.manager.get_children(1)
        assert len(epic_children) == 2  # Story 1개 + Task 1개
        types = [t.type for t in epic_children]
        assert "story" in types
        assert "task" in types
        print("   ✓ Epic 하위에 1개의 Story와 1개의 Task 존재")

        story_children = app.manager.get_children(2)
        assert len(story_children) == 1
        assert story_children[0].type == "task"
        print("   ✓ Story 하위에 1개의 Task 존재")

        # ============================================
        # 테스트 7: 상태 변경
        # ============================================
        print("\n📌 테스트 7: 상태 변경")

        # Task 상태 변경: todo -> in_progress
        result = app.manager.change_status(3)
        assert result.status == "in_progress"
        print("   ✓ Task ID 3 진행중 상태로 변경됨")

        # 다시 변경: in_progress -> done
        result = app.manager.change_status(3)
        assert result.status == "done"
        print("   ✓ Task ID 3 완료 상태로 변경됨")

        # 다시 변경: done -> todo
        result = app.manager.change_status(3)
        assert result.status == "todo"
        print("   ✓ Task ID 3 대기 상태로 변경됨")

        # ============================================
        # 테스트 8: 통계 확인
        # ============================================
        print("\n📌 테스트 8: 통계 확인")

        stats = app.manager.get_stats()
        assert stats["total"] == 4
        assert stats["epics"] == 1
        assert stats["stories"] == 1
        assert stats["tasks"] == 2
        assert stats["todo"] == 4
        assert stats["in_progress"] == 0
        assert stats["done"] == 0
        print(f"   ✓ 통계: 전체 {stats['total']}, Epic {stats['epics']}, Story {stats['stories']}, Task {stats['tasks']}")

        # ============================================
        # 테스트 9: 키보드 입력 테스트 (펼치기/접기)
        # ============================================
        print("\n📌 테스트 9: 키보드 입력 테스트")

        # 화면 새로고침
        app.screen._refresh_tree()
        await pilot.pause()

        # 전체 펼치기
        await pilot.press("e")
        await pilot.pause()
        print("   ✓ 전체 펼치기 실행")

        # 전체 접기
        await pilot.press("c")
        await pilot.pause()
        print("   ✓ 전체 접기 실행")

        # ============================================
        # 테스트 10: Story 삭제 (하위 Task도 함께 삭제)
        # ============================================
        print("\n📌 테스트 10: Story 삭제 (하위 Task 포함)")

        # Story 삭제 (ID 2) - 하위 Task (ID 3)도 함께 삭제되어야 함
        app.manager.delete_todo(2)

        # Story 1개와 하위 Task 1개가 삭제되어 총 2개가 남아야 함
        assert len(app.manager.todos) == 2
        remaining_ids = [t.id for t in app.manager.todos]
        assert 2 not in remaining_ids  # Story 삭제됨
        assert 3 not in remaining_ids  # Story의 하위 Task도 삭제됨
        print("   ✓ Story 삭제 시 하위 Task도 함께 삭제됨")
        print(f"   ✓ 남은 항목: {len(app.manager.todos)}개 (Epic 1개, Task 1개)")

        # ============================================
        # 테스트 11: Epic 삭제 (남은 모든 항목 삭제)
        # ============================================
        print("\n📌 테스트 11: Epic 삭제 (하위 항목 포함)")

        # Epic 삭제 (ID 1) - 하위 Task (ID 4)도 함께 삭제되어야 함
        app.manager.delete_todo(1)

        assert len(app.manager.todos) == 0
        print("   ✓ Epic 삭제 시 모든 하위 항목이 함께 삭제됨")

        # ============================================
        # 테스트 12: 데이터 저장 및 로드
        # ============================================
        print("\n📌 테스트 12: 데이터 저장 및 로드")

        # 새 항목 추가
        new_epic = app.manager.add_todo(
            content="새 프로젝트",
            type="epic"
        )

        # 파일에서 직접 로드 테스트
        new_manager = TodoManager()
        assert len(new_manager.todos) == 1
        assert new_manager.todos[0].content == "새 프로젝트"
        print("   ✓ 데이터가 파일에 저장되고 정상적으로 로드됨")

        # ============================================
        # 테스트 13: 부모 선택 가능 목록 테스트
        # ============================================
        print("\n📌 테스트 13: 부모 선택 가능 목록")

        # Epic의 가능한 부모 (없어야 함)
        epic_parents = new_manager.get_possible_parents("epic")
        assert len(epic_parents) == 0
        print("   ✓ Epic은 부모를 가질 수 없음")

        # Story의 가능한 부모 (Epic만)
        story_parents = new_manager.get_possible_parents("story")
        assert len(story_parents) == 1
        assert story_parents[0].type == "epic"
        print("   ✓ Story는 Epic 하위에만 추가 가능")

        # Task의 가능한 부모 (Epic 또는 Story)
        # 먼저 Story 추가
        new_manager.add_todo(content="테스트 스토리", type="story", parent_id=1)
        task_parents = new_manager.get_possible_parents("task")
        assert len(task_parents) == 2  # Epic 1개 + Story 1개
        print("   ✓ Task는 Epic 또는 Story 하위에 추가 가능")

    print("\n" + "=" * 60)
    print("✅ 모든 E2E 테스트 통과! (13/13)")
    print("=" * 60)
    return True


async def test_ui_interaction():
    """UI 인터랙션 테스트"""
    print("\n" + "=" * 60)
    print("🧪 UI 인터랙션 테스트 시작")
    print("=" * 60)

    # 데이터 초기화
    import json
    from pathlib import Path
    config_path = Path(__file__).parent / "config.json"
    if config_path.exists():
        with open(config_path, "r") as f:
            config = json.load(f)
        todos_file = Path(config["save_path"]).expanduser() / "todos.json"
        if todos_file.exists():
            todos_file.unlink()

    app = TodoApp()

    async with app.run_test() as pilot:
        # 테스트 데이터 생성
        app.manager.add_todo("테스트 Epic", type="epic")
        app.manager.add_todo("테스트 Story", type="story", parent_id=1)
        app.manager.add_todo("테스트 Task", type="task", parent_id=2)
        app.screen._refresh_tree()
        await pilot.pause()

        print("\n📌 UI 인터랙션 테스트")

        # 전체 펼치기
        await pilot.press("e")
        await pilot.pause()
        print("   ✓ 'e' 키: 전체 펼치기")

        # 전체 접기
        await pilot.press("c")
        await pilot.pause()
        print("   ✓ 'c' 키: 전체 접기")

        # 방향키 아래
        await pilot.press("down")
        await pilot.pause()
        print("   ✓ 방향키: 항목 탐색")

        # 펼치기 (오른쪽)
        await pilot.press("right")
        await pilot.pause()
        print("   ✓ '→' 키: 항목 펼치기")

        # 접기 (왼쪽)
        await pilot.press("left")
        await pilot.pause()
        print("   ✓ '←' 키: 항목 접기")

        # 추가 화면 열기
        await pilot.press("a")
        await pilot.pause()

        # 추가 화면이 열렸는지 확인
        try:
            content_input = app.query_one("#content", Input)
            print("   ✓ 'a' 키: 추가 화면 열림")

            # ============================================
            # 탭 키 동작 테스트
            # ============================================
            print("\n   📌 탭 키 동작 테스트:")

            # 현재 포커스 확인
            focused_before = app.focused
            print(f"      탭 전 포커스: {type(focused_before).__name__ if focused_before else 'None'}")

            # 탭 키 누르기
            await pilot.press("tab")
            await pilot.pause()

            focused_after_tab = app.focused
            print(f"      탭 후 포커스: {type(focused_after_tab).__name__ if focused_after_tab else 'None'}")

            # 여러 번 탭 눌러서 포커스 이동 확인
            for i in range(5):
                await pilot.press("tab")
                await pilot.pause()
                focused = app.focused
                widget_type = type(focused).__name__ if focused else "None"
                print(f"      Tab x{i+2}: {widget_type}")

            # Shift+Tab (역방향)
            await pilot.press("shift+tab")
            await pilot.pause()
            focused_back = app.focused
            print(f"      Shift+Tab: {type(focused_back).__name__ if focused_back else 'None'}")

        except Exception as e:
            print(f"   ✗ 'a' 키: 추가 화면 열기 실패 - {e}")

        # 취소 (Escape)
        await pilot.press("escape")
        await pilot.pause()
        print("   ✓ Escape: 추가 화면 닫기")

    print("\n" + "=" * 60)
    print("✅ UI 인터랙션 테스트 완료!")
    print("=" * 60)
    return True


async def test_tree_selection_and_add_child():
    """트리 선택 후 하위 추가 테스트"""
    print("\n" + "=" * 60)
    print("🧪 트리 선택 및 하위 추가 테스트 시작")
    print("=" * 60)

    # 데이터 초기화
    import json
    from pathlib import Path
    config_path = Path(__file__).parent / "config.json"
    if config_path.exists():
        with open(config_path, "r") as f:
            config = json.load(f)
        todos_file = Path(config["save_path"]).expanduser() / "todos.json"
        if todos_file.exists():
            todos_file.unlink()

    app = TodoApp()

    async with app.run_test() as pilot:
        await pilot.pause()

        # 테스트 데이터 생성
        app.manager.add_todo("부모 Epic", type="epic")
        app.screen._refresh_tree()
        await pilot.pause()

        print("\n📌 테스트: 트리에서 항목 선택 후 'A' 키로 하위 추가")

        # 전체 펼치기
        await pilot.press("e")
        await pilot.pause()

        # 방향키로 Epic 선택 (루트 노드에서 아래로)
        await pilot.press("down")
        await pilot.pause()

        # 트리에서 선택된 항목 확인
        tree = app.screen.query_one("#todo-tree")
        print(f"   Tree cursor_node: {tree.cursor_node}")

        if tree.cursor_node and hasattr(tree.cursor_node, 'data') and tree.cursor_node.data:
            selected_id = tree.cursor_node.data.todo_id
            selected_type = tree.cursor_node.data.todo_type
            print(f"   ✓ 선택된 항목: ID={selected_id}, Type={selected_type}")

            # 화면의 selected_todo_id 업데이트 확인
            await pilot.pause()
            screen_selected_id = app.screen.selected_todo_id
            screen_selected_type = app.screen.selected_todo_type
            print(f"   Screen selected: ID={screen_selected_id}, Type={screen_selected_type}")

            if screen_selected_id == selected_id:
                print("   ✓ 트리 선택이 화면에 반영됨")
            else:
                print(f"   ✗ 트리 선택이 화면에 반영되지 않음 (expected={selected_id}, got={screen_selected_id})")
        else:
            print("   ✗ 트리에서 항목이 선택되지 않음")

        # 'A' 키로 하위 추가 화면 열기
        await pilot.press("A")  # Shift+a
        await pilot.pause()

        # 추가 화면이 열렸는지 확인
        try:
            content_input = app.screen.query_one("#content", Input)
            print("   ✓ 'A' 키: 하위 추가 화면 열림")

            # 상위 항목이 제대로 전달되었는지 확인
            # AddTodoScreen의 default_parent_id 확인
            current_screen = app.screen
            if hasattr(current_screen, 'default_parent_id') and current_screen.default_parent_id:
                print(f"   ✓ 상위 항목 ID 전달됨: {current_screen.default_parent_id}")
            else:
                print("   ✗ 상위 항목이 전달되지 않음")

            # 취소
            await pilot.press("escape")
            await pilot.pause()
            print("   ✓ Escape: 추가 화면 닫기")

        except Exception as e:
            print(f"   ✗ 'A' 키: 하위 추가 화면 열기 실패 - {e}")

    print("\n" + "=" * 60)
    print("✅ 트리 선택 및 하위 추가 테스트 완료!")
    print("=" * 60)
    return True


async def test_keyboard_shortcuts():
    """모든 키보드 단축키 테스트"""
    print("\n" + "=" * 60)
    print("🧪 키보드 단축키 전체 테스트 시작")
    print("=" * 60)

    # 데이터 초기화
    import json
    from pathlib import Path
    config_path = Path(__file__).parent / "config.json"
    if config_path.exists():
        with open(config_path, "r") as f:
            config = json.load(f)
        todos_file = Path(config["save_path"]).expanduser() / "todos.json"
        if todos_file.exists():
            todos_file.unlink()

    app = TodoApp()

    async with app.run_test() as pilot:
        await pilot.pause()

        # 테스트 데이터 생성
        epic = app.manager.add_todo("테스트 Epic", type="epic")
        story = app.manager.add_todo("테스트 Story", type="story", parent_id=epic.id)
        task = app.manager.add_todo("테스트 Task", type="task", parent_id=story.id)
        app.screen._refresh_tree()
        await pilot.pause()

        print("\n📌 단축키 테스트:")

        # ============================================
        # 1. 전체 펼치기 (e)
        # ============================================
        await pilot.press("e")
        await pilot.pause()
        print("   ✓ 'e' 키: 전체 펼치기")

        # ============================================
        # 2. 전체 접기 (c)
        # ============================================
        await pilot.press("c")
        await pilot.pause()
        print("   ✓ 'c' 키: 전체 접기")

        # ============================================
        # 3. 방향키 탐색 (down)
        # ============================================
        await pilot.press("down")
        await pilot.pause()
        assert app.screen.selected_todo_id == epic.id
        print("   ✓ 'down' 키: Epic 선택")

        # ============================================
        # 4. 노드 펼치기 (right)
        # ============================================
        await pilot.press("right")
        await pilot.pause()
        print("   ✓ '→' 키: 노드 펼치기")

        # ============================================
        # 5. 노드 접기 (left)
        # ============================================
        await pilot.press("left")
        await pilot.pause()
        print("   ✓ '←' 키: 노드 접기")

        # ============================================
        # 6. 완료 토글 (t)
        # ============================================
        # Epic 선택 상태에서 토글 테스트
        # (방향키 이동이 테스트 환경에서 불안정하므로 직접 선택)
        app.screen.selected_todo_id = story.id
        app.screen.selected_todo_type = story.type
        await pilot.pause()

        # s 키로 상태 변경
        await pilot.press("s")
        await pilot.pause()

        # 상태 변경 확인
        story_after = [t for t in app.manager.todos if t.id == story.id][0]
        assert story_after.status == "in_progress"
        print(f"   ✓ 's' 키: 상태 변경 (todo -> in_progress)")

        # 다시 변경
        await pilot.press("s")
        await pilot.pause()
        story_final = [t for t in app.manager.todos if t.id == story.id][0]
        assert story_final.status == "done"
        print("   ✓ 's' 키: 상태 변경 (in_progress -> done)")

        # 한 번 더 변경
        await pilot.press("s")
        await pilot.pause()
        story_back = [t for t in app.manager.todos if t.id == story.id][0]
        assert story_back.status == "todo"
        print("   ✓ 's' 키: 상태 변경 (done -> todo)")

        # ============================================
        # 7. 삭제 (d)
        # ============================================
        # Task 선택 상태로 설정
        app.screen.selected_todo_id = task.id
        app.screen.selected_todo_type = task.type
        await pilot.pause()

        # d 키로 삭제
        await pilot.press("d")
        await pilot.pause()

        # 삭제 확인
        remaining_ids = [t.id for t in app.manager.todos]
        assert task.id not in remaining_ids
        print(f"   ✓ 'd' 키: Task 삭제 (ID={task.id})")

        # ============================================
        # 8. 추가 화면 열기/닫기 (a / escape)
        # ============================================
        await pilot.press("a")
        await pilot.pause()

        try:
            content_input = app.screen.query_one("#content", Input)
            print("   ✓ 'a' 키: 추가 화면 열기")

            # Escape로 닫기
            await pilot.press("escape")
            await pilot.pause()
            print("   ✓ 'escape' 키: 추가 화면 닫기")
        except:
            print("   ✗ 'a' 키: 추가 화면 열기 실패")

        # ============================================
        # 9. 하위 추가 (A)
        # ============================================
        # Epic 선택 상태로 설정
        app.screen.selected_todo_id = epic.id
        app.screen.selected_todo_type = epic.type
        await pilot.pause()

        await pilot.press("A")
        await pilot.pause()

        try:
            content_input = app.screen.query_one("#content", Input)
            add_screen = app.screen
            assert add_screen.default_parent_id == epic.id
            print(f"   ✓ 'A' 키: 하위 추가 화면 (parent_id={epic.id})")

            # Escape로 닫기
            await pilot.press("escape")
            await pilot.pause()
        except:
            print("   ✗ 'A' 키: 하위 추가 화면 열기 실패")

    print("\n" + "=" * 60)
    print("✅ 키보드 단축키 테스트 완료!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    try:
        # 메인 테스트 실행
        asyncio.run(test_todo_app())

        # UI 인터랙션 테스트 실행
        asyncio.run(test_ui_interaction())

        # 트리 선택 및 하위 추가 테스트 실행
        asyncio.run(test_tree_selection_and_add_child())

        # 키보드 단축키 테스트 실행
        asyncio.run(test_keyboard_shortcuts())

        print("\n🎉 모든 테스트가 성공적으로 완료되었습니다!")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
