/* PlanCard component */
(function() {
  var html = htm.bind(React.createElement);
  var useMemo = React.useMemo;

  function formatDuration(startedAt, endedAt) {
    if (!startedAt) return '';
    var start = new Date(startedAt);
    var end = endedAt ? new Date(endedAt) : new Date();
    var diffMs = end - start;
    var minutes = Math.floor(diffMs / 60000);
    if (minutes < 60) return minutes + 'm';
    var hours = Math.floor(minutes / 60);
    var rm = minutes % 60;
    if (hours < 24) return hours + 'h ' + rm + 'm';
    return Math.floor(hours / 24) + 'd ' + (hours % 24) + 'h';
  }

  function pClass(rate) {
    if (rate < 30) return 'low';
    if (rate < 70) return 'mid';
    return 'high';
  }

  window.PlanCard = function PlanCard(props) {
    var plan = props.plan;
    var todos = props.todos;

    var stats = useMemo(function() {
      var total = todos.length;
      var done = todos.filter(function(t) { return t.status === 'done'; }).length;
      return {
        total: total,
        done: done,
        in_progress: todos.filter(function(t) { return t.status === 'in_progress'; }).length,
        todo: todos.filter(function(t) { return t.status === 'todo'; }).length,
        completion_rate: total > 0 ? Math.round((done / total) * 1000) / 10 : 0,
      };
    }, [todos]);

    var bc = plan.status === 'active' ? 'badge-active'
      : plan.status === 'completed' ? 'badge-completed' : 'badge-cancelled';
    var dirDisplay = plan.working_dir ? plan.working_dir.split('/').slice(-2).join('/') : '';

    return html`
      <div class="plan-card" onClick=${props.onClick}>
        <div class="plan-card-header">
          <div class="plan-card-name">${plan.name}</div>
          <span class=${'badge ' + bc}>${plan.status}</span>
        </div>
        <div class="plan-card-meta">
          ${dirDisplay && html`<span title=${plan.working_dir}>${dirDisplay}</span>`}
          ${plan.model && html`<span>${plan.model}</span>`}
          <span>${formatDuration(plan.started_at, plan.ended_at)}</span>
        </div>
        ${stats.total > 0 && html`
          <div>
            <div class="progress-bar">
              <div class=${'progress-bar-fill ' + pClass(stats.completion_rate)} style=${{ width: stats.completion_rate + '%' }}></div>
            </div>
            <div class="plan-card-stats">
              <span>${stats.completion_rate}%</span>
              <span>${stats.done}/${stats.total} tasks</span>
            </div>
          </div>
        `}
        <div class="plan-card-actions" onClick=${function(e) { e.stopPropagation(); }}>
          ${plan.status === 'active' && html`
            <button class="btn btn-sm" onClick=${props.onEnd}>Complete</button>
          `}
          <button class="btn btn-sm btn-danger" onClick=${props.onDelete}>Delete</button>
        </div>
      </div>
    `;
  };
})();
