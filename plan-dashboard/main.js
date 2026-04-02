const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const fs = require('fs');
const os = require('os');

const TODO_DIR = path.join(os.homedir(), 'todos');
const PLANS_FILE = path.join(TODO_DIR, 'plans.json');
const TODOS_FILE = path.join(TODO_DIR, 'todos.json');

function readJsonFile(filePath) {
  try {
    if (!fs.existsSync(filePath)) return [];
    const data = fs.readFileSync(filePath, 'utf-8');
    return JSON.parse(data);
  } catch {
    return [];
  }
}

function writeJsonFile(filePath, data) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, JSON.stringify(data, null, 2), 'utf-8');
}

let mainWindow;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    titleBarStyle: 'hiddenInset',
    trafficLightPosition: { x: 16, y: 18 },
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  mainWindow.loadFile(path.join(__dirname, 'src', 'index.html'));
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow();
});

// --- Plan IPC ---
ipcMain.handle('plan:list', (_e, status) => {
  const plans = readJsonFile(PLANS_FILE);
  if (status) return plans.filter(p => p.status === status);
  return plans;
});

ipcMain.handle('plan:get', (_e, id) => {
  const plans = readJsonFile(PLANS_FILE);
  return plans.find(p => p.id === id) || null;
});

ipcMain.handle('plan:create', (_e, planData) => {
  const plans = readJsonFile(PLANS_FILE);
  const newId = plans.reduce((max, p) => Math.max(max, p.id), 0) + 1;
  const plan = {
    id: newId,
    name: planData.name,
    status: 'active',
    source: planData.source || 'dashboard',
    working_dir: planData.working_dir || null,
    model: planData.model || null,
    prompt: planData.prompt || null,
    started_at: new Date().toISOString().slice(0, 19),
    ended_at: null,
    metadata: planData.metadata || {},
  };
  plans.push(plan);
  writeJsonFile(PLANS_FILE, plans);
  return plan;
});

ipcMain.handle('plan:end', (_e, id) => {
  const plans = readJsonFile(PLANS_FILE);
  const plan = plans.find(p => p.id === id);
  if (plan) {
    plan.status = 'completed';
    plan.ended_at = new Date().toISOString().slice(0, 19);
    writeJsonFile(PLANS_FILE, plans);
  }
  return plan || null;
});

ipcMain.handle('plan:update', (_e, id, updates) => {
  const plans = readJsonFile(PLANS_FILE);
  const plan = plans.find(p => p.id === id);
  if (plan) {
    Object.assign(plan, updates);
    writeJsonFile(PLANS_FILE, plans);
  }
  return plan || null;
});

ipcMain.handle('plan:delete', (_e, id) => {
  let plans = readJsonFile(PLANS_FILE);
  const len = plans.length;
  plans = plans.filter(p => p.id !== id);
  writeJsonFile(PLANS_FILE, plans);
  return plans.length < len;
});

// --- Todo IPC ---
ipcMain.handle('todo:list', (_e, filters) => {
  const todos = readJsonFile(TODOS_FILE);
  if (!filters) return todos;
  return todos.filter(t => {
    if (filters.plan_id !== undefined && t.plan_id !== filters.plan_id) return false;
    if (filters.status && t.status !== filters.status) return false;
    if (filters.type && t.type !== filters.type) return false;
    return true;
  });
});

ipcMain.handle('todo:get', (_e, id) => {
  const todos = readJsonFile(TODOS_FILE);
  return todos.find(t => t.id === id) || null;
});

ipcMain.handle('todo:add', (_e, todoData) => {
  const todos = readJsonFile(TODOS_FILE);
  const newId = todos.reduce((max, t) => Math.max(max, t.id), 0) + 1;
  const todo = {
    id: newId,
    content: todoData.content,
    type: todoData.type || 'task',
    category: todoData.category || 'general',
    priority: todoData.priority || 'medium',
    due_date: todoData.due_date || null,
    status: 'todo',
    created_at: new Date().toISOString().slice(0, 10),
    completed_at: null,
    parent_id: todoData.parent_id || null,
    season_id: todoData.season_id || null,
    plan_id: todoData.plan_id || null,
    jira_key: null,
    jira_id: null,
    description: todoData.description || null,
    order: todos.filter(t => t.parent_id === (todoData.parent_id || null)).length,
  };
  todos.push(todo);
  writeJsonFile(TODOS_FILE, todos);
  return todo;
});

ipcMain.handle('todo:setStatus', (_e, id, status) => {
  const todos = readJsonFile(TODOS_FILE);
  const todo = todos.find(t => t.id === id);
  if (todo) {
    todo.status = status;
    if (status === 'done') todo.completed_at = new Date().toISOString().slice(0, 10);
    else if (status === 'todo') todo.completed_at = null;
    writeJsonFile(TODOS_FILE, todos);
  }
  return todo || null;
});

ipcMain.handle('todo:delete', (_e, id) => {
  let todos = readJsonFile(TODOS_FILE);
  const idsToDelete = new Set([id]);
  let changed = true;
  while (changed) {
    changed = false;
    for (const t of todos) {
      if (idsToDelete.has(t.parent_id) && !idsToDelete.has(t.id)) {
        idsToDelete.add(t.id);
        changed = true;
      }
    }
  }
  const len = todos.length;
  todos = todos.filter(t => !idsToDelete.has(t.id));
  writeJsonFile(TODOS_FILE, todos);
  return todos.length < len;
});

// --- File Watch (polling) ---
let watchers = {};

ipcMain.handle('watch:start', (_e) => {
  if (watchers.interval) return;
  let lastPlansMtime = 0;
  let lastTodosMtime = 0;
  watchers.interval = setInterval(() => {
    try {
      const plansMtime = fs.existsSync(PLANS_FILE) ? fs.statSync(PLANS_FILE).mtimeMs : 0;
      const todosMtime = fs.existsSync(TODOS_FILE) ? fs.statSync(TODOS_FILE).mtimeMs : 0;
      if (plansMtime !== lastPlansMtime || todosMtime !== lastTodosMtime) {
        lastPlansMtime = plansMtime;
        lastTodosMtime = todosMtime;
        if (mainWindow && !mainWindow.isDestroyed()) {
          mainWindow.webContents.send('data:changed');
        }
      }
    } catch { /* ignore */ }
  }, 2000);
});

ipcMain.handle('watch:stop', () => {
  if (watchers.interval) {
    clearInterval(watchers.interval);
    watchers = {};
  }
});
