/* Data access helpers - uses window.api from preload.js */

window.DataAccess = {
  async fetchPlans(status) {
    return window.api.planList(status || undefined);
  },

  async fetchPlan(id) {
    return window.api.planGet(id);
  },

  async createPlan(data) {
    return window.api.planCreate(data);
  },

  async endPlan(id) {
    return window.api.planEnd(id);
  },

  async updatePlan(id, updates) {
    return window.api.planUpdate(id, updates);
  },

  async deletePlan(id) {
    return window.api.planDelete(id);
  },

  async fetchTodos(filters) {
    return window.api.todoList(filters || undefined);
  },

  async addTodo(data) {
    return window.api.todoAdd(data);
  },

  async setTodoStatus(id, status) {
    return window.api.todoSetStatus(id, status);
  },

  async deleteTodo(id) {
    return window.api.todoDelete(id);
  },

  startWatching(callback) {
    window.api.watchStart();
    window.api.onDataChanged(callback);
  },

  stopWatching() {
    window.api.watchStop();
  },
};
