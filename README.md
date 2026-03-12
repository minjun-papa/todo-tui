# Todo TUI

터미널에서 인터랙티브하게 사용할 수 있는 TUI 기반 Todo 앱입니다. Python의 `textual` 라이브러리를 사용하여 만들어졌습니다.

## 기능

### 계층 구조
- **Epic** > **Story** > **Task** 3단계 계층 구조 지원
- 트리뷰로 펼치기/접기 가능

### 상태 관리
- **대기** - ○ 아이콘
- **진행중** - ◐ 아이콘
- **완료** - ● 아이콘
- 진행중인 항목은 상단에 별도 표시

### 기타 기능
- 우선순위 (높음/보통/낮음)
- 마감일 설정
- 데이터 JSON 저장

## 키보드 단축키

| 키 | 기능 |
|----|------|
| `a` | 새 항목 추가 |
| `A` | 하위 항목 추가 (선택된 항목 아래) |
| `s` | 상태 변경 (대기→진행중→완료→대기) |
| `d` | 삭제 (하위 항목 포함) |
| `e` | 전체 펼치기 |
| `c` | 전체 접기 |
| `→` | 노드 펼치기 |
| `←` | 노드 접기 |
| `↑/↓` | 항목 탐색 |
| `Tab` | 입력 필드 이동 |
| `Enter` | 추가 화면에서 저장 |
| `Escape` | 추가 화면 닫기 |
| `q` | 앱 종료 |

## 설치

### 1. 저장소 클론

```bash
git clone https://github.com/minjun-papa/todo-tui.git
cd todo-tui
```

### 2. 의존성 설치

```bash
pip install textual
```

### 3. 실행

```bash
python3 todo.py
```

### 4. alias 설정 (선택사항)

`~/.zshrc` 또는 `~/.bashrc`에 추가:

```bash
alias todo='python3 /path/to/todo-tui/todo.py'
```

## 사용법

### 항목 추가
1. `a` 키로 최상위 항목 추가 (Epic)
2. 항목 선택 후 `A` 키로 하위 항목 추가 (Story/Task)
3. 유형, 내용 입력 (우선순위, 마감일은 선택사항)

### 상태 변경
- 항목 선택 후 `s` 키로 상태 순환

### 삭제
- `d` 키로 삭제 (하위 항목도 함께 삭제됨)

## 데이터 저장

- 저장 위치: `~/todos/todos.json`
- `config.json`에서 경로 변경 가능
- 기존 `completed` 필드 데이터는 자동으로 `status`로 변환

## 파일 구조

```
todo-tui/
├── todo.py          # 메인 실행 파일
├── test_e2e.py      # E2E 테스트
├── README.md        # 문서
├── config.json      # 설정 파일
└── .gitignore
```

## 아이콘

### 타입
| 타입 | 아이콘 |
|------|--------|
| Epic | 📁 |
| Story | 📖 |
| Task | ✅ |

### 우선순위
| 우선순위 | 아이콘 |
|---------|--------|
| High | 🔴 |
| Medium | 🟡 |
| Low | 🟢 |

### 상태
| 상태 | 아이콘 |
|------|--------|
| 대기 | ○ |
| 진행중 | ◐ |
| 완료 | ● |

## 테스트

```bash
python3 test_e2e.py
```

## 요구사항

- Python 3.8+
- textual 라이브러리

## 라이선스

MIT License
