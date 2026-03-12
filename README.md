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

### 📸 스크린샷

```
┌─────────────────────────────────────────────────────────────┐
│ 📊 전체: 5 | 📋 대기: 2 | 🔄 진행중: 2 | ✅ 완료: 1         │
│ 📁 Epic: 1 | 📖 Story: 2 | ✅ Task: 2                       │
├─────────────────────────────────────────────────────────────┤
│ 🔄 진행중 (2): 로그인 구현 (task) | API 개발 (task)         │
├─────────────────────────────────────────────────────────────┤
│ 📋 Todo List                                                │
│ ├─ ○ 📁 🟡 [general] 프로젝트 개발                          │
│ │  ├─ ◐ 📖 🟡 [general] 백엔드 개발                         │
│ │  │  └─ ◐ ✅ 🟡 [general] API 개발                         │
│ │  └─ ● 📖 🟢 [general] 프론트엔드 개발                      │
│ │     └─ ● ✅ 🔴 [general] 로그인 구현 (due: 2024-12-31)    │
└─────────────────────────────────────────────────────────────┘
```

### 🚀 빠른 시작

#### 설치

```bash
# 저장소 클론
git clone https://github.com/minjun-papa/todo-tui.git
cd todo-tui

# 의존성 설치
pip install textual
```

#### 실행

```bash
python3 todo.py
```

#### Alias 설정 (선택사항)

```bash
# ~/.zshrc 또는 ~/.bashrc에 추가
echo "alias todo='python3 $(pwd)/todo.py'" >> ~/.zshrc
source ~/.zshrc

# 이제 어디서든
todo
```

### ⌨️ 키보드 단축키

#### 메인 화면

| 키 | 기능 |
|----|------|
| `a` | 새 항목 추가 |
| `A` | 하위 항목 추가 (선택된 항목 아래) |
| `s` | 상태 변경 (대기 → 진행중 → 완료 → 대기) |
| `d` | 삭제 (하위 항목도 함께 삭제) |
| `e` | 전체 펼치기 |
| `c` | 전체 접기 |
| `→` | 선택 노드 펼치기 |
| `←` | 선택 노드 접기 |
| `↑/↓` | 항목 탐색 |
| `q` | 앱 종료 |

#### 추가 화면

| 키 | 기능 |
|----|------|
| `Tab` | 다음 필드로 이동 |
| `Shift+Tab` | 이전 필드로 이동 |
| `Enter` | 저장 |
| `Escape` | 취소 |

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
| 대기 | ○ | 아직 시작하지 않음 |
| 진행중 | ◐ | 현재 작업 중 |
| 완료 | ● | 작업 완료 |

#### 우선순위 아이콘

| 우선순위 | 아이콘 |
|---------|--------|
| 높음 | 🔴 |
| 보통 | 🟡 |
| 낮음 | 🟢 |

### 📁 데이터 저장

- **저장 위치**: `~/todos/todos.json`
- **설정 파일**: `config.json`에서 경로 변경 가능
- **자동 변환**: 기존 `completed` 필드는 자동으로 `status`로 변환

### 🧪 테스트

```bash
python3 test_e2e.py
```

### 📋 요구사항

- Python 3.8+
- [textual](https://github.com/Textualize/textual) 라이브러리

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

### 🚀 Quick Start

```bash
# Clone repository
git clone https://github.com/minjun-papa/todo-tui.git
cd todo-tui

# Install dependency
pip install textual

# Run
python3 todo.py
```

### ⌨️ Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `a` | Add new item |
| `A` | Add child item |
| `s` | Change status (todo → in_progress → done → todo) |
| `d` | Delete (with children) |
| `e` | Expand all |
| `c` | Collapse all |
| `→` | Expand node |
| `←` | Collapse node |
| `↑/↓` | Navigate |
| `q` | Quit |

### 📋 Requirements

- Python 3.8+
- [textual](https://github.com/Textualize/textual) library

---

## 📄 License

MIT License - feel free to use and modify!

---

<div align="center">

Made with ❤️ by [minjun-papa](https://github.com/minjun-papa)

</div>
