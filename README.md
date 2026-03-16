# 📋 Todo TUI

<div align="center">

**터미널에서 인터랙티브하게 사용하는 TUI 기반 Todo 관리 앱**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Textual](https://img.shields.io/badge/Textual-0.47+-purple.svg)](https://github.com/Textualize/textual)

[English](#english) | [한국어](#한국어)

</div>

---

## 한국어

### ✨ 소개

**Todo TUI**는 터미널에서 직관적으로 사용할 수 있는 할 일 관리 애플리케이션입니다.

프로젝트 관리를 위한 **Epic > Story > Task** 계층 구조를 지원하며, 진행 상황을 한눈에 파악할 수 있는 깔끔한 UI를 제공합니다.

### 🎯 주요 기능

| 기능 | 설명 |
|------|------|
| 🏗️ **계층 구조** | Epic > Story > Task 3단계 구조로 체계적으로 관리 |
| 🔄 **상태 관리** | 대기 → 진행중 → 완료 상태 순환 |
| 📊 **진행중 표시** | 진행중인 항목을 상단에 별도 표시 |
| 🎨 **직관적 UI** | 이모지 아이콘으로 상태/타입/우선순위 표시 |
| 💾 **자동 저장** | JSON 형식으로 데이터 자동 저장 |
| ⌨️ **키보드 중심** | 마우스 없이 키보드만으로 모든 조작 가능 |
| 📅 **시즌 관리** | 프로젝트/기간별로 시즌을 나누어 관리 |
| 🔗 **Jira 동기화** | Jira와 양방향 동기화 지원 |
| 🤖 **Claude MCP 연동** | Claude와 MCP로 직접 연동하여 작업 관리 |
| 📈 **리포트** | 오늘/주간/시즌별 리포트 생성 |

### 📸 스크린샷

```
┌─────────────────────────────────────────────────────────────┐
│ 🔗 Jira 연결됨 | J: 동기화 | Ctrl+J: 설정                    │
├─────────────────────────────────────────────────────────────┤
│ 📊 전체: 5 | 📋 대기: 2 | 🔄 진행중: 2 | ✅ 완료: 1         │
│ 📁 Epic: 1 | 📖 Story: 2 | ✅ Task: 2                       │
├─────────────────────────────────────────────────────────────┤
│ 🔄 진행중 (2): 로그인 구현 (task) | API 개발 (task)         │
├─────────────────────────────────────────────────────────────┤
│ 📋 Todo List                                                │
│ ├─ ○ 📁 🟡 [general] 프로젝트 개발 [PROJ-1]                 │
│ │  ├─ ◐ 📖 🟡 [general] 백엔드 개발 [PROJ-2]                │
│ │  │  └─ ◐ ✅ 🟡 [general] API 개발 [PROJ-3]                │
│ │  └─ ● 📖 🟢 [general] 프론트엔드 개발                      │
│ │     └─ ● ✅ 🔴 [general] 로그인 구현 (due: 2024-12-31)    │
└─────────────────────────────────────────────────────────────┘
```

### 🚀 설치

#### 방법 1: pip로 설치 (권장)

```bash
# 저장소 클론
git clone https://github.com/minjun-papa/todo-tui.git
cd todo-tui

# 패키지 설치
pip3 install .
```

#### PATH 설정 (최초 1회)

```bash
echo 'export PATH="$HOME/Library/Python/3.9/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### ▶️ 실행

```bash
todo
```

또는 PATH 설정 없이 직접 실행:

```bash
python3 -m todo_tui.main
```

### ⌨️ 키보드 단축키

#### 메인 화면

| 키 | 기능 |
|----|------|
| `Space` | 체크 토글 (To Do ↔ Done) |
| `s` | 상태 변경 (대기 → 진행중 → 완료 → 대기) |
| `a` | 새 항목 추가 |
| `A` | 하위 항목 추가 (선택된 항목 아래) |
| `d` | 삭제 (하위 항목도 함께 삭제) |
| `e` | 전체 펼치기 |
| `c` | 전체 접기 |
| `→` | 선택 노드 펼치기 |
| `←` | 선택 노드 접기 |
| `S` | 시즌 선택 |
| `r` | 리포트 보기 |
| `j` | Jira 동기화 |
| `Ctrl+J` | Jira 설정 |
| `↑/↓` | 항목 탐색 |
| `q` | 앱 종료 |

#### 추가 화면

| 키 | 기능 |
|----|------|
| `Tab` | 다음 필드로 이동 |
| `Shift+Tab` | 이전 필드로 이동 |
| `Enter` | 저장 |
| `Escape` | 취소 |

### 🔗 Jira 연동

#### Jira 설정

1. `Ctrl+J`를 눌러 Jira 설정 화면 열기
2. 다음 정보 입력:
   - **Jira URL**: `https://your-company.atlassian.net`
   - **이메일**: Jira 계정 이메일
   - **API 토큰**: [Atlassian API 토큰](https://id.atlassian.com/manage-profile/security/api-tokens)에서 생성
   - **프로젝트 키**: 예) `PROJ`
3. "연결 테스트" 버튼으로 연결 확인
4. "저장" 버튼으로 설정 저장

#### Jira 동기화

- `j` 키를 눌러 Jira에서 Todo 동기화
- 새 Todo 추가 시 자동으로 Jira 이슈 생성
- 상태 변경 시 자동으로 Jira 이슈 상태 업데이트

#### 데이터 매핑

| Todo 필드 | Jira 필드 |
|-----------|-----------|
| content | summary |
| type (epic/story/task) | issuetype (Epic/Story/Task) |
| status | status (To Do/In Progress/Done) |
| priority | priority |
| due_date | duedate |

### 📁 데이터 저장

- **저장 위치**: `~/.todo-tui/`
- **설정 파일**: `~/.todo-tui/config.json`
- **Todo 데이터**: `~/.todo-tui/todos.json`
- **시즌 데이터**: `~/.todo-tui/seasons/`

### ⚙️ 설정 파일

`~/.todo-tui/config.json`:

```json
{
  "save_path": "/Users/your-username/.todo-tui",
  "storage_type": "local",
  "jira": {
    "enabled": false,
    "base_url": "https://your-company.atlassian.net",
    "email": "your-email@example.com",
    "api_token": "your-api-token",
    "project_key": "PROJ"
  }
}
```

### 📦 기존 데이터 마이그레이션

기존 프로젝트 디렉토리에서 데이터를 복사:

```bash
cp /Users/sun/Document/01_project/todo-cli/config.json ~/.todo-tui/
cp -r /Users/sun/todos ~/.todo-tui/
```

### 🤖 Claude MCP 연동

Claude Desktop에서 Todo 앱을 직접 제어할 수 있습니다.

#### 설치

1. Python 3.10+ 가상환경 생성 및 의존성 설치:

```bash
cd /Users/sun/Document/01_project/todo-cli
python3.12 -m venv .venv
source .venv/bin/activate
pip install mcp textual requests
```

2. Claude Desktop 설정 파일 업데이트 (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "todo-tui": {
      "command": "/Users/sun/Document/01_project/todo-cli/.venv/bin/python3",
      "args": ["/Users/sun/Document/01_project/todo-cli/todo_mcp_server.py"]
    }
  }
}
```

3. Claude Desktop 재시작

#### 사용 가능한 MCP 도구

| 도구 | 설명 |
|------|------|
| `todo_add` | 새 Todo 항목 추가 (Epic/Story/Task) |
| `todo_done` | 항목 완료 처리 |
| `todo_start` | 항목 진행중으로 변경 |
| `todo_list` | Todo 목록 조회 |
| `todo_get` | 특정 항목 상세 조회 |
| `todo_delete` | 항목 삭제 |
| `todo_update_description` | 설명 수정 |
| `todo_stats` | 통계 조회 |
| `todo_set_status` | 상태 직접 설정 |
| `season_list` | 시즌 목록 조회 |
| `season_current` | 현재 시즌 정보 |

#### 사용 예시

```
User: "로그인 기능 구현해줘"

Claude: [MCP 도구 호출]
1. todo_add("로그인 기능", type="epic")
   → Created epic id=10

2. todo_add("로그인 UI", type="story", parent_id=10)
   → Created story id=11

3. todo_add("로그인 API", type="story", parent_id=10)
   → Created story id=12

4. todo_add("로그인 버튼 구현", type="task", parent_id=11)
   → Created task id=13

[작업 진행 중...]
5. todo_start(13)
   → Status: in_progress

[작업 완료]
6. todo_done(13)
   → Status: done
```

### 🎨 아이콘 가이드

#### 타입 아이콘

| 타입 | 아이콘 | 설명 |
|------|--------|------|
| Epic | 📁 | 최상위 프로젝트 단위 |
| Story | 📖 | Epic 하위의 기능 단위 |
| Task | ✅ | 실제 수행할 작업 |

#### 상태 아이콘

| 상태 | 아이콘 | 설명 |
|------|--------|------|
| 대기 | ⬜ | 아직 시작하지 않음 |
| 진행중 | 🔄 | 현재 작업 중 |
| 완료 | ✅ | 작업 완료 |

#### 우선순위 아이콘

| 우선순위 | 아이콘 |
|---------|--------|
| 높음 | 🔴 |
| 보통 | 🟡 |
| 낮음 | 🟢 |

### 📋 요구사항

- Python 3.8+
- textual >= 0.40.0
- requests >= 2.28.0

### 📁 프로젝트 구조

```
todo-cli/
├── src/todo_tui/
│   ├── __init__.py
│   ├── main.py          # 메인 애플리케이션
│   └── jira_client.py   # Jira REST API 클라이언트
├── setup.py
├── pyproject.toml
└── README.md
```

### 🧪 테스트

```bash
python3 test_e2e.py
```

---

## English

### ✨ Introduction

**Todo TUI** is an interactive terminal-based todo management application.

It supports **Epic > Story > Task** hierarchy for project management, with a clean UI for tracking progress at a glance.

### 🎯 Key Features

| Feature | Description |
|---------|-------------|
| 🏗️ **Hierarchy** | Epic > Story > Task 3-level structure |
| 🔄 **Status Management** | Todo → In Progress → Done cycle |
| 📊 **In-Progress Display** | Shows in-progress items separately at top |
| 🎨 **Intuitive UI** | Emoji icons for status/type/priority |
| 💾 **Auto Save** | Automatic JSON data persistence |
| ⌨️ **Keyboard-First** | Full keyboard navigation |
| 📅 **Season Management** | Organize work by project/period |
| 🔗 **Jira Sync** | Bidirectional sync with Jira |
| 📈 **Reports** | Daily/weekly/season reports |

### 🚀 Installation

```bash
# Clone repository
git clone https://github.com/minjun-papa/todo-tui.git
cd todo-tui

# Install package
pip3 install .
```

#### PATH Setup (one-time)

```bash
echo 'export PATH="$HOME/Library/Python/3.9/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### ▶️ Run

```bash
todo
```

Or run directly without PATH:

```bash
python3 -m todo_tui.main
```

### ⌨️ Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Space` | Toggle check (To Do ↔ Done) |
| `s` | Change status (todo → in_progress → done → todo) |
| `a` | Add new item |
| `A` | Add child item |
| `d` | Delete (with children) |
| `e` | Expand all |
| `c` | Collapse all |
| `→` | Expand node |
| `←` | Collapse node |
| `S` | Season select |
| `r` | View report |
| `j` | Jira sync |
| `Ctrl+J` | Jira settings |
| `q` | Quit |

### 🔗 Jira Integration

#### Setup

1. Press `Ctrl+J` to open Jira settings
2. Enter your Jira credentials:
   - **Jira URL**: `https://your-company.atlassian.net`
   - **Email**: Your Jira account email
   - **API Token**: Generate at [Atlassian API tokens](https://id.atlassian.com/manage-profile/security/api-tokens)
   - **Project Key**: e.g., `PROJ`
3. Click "Test Connection" to verify
4. Click "Save" to save settings

#### Sync

- Press `j` to sync from Jira
- New todos automatically create Jira issues
- Status changes automatically update Jira issues

### 📁 Data Storage

- **Location**: `~/.todo-tui/`
- **Config**: `~/.todo-tui/config.json`
- **Todos**: `~/.todo-tui/todos.json`
- **Seasons**: `~/.todo-tui/seasons/`

### 📋 Requirements

- Python 3.8+
- textual >= 0.40.0
- requests >= 2.28.0

---

## 📄 License

MIT License - feel free to use and modify!

---

<div align="center">

Made with ❤️ by [minjun-papa](https://github.com/minjun-papa)

</div>
