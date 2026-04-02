/* Dashboard component */
(function() {
  var html = htm.bind(React.createElement);
  var useMemo = React.useMemo;

  window.Dashboard = function Dashboard(props) {
    var plans = props.plans;
    var todos = props.todos;
    var onAdd = props.onAdd;
    var onPlanClick = props.onPlanClick;
    var onUpdate = props.onUpdate;

    var activePlans = useMemo(function() {
      return plans.filter(function(p) { return p.status === 'active'; });
    }, [plans]);

    var completedPlans = useMemo(function() {
      return plans.filter(function(p) { return p.status === 'completed'; });
    }, [plans]);

    var stats = useMemo(function() {
      return {
        active: activePlans.length,
        totalTodos: todos.length,
        doneTodos: todos.filter(function(t) { return t.status === 'done'; }).length,
        inProgressTodos: todos.filter(function(t) { return t.status === 'in_progress'; }).length,
      };
    }, [activePlans, todos]);

    function onEnd(id) { window.DataAccess.endPlan(id).then(onUpdate); }
    function onDelete(id) { window.DataAccess.deletePlan(id).then(onUpdate); }

    var activeCards = activePlans.map(function(plan) {
      var pt = todos.filter(function(t) { return t.plan_id === plan.id; });
      return html`<${PlanCard} key=${plan.id} plan=${plan} todos=${pt}
        onClick=${function() { onPlanClick(plan.id); }}
        onEnd=${function() { onEnd(plan.id); }}
        onDelete=${function() { onDelete(plan.id); }} />`;
    });

    var completedCards = completedPlans.map(function(plan) {
      var pt = todos.filter(function(t) { return t.plan_id === plan.id; });
      return html`<${PlanCard} key=${plan.id} plan=${plan} todos=${pt}
        onClick=${function() { onPlanClick(plan.id); }}
        onEnd=${function() { onEnd(plan.id); }}
        onDelete=${function() { onDelete(plan.id); }} />`;
    });

    return html`
      <div>
        <div class="dashboard-header">
          <h1>Plans</h1>
          <button class="btn btn-primary" onClick=${onAdd}>+ New Plan</button>
        </div>
        <div class="stats-bar">
          <div class="stat-card">
            <div class="stat-value active">${stats.active}</div>
            <div class="stat-label">Active Plans</div>
          </div>
          <div class="stat-card">
            <div class="stat-value progress">${stats.inProgressTodos}</div>
            <div class="stat-label">In Progress</div>
          </div>
          <div class="stat-card">
            <div class="stat-value done">${stats.doneTodos}</div>
            <div class="stat-label">Completed Tasks</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">${stats.totalTodos}</div>
            <div class="stat-label">Total Tasks</div>
          </div>
        </div>
        ${activePlans.length > 0 && html`
          <div>
            <h3 style=${{ color: 'var(--text-muted)', fontSize: '12px', marginBottom: '10px', textTransform: 'uppercase' }}>Active</h3>
            <div class="plan-grid">${activeCards}</div>
          </div>
        `}
        ${completedPlans.length > 0 && html`
          <div style=${{ marginTop: '24px' }}>
            <h3 style=${{ color: 'var(--text-muted)', fontSize: '12px', marginBottom: '10px', textTransform: 'uppercase' }}>Completed</h3>
            <div class="plan-grid">${completedCards}</div>
          </div>
        `}
        ${plans.length === 0 && html`
          <div class="empty">
            <div class="empty-icon">\uD83D\uDCCB</div>
            <div class="empty-text">No plans yet. Create your first plan!</div>
          </div>
        `}
      </div>
    `;
  };
})();
