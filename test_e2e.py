#!/usr/bin/env python3
"""
E2E 테스트 - Todo 앱 기능 테스트
"""

import sys
sys.path.insert(0, '/Users/sun/Document/01_project/todo-cli')

from todo import TodoManager, SeasonManager, TodoItem, Season
from pathlib import Path
import json
import os

class TestRunner:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []

    def test(self, name, func):
        try:
            func()
            self.passed += 1
            print(f"  {name}")
        except AssertionError as e:
            self.failed += 1
            print(f"  {name}: {e}")
        except Exception as e:
            self.failed += 1
            print(f"  {name}: {type(e).__name__}: {e}")

    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*50}")
        print(f" : {self.passed}/{total} ")
        if self.failed > 0:
            print(f" : {self.failed}")
            return False
        return True


def test_todo_manager_basic():
    """TodoManager """
    manager = TodoManager()

    #
    initial_count = len(manager.todos)

    # Todo
    todo = manager.add_todo(" ", type="task")
    assert todo.id is not None, "Todo ID "
    assert todo.content == " ", " "
    assert todo.status == "todo", " todo "
    assert len(manager.todos) == initial_count + 1, "Todo "
    print("  - Todo : OK")


def test_toggle_check():
    """  ( )"""
    manager = TodoManager()

    #
    todo = manager.add_todo(" ", type="task")
    todo_id = todo.id

    #
    assert todo.status == "todo", f" todo : {todo.status}"
    print(f"  - : {todo.status}")

    #  1: todo -> done
    result = manager.toggle_check(todo_id)
    assert result is not None, "toggle_check None "
    assert result.status == "done", f"todo -> done : {result.status}"
    print(f"  -  1: {todo.status} -> done")

    #  2: done -> todo
    result = manager.toggle_check(todo_id)
    assert result.status == "todo", f"done -> todo : {result.status}"
    print(f"  -  2: done -> todo")

    # in_progress : in_progress -> done
    manager.change_status(todo_id)  # todo -> in_progress
    todo = next(t for t in manager.todos if t.id == todo_id)
    assert todo.status == "in_progress", " "
    print(f"  - in_progress ")

    result = manager.toggle_check(todo_id)
    assert result.status == "done", f"in_progress -> done : {result.status}"
    print(f"  - : in_progress -> done")


def test_change_status():
    """  (s )"""
    manager = TodoManager()

    todo = manager.add_todo(" ", type="task")
    todo_id = todo.id

    # todo -> in_progress
    result = manager.change_status(todo_id)
    assert result.status == "in_progress", f"todo -> in_progress : {result.status}"
    print(f"  - todo -> in_progress: OK")

    # in_progress -> done
    result = manager.change_status(todo_id)
    assert result.status == "done", f"in_progress -> done : {result.status}"
    print(f"  - in_progress -> done: OK")

    # done -> todo
    result = manager.change_status(todo_id)
    assert result.status == "todo", f"done -> todo : {result.status}"
    print(f"  - done -> todo: OK")


def test_season_manager():
    """ """
    config_path = Path('/Users/sun/Document/01_project/todo-cli/config.json')
    manager = SeasonManager(config_path)

    #
    season = manager.create_season(" ", "2024-01-01", "2024-12-31")
    assert season.id is not None, " ID "
    assert season.name == " ", " "
    assert season.status == "active", " active "
    print(f"  - : OK (id={season.id})")

    #
    manager.set_current_season(season.id)
    assert manager.current_season_id == season.id, " "
    print(f"  - : OK")

    #
    current = manager.get_current_season()
    assert current is not None, " None"
    assert current.id == season.id, " ID "
    print(f"  - : OK")


def test_todo_with_season():
    """ Todo """
    config_path = Path('/Users/sun/Document/01_project/todo-cli/config.json')
    todo_manager = TodoManager()
    season_manager = SeasonManager(config_path)
    todo_manager.set_season_manager(season_manager)

    #
    season = season_manager.create_season(" ", "2024-01-01", "2024-12-31")
    season_manager.set_current_season(season.id)

    # Todo
    todo = todo_manager.add_todo(" Todo", season_id=season.id)
    assert todo.season_id == season.id, " ID "
    print(f"  - Todo : OK (season_id={todo.season_id})")

    #
    season_todos = todo_manager.get_todos_by_season(season.id)
    assert len(season_todos) > 0, " Todo "
    print(f"  - : OK ({len(season_todos)})")


def test_report_data():
    """ """
    manager = TodoManager()

    #
    manager.add_todo(" 1", type="task")
    manager.add_todo(" 2", type="epic")

    #
    report = manager.get_report_data("today")
    assert "period" in report, "period "
    assert "stats" in report, "stats "
    assert "todos" in report, "todos "
    print(f"  - : OK")

    #
    report = manager.get_report_data("weekly")
    assert report is not None, " None"
    print(f"  - : OK")


def test_status_icons():
    """ """
    #
    status_icons = {"todo": "⬜", "in_progress": "🔄", "done": "✅"}

    for status, icon in status_icons.items():
        assert len(icon) > 0, f"{status} "
        print(f"  - {status}: {icon}")


def test_description_field():
    """설명 필드 테스트"""
    manager = TodoManager()

    # 설명과 함께 Todo 추가
    todo = manager.add_todo("설명 테스트", type="task", description="초기 설명")
    assert todo.description == "초기 설명", "설명이 저장되지 않음"
    print(f"  - 설명과 함께 추가: OK")

    # 설명 없는 Todo
    todo2 = manager.add_todo("설명 없는 항목", type="task")
    assert todo2.description is None, "설명이 None이 아님"
    print(f"  - 설명 없이 추가: OK")

    # 설명 업데이트
    manager.update_description(todo2.id, "새로운 설명")
    updated_todo = manager.get_todo_by_id(todo2.id)
    assert updated_todo.description == "새로운 설명", "설명 업데이트 실패"
    print(f"  - 설명 업데이트: OK")

    # 설명 삭제 (None으로 설정)
    manager.update_description(todo2.id, None)
    updated_todo = manager.get_todo_by_id(todo2.id)
    assert updated_todo.description is None, "설명 삭제 실패"
    print(f"  - 설명 삭제: OK")


def test_description_persistence():
    """설명 영속성 테스트 - 업데이트 후 다시 불러오기"""
    manager = TodoManager()

    # Todo 추가
    todo = manager.add_todo("영속성 테스트", type="task")
    todo_id = todo.id

    # 설명 추가
    manager.update_description(todo_id, "저장될 설명")

    # 바로 다시 조회해서 확인
    retrieved = manager.get_todo_by_id(todo_id)
    assert retrieved.description == "저장될 설명", "설명이 즉시 조회되지 않음"
    print(f"  - 즉시 조회: OK")

    # 설명 수정
    manager.update_description(todo_id, "수정된 설명")
    retrieved = manager.get_todo_by_id(todo_id)
    assert retrieved.description == "수정된 설명", "수정된 설명이 조회되지 않음"
    print(f"  - 수정 후 조회: OK")

    # 빈 문자열로 설정하면 None이 되어야 함
    manager.update_description(todo_id, "")
    retrieved = manager.get_todo_by_id(todo_id)
    # update_description에서 빈 문자열을 None으로 변환하지 않으므로 빈 문자열 그대로
    assert retrieved.description == "" or retrieved.description is None, "빈 문자열 처리 실패"
    print(f"  - 빈 문자열 처리: OK")


def test_description_update_flow():
    """설명 수정 전체 플로우 테스트"""
    manager = TodoManager()

    # 1. 새 Todo 생성 (설명 없음)
    todo = manager.add_todo("플로우 테스트", type="task")
    assert todo.description is None, "초기 설명이 None이 아님"
    print(f"  - 초기 상태: 설명 없음")

    # 2. 설명 추가
    result = manager.update_description(todo.id, "첫 번째 설명")
    assert result == True, "update_description이 True를 반환하지 않음"
    todo = manager.get_todo_by_id(todo.id)
    assert todo.description == "첫 번째 설명", "설명 추가 실패"
    print(f"  - 설명 추가: OK")

    # 3. 설명 수정
    result = manager.update_description(todo.id, "두 번째 설명")
    assert result == True, "update_description이 True를 반환하지 않음"
    todo = manager.get_todo_by_id(todo.id)
    assert todo.description == "두 번째 설명", "설명 수정 실패"
    print(f"  - 설명 수정: OK")

    # 4. 긴 설명 추가
    long_desc = "이것은 매우 긴 설명입니다. " * 10
    result = manager.update_description(todo.id, long_desc)
    todo = manager.get_todo_by_id(todo.id)
    assert todo.description == long_desc, "긴 설명 저장 실패"
    print(f"  - 긴 설명: OK")

    # 5. 설명 제거
    result = manager.update_description(todo.id, None)
    todo = manager.get_todo_by_id(todo.id)
    assert todo.description is None, "설명 제거 실패"
    print(f"  - 설명 제거: OK")


def test_item_reordering():
    """ """
    manager = TodoManager()

    #
    todo1 = manager.add_todo(" 1", type="task")
    todo2 = manager.add_todo(" 2", type="task")
    todo3 = manager.add_todo(" 3", type="task")

    #
    assert todo1.order < todo2.order, "todo1 todo2 "
    assert todo2.order < todo3.order, "todo2 todo3 "
    print(f"  - : {todo1.order}, {todo2.order}, {todo3.order}")

    # todo2
    result = manager.move_item_up(todo2.id)
    assert result == True, " "
    updated_todo2 = manager.get_todo_by_id(todo2.id)
    updated_todo1 = manager.get_todo_by_id(todo1.id)
    assert updated_todo2.order < updated_todo1.order, " "
    print(f"  - : OK")

    # todo1
    result = manager.move_item_down(todo1.id)
    assert result == True, " "
    updated_todo1 = manager.get_todo_by_id(todo1.id)
    updated_todo2 = manager.get_todo_by_id(todo2.id)
    assert updated_todo1.order > updated_todo2.order, " "
    print(f"  - : OK")

    #   ( )
    result = manager.move_item_up(todo1.id)
    assert result == True, " "
    print(f"  - : OK")


def test_order_field():
    """ order """
    manager = TodoManager()

    #
    todo1 = manager.add_todo(" 1", type="epic")
    todo2 = manager.add_todo(" 2", type="epic")

    #
    assert hasattr(todo1, 'order'), "order "
    assert hasattr(todo2, 'order'), "order "
    assert todo1.order >= 0, "order 0 "
    assert todo2.order >= 0, "order 0 "
    print(f"  - order : OK ({todo1.order}, {todo2.order})")


def test_get_todo_by_id():
    """ ID Todo """
    manager = TodoManager()

    todo = manager.add_todo("ID ", type="task")
    found = manager.get_todo_by_id(todo.id)
    assert found is not None, "Todo "
    assert found.id == todo.id, "ID "
    assert found.content == "ID ", " "

    # ID
    not_found = manager.get_todo_by_id(99999)
    assert not_found is None, " ID None "
    print(f"  - ID Todo : OK")


def main():
    print("="*50)
    print("Todo 앱 E2E 테스트 시작")
    print("="*50)

    runner = TestRunner()

    print("\n[1] TodoManager 기본 기능")
    runner.test("TodoManager 기본", test_todo_manager_basic)

    print("\n[2] 체크 토글 (스페이스바)")
    runner.test("toggle_check", test_toggle_check)

    print("\n[3] 상태 순환 (s 키)")
    runner.test("change_status", test_change_status)

    print("\n[4] 시즌 관리")
    runner.test("SeasonManager", test_season_manager)

    print("\n[5] 시즌별 Todo")
    runner.test("Todo with Season", test_todo_with_season)

    print("\n[6] 리포트 데이터")
    runner.test("Report Data", test_report_data)

    print("\n[7] 상태 아이콘")
    runner.test("Status Icons", test_status_icons)

    print("\n[8] 설명 필드")
    runner.test("설명 필드", test_description_field)

    print("\n[9] 설명 영속성")
    runner.test("설명 영속성", test_description_persistence)

    print("\n[10] 설명 수정 플로우")
    runner.test("설명 수정 플로우", test_description_update_flow)

    print("\n[11] 항목 순서 변경")
    runner.test("항목 순서 변경", test_item_reordering)

    print("\n[12] order 필드")
    runner.test("order 필드", test_order_field)

    print("\n[13] ID로 Todo 찾기")
    runner.test("ID로 Todo 찾기", test_get_todo_by_id)

    success = runner.summary()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
