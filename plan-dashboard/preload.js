const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('api', {
  // Plans
  planList: (status) => ipcRenderer.invoke('plan:list', status),
  planGet: (id) => ipcRenderer.invoke('plan:get', id),
  planCreate: (data) => ipcRenderer.invoke('plan:create', data),
  planEnd: (id) => ipcRenderer.invoke('plan:end', id),
  planUpdate: (id, updates) => ipcRenderer.invoke('plan:update', id, updates),
  planDelete: (id) => ipcRenderer.invoke('plan:delete', id),

  // Todos
  todoList: (filters) => ipcRenderer.invoke('todo:list', filters),
  todoGet: (id) => ipcRenderer.invoke('todo:get', id),
  todoAdd: (data) => ipcRenderer.invoke('todo:add', data),
  todoSetStatus: (id, status) => ipcRenderer.invoke('todo:setStatus', id, status),
  todoDelete: (id) => ipcRenderer.invoke('todo:delete', id),

  // File watching
  watchStart: () => ipcRenderer.invoke('watch:start'),
  watchStop: () => ipcRenderer.invoke('watch:stop'),
  onDataChanged: (callback) => {
    ipcRenderer.on('data:changed', () => callback());
  },
});
