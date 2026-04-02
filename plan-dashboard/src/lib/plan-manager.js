/* Plan CRUD helpers */

import { fetchPlans, createPlan as apiCreate, endPlan as apiEnd, updatePlan as apiUpdate, deletePlan as apiDelete, fetchTodos } from './data.js';

export async function listPlans(status) {
  return fetchPlans(status);
}

export async function createPlan({ name, working_dir, model, prompt }) {
  return apiCreate({ name, working_dir, model, prompt });
}

export async function endPlan(id) {
  return apiEnd(id);
}

export async function updatePlan(id, updates) {
  return apiUpdate(id, updates);
}

export async function removePlan(id) {
  return apiDelete(id);
}

export async function getPlanWithTodos(planId) {
  const [plan, todos] = await Promise.all([
    fetchPlans().then(plans => plans.find(p => p.id === planId)),
    fetchTodos({ plan_id: planId }),
  ]);
  if (!plan) return null;
  const total = todos.length;
  const done = todos.filter(t => t.status === 'done').length;
  return {
    ...plan,
    todos,
    stats: {
      total,
      done,
      in_progress: todos.filter(t => t.status === 'in_progress').length,
      todo: todos.filter(t => t.status === 'todo').length,
      completion_rate: total > 0 ? Math.round((done / total) * 1000) / 10 : 0,
    },
  };
}
