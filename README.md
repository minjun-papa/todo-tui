# Claude Planner

<div align="center">

**Claude Code와 연동되는 작업 계획 관리 도구 - TUI + Dashboard**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Electron](https://img.shields.io/badge/Electron-33+-blue.svg)](https://www.electronjs.org/)
[![React](https://img.shields.io/badge/React-18-blue.svg)](https://react.dev/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

[English](#english) | [한국어](#한국어)

</div>

---

## 한국어

### 소개

**Claude Planner**는 Claude Code 세션에서 수행하는 작업을 자동으로 계획하고 추적하는 도구입니다.

- **TUI**: 터미널에서 직접 사용하는 인터랙티브 Todo 관리
- **Plan Dashboard**: Electron + React 데스크톱 앱으로 작업 진행 상황 실시간 모니터링
- **MCP Server**: Claude Code가 작업을 자동으로 Plan으로 생성하고 관리

### 아키텍처

```
claude-planner/
├── todo.py                    # 데이터 레이어 (Plan, TodoItem, PlanManager)
├── todo_mcp_server.py         # MCP 서버 (17개 툴)
├── plan-dashboard/            # Electron Dashboard
│   ├── main.js               # Electron 메인 프로세스
│   ├── preload.js            # IPC 브릿지
│   ├── setup.sh              # 자동 설치 스크립트
│   └── src/
│       ├── app.js            # React 진입점
│       ├── styles.css        # Tokyo Night 테마
│       └── components/       # UI 컴포넌트
│           ├── Dashboard.jsx
│           ├── PlanCard.jsx
│           ├── PlanDetail.jsx
│           ├── PlanTree.jsx
│           ├── Timeline.jsx
│           └── AddPlanModal.jsx
```

### 작동 흐름

```
사용자가 Claude Code에 작업 요청
       ↓
CLAUDE.md 지시어에 따라 자동 실행:
  1. plan_create → 새 Plan 생성
  2. todo_add (Epic > Story > Task) → 작업 세분화
  3. todo_start / todo_done → 진행 상황 업데이트
  4. plan_end → 완료 처리
       ↓
Plan Dashboard에 실시간 반영 (2초 폴링)
```

### 빠른 시작

```bash
# 1. 클론
git clone https://github.com/minjun-papa/claude-planner.git

# 2. 자동 설정
cd claude-planner/plan-dashboard && bash setup.sh

# 3. 대시보드 실행
npm start

# 4. Claude Code 새 세션 열기 → 작업 요청 → 자동으로 Plan 생성됨
```

### setup.sh가 하는 일

| 단계 | 내용 |
|------|------|
| 1 | `~/todos/` 데이터 디렉토리 + plans.json, todos.json 생성 |
| 2 | Python 가상환경 생성 + mcp, textual, requests 설치 |
| 3 | `~/.mcp.json`에 todo MCP 서버 등록 |
| 4 | `~/.claude/CLAUDE.md`에 자동 Plan 생성 지시어 추가 |
| 5 | Electron dashboard npm 의존성 설치 |

### Plan Dashboard 기능

| 기능 | 설명 |
|------|------|
| Dashboard | 활성/완료 Plan 카드 뷰, 진행률 바, 통계 |
| Plan Tree | Epic > Story > Task 계층 트리 뷰 |
| Timeline | 시간순 Plan 배치, 소요 시간 표시 |
| Plan Detail | 개별 Plan 상세, Task 상태 토글, Task 추가 |
| Real-time | 2초 폴링으로 파일 변경 자동 감지 |
| Dark Theme | Tokyo Night 컬러 스킴 |

### MCP 툴 목록 (17개)

#### Todo 툴

| 툴 | 설명 |
|-----|------|
| `todo_add` | 새 항목 추가 (Epic/Story/Task, plan_id 지정 가능) |
| `todo_done` | 완료 처리 |
| `todo_start` | 진행중으로 변경 |
| `todo_list` | 목록 조회 (시즌/상태/타입 필터) |
| `todo_get` | 상세 조회 |
| `todo_delete` | 삭제 (하위 항목 포함) |
| `todo_update_description` | 설명 수정 |
| `todo_stats` | 통계 조회 |
| `todo_set_status` | 상태 직접 설정 |

#### Plan 툴

| 툴 | 설명 |
|-----|------|
| `plan_create` | 새 Plan 생성 (name, working_dir, model, prompt) |
| `plan_end` | Plan 완료 처리 |
| `plan_list` | Plan 목록 조회 |
| `plan_get` | Plan 상세 조회 (연관 Todo 통계 포함) |
| `plan_update` | Plan 정보 수정 |
| `plan_delete` | Plan 삭제 |

#### Season 툴

| 툴 | 설명 |
|-----|------|
| `season_list` | 시즌 목록 |
| `season_current` | 현재 시즌 정보 |

### TUI 키보드 단축키

| 키 | 기능 |
|----|------|
| `Space` | 상태 토글 (To Do ↔ Done) |
| `s` | 상태 변경 (대기 → 진행중 → 완료 → 대기) |
| `a` | 새 항목 추가 |
| `A` | 하위 항목 추가 |
| `d` | 삭제 |
| `e` / `c` | 전체 펼치기 / 접기 |
| `S` | 시즌 선택 |
| `r` | 리포트 보기 |
| `j` | Jira 동기화 |
| `q` | 종료 |

### 데이터 모델

**Plan** (`~/todos/plans.json`)

```json
{
  "id": 1,
  "name": "Plan Dashboard UI 개발",
  "status": "active",
  "source": "claude_code",
  "working_dir": "/path/to/project",
  "model": "claude-sonnet-4-20250514",
  "prompt": "원본 요청 내용",
  "started_at": "2026-04-01T12:00:00",
  "ended_at": null
}
```

**TodoItem** (`~/todos/todos.json`) - `plan_id` 필드로 Plan과 연결

### 요구사항

- Python 3.10+
- Node.js 18+
- macOS (Electron titleBarStyle: hiddenInset)

---

## English

### Introduction

**Claude Planner** is a task planning and tracking tool that integrates with Claude Code sessions.

- **TUI**: Interactive terminal-based Todo management
- **Plan Dashboard**: Electron + React desktop app for real-time monitoring
- **MCP Server**: Auto-creates plans and tracks progress from Claude Code

### Quick Start

```bash
# 1. Clone
git clone https://github.com/minjun-papa/claude-planner.git

# 2. Auto setup
cd claude-planner/plan-dashboard && bash setup.sh

# 3. Start dashboard
npm start

# 4. Open a new Claude Code session → request a task → Plan auto-created
```

### Architecture

```
Claude Code session → MCP tools (plan_create, todo_add, ...)
       ↓
~/todos/plans.json + todos.json
       ↓
Electron Dashboard (2s polling)
```

### MCP Tools (17)

- **Todo**: todo_add, todo_done, todo_start, todo_list, todo_get, todo_delete, todo_update_description, todo_stats, todo_set_status
- **Plan**: plan_create, plan_end, plan_list, plan_get, plan_update, plan_delete
- **Season**: season_list, season_current

### Requirements

- Python 3.10+
- Node.js 18+
- macOS

---

## License

MIT License - feel free to use and modify!

---

<div align="center">

Made with ❤️ by [minjun-papa](https://github.com/minjun-papa)

</div>
