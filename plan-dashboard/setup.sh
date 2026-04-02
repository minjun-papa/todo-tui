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
if [ ! -f "$TODO_DATA_DIR/history.json" ]; then
  echo '[]' > "$TODO_DATA_DIR/history.json"
  echo "  created history.json"
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

PLAN_BLOCK='## Plan 관리 (명령어 기반)
사용자가 명시적으로 다음과 같이 요청할 때만 plan을 생성하고 관리:
- "/plan", "plan 시작", "계획 세워" 등으로 요청 시:
  1. plan_create 툴로 Plan 생성 (name, working_dir, model, prompt)
  2. todo_add 툴로 task 추가 (plan_id 지정, Epic > Story > Task)
  3. 각 단계 시작 시 todo_start, 완료 시 todo_done
  4. 작업 진행 중 plan_log 툴로 중요 결정/이슈/진행 상황 기록
  5. 전체 완료 후 plan_end 툴로 Plan 종료'

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
echo "     -> Request a task and Plan is auto-created"

echo ""
