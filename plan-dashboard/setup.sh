#!/bin/bash
# Plan Dashboard + Todo MCP Server Setup
# 어느 컴퓨터에서든 실행하면 자동으로 세팅됩니다.
#
# 사용법:
#   git clone https://github.com/minjun-papa/todo-tui.git
#   cd todo-tui/plan-dashboard && bash setup.sh

set -e

# --- 설정 ---
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TODO_TUI_DIR="$(dirname "$SCRIPT_DIR")"
PLAN_DASH_DIR="$SCRIPT_DIR"
TODO_DATA_DIR="$HOME/todos"
CLAUDE_DIR="$HOME/.claude"

echo "========================================="
echo "  Plan Dashboard Setup"
echo "========================================="
echo ""
echo "todo-tui:    $TODO_TUI_DIR"
echo "dashboard:   $PLAN_DASH_DIR"
echo "data:        $TODO_DATA_DIR"
echo ""

# --- 1. 데이터 디렉토리 ---
echo "[1/6] 데이터 디렉토리 생성..."
mkdir -p "$TODO_DATA_DIR"
if [ ! -f "$TODO_DATA_DIR/plans.json" ]; then
  echo '[]' > "$TODO_DATA_DIR/plans.json"
  echo "  created plans.json"
fi
if [ ! -f "$TODO_DATA_DIR/todos.json" ]; then
  echo '[]' > "$TODO_DATA_DIR/todos.json"
  echo "  created todos.json"
fi

# --- 2. Python venv + deps ---
echo "[2/6] Python 가상환경 설정..."
if [ ! -d "$TODO_TUI_DIR/.venv" ]; then
  python3 -m venv "$TODO_TUI_DIR/.venv" 2>/dev/null || python3.12 -m venv "$TODO_TUI_DIR/.venv"
  echo "  created .venv"
fi
"$TODO_TUI_DIR/.venv/bin/pip" install -r "$TODO_TUI_DIR/requirements.txt" -q
echo "  dependencies installed"

# --- 3. MCP 서버 등록 ---
echo "[3/6] MCP 서버 등록 (~/.mcp.json)..."
MCP_FILE="$HOME/.mcp.json"
VENV_PYTHON="$TODO_TUI_DIR/.venv/bin/python3"
MCP_SERVER="$TODO_TUI_DIR/todo_mcp_server.py"

if [ -f "$MCP_FILE" ]; then
  "$TODO_TUI_DIR/.venv/bin/python3" -c "
import json

with open('$MCP_FILE') as f:
    config = json.load(f)

config['todo'] = {
    'type': 'stdio',
    'command': '$VENV_PYTHON',
    'args': ['$MCP_SERVER']
}

with open('$MCP_FILE', 'w') as f:
    json.dump(config, f, indent=2)

print('  todo MCP server registered')
"
else
  cat > "$MCP_FILE" << EOFJSON
{
  "todo": {
    "type": "stdio",
    "command": "$VENV_PYTHON",
    "args": ["$MCP_SERVER"]
  }
}
EOFJSON
  echo "  created .mcp.json with todo server"
fi

# --- 4. CLAUDE.md 설정 ---
echo "[4/6] CLAUDE.md 자동 plan 지시어 설정..."
mkdir -p "$CLAUDE_DIR"
CLAUDE_MD="$CLAUDE_DIR/CLAUDE.md"

PLAN_BLOCK='## 자동 Plan 관리
사용자가 새로운 작업을 요청하면, 작업 시작 전에 반드시 아래 절차를 따른다:
1. 작업을 분석해서 plan_create 툴로 새 Plan을 생성한다
   - name: 작업의 핵심을 요약한 이름
   - working_dir: 현재 작업 디렉토리
   - model: 현재 사용 중인 모델명
   - prompt: 사용자의 원본 요청을 그대로 입력
2. 작업을 세분화해서 todo_add 툴로 task들을 추가한다 (plan_id 지정)
   - Epic > Story > Task 계층으로 구성
3. 각 작업 단계를 시작할 때 todo_start로 in_progress로 변경
4. 완료 시 todo_done으로 변경
5. 전체 작업이 끝나면 plan_end 툴로 plan을 completed로 변경'

if [ -f "$CLAUDE_MD" ]; then
  if grep -q "자동 Plan 관리" "$CLAUDE_MD" 2>/dev/null; then
    echo "  already configured"
  else
    echo "" >> "$CLAUDE_MD"
    echo "$PLAN_BLOCK" >> "$CLAUDE_MD"
    echo "  appended plan instructions"
  fi
else
  echo "$PLAN_BLOCK" > "$CLAUDE_MD"
  echo "  created CLAUDE.md with plan instructions"
fi

# --- 5. Electron dashboard npm install ---
echo "[5/6] Electron dashboard 의존성 설치..."
cd "$PLAN_DASH_DIR"
npm install --silent 2>/dev/null || npm install
echo "  npm dependencies installed"

# --- 6. 완료 ---
echo "[6/6] 설정 완료!"
echo ""
echo "========================================="
echo "  Setup Complete!"
echo "========================================="
echo ""
echo "Usage:"
echo "  1. Start dashboard:"
echo "     cd $PLAN_DASH_DIR && npm start"
echo ""
echo "  2. Open a new Claude Code session"
echo "     -> Request a task and Plan is auto-created"
echo "     -> Dashboard shows real-time progress"
echo ""
