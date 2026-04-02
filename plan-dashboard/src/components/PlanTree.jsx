/* PlanTree component */
(function() {
  var html = htm.bind(React.createElement);
  var useState = React.useState;

  function TreeNode(props) {
    var todo = props.todo;
    var todos = props.todos;
    var children = todos.filter(function(t) { return t.parent_id === todo.id; });
    var ref = useState(true);
    var expanded = ref[0];
    var setExpanded = ref[1];
    var statusIcon = todo.status === 'done' ? '\u2705' : todo.status === 'in_progress' ? '\uD83D\uDD04' : '\u2B1C';
    var typeIcon = todo.type === 'epic' ? '\uD83D\uDCC1' : todo.type === 'story' ? '\uD83D\uDCD6' : '\uD83D\uDCCC';
    var textClass = todo.status === 'done' ? 'done' : '';
    var toggleEl = children.length > 0
      ? html`<span class="tree-toggle" onClick=${function(e) { e.stopPropagation(); setExpanded(!expanded); }}>${expanded ? '\u25BC' : '\u25B6'}</span>`
      : html`<span class="tree-toggle"></span>`;
    var childEls = null;
    if (expanded && children.length > 0) {
      childEls = html`<div class="tree-node">${children.map(function(child) {
        return html`<${TreeNode} key=${child.id} todo=${child} todos=${todos} />`;
      })}</div>`;
    }
    return html`<div><div class="tree-row">${toggleEl}<span class="tree-icon">${typeIcon}</span><span class=${'tree-text ' + textClass}>${todo.content}</span><span class="tree-status">${statusIcon}</span></div>${childEls}</div>`;
  }

  function PlanTreeItem(props) {
    var plan = props.plan;
    var todos = props.todos;
    var onPlanClick = props.onPlanClick;
    var planTodos = todos.filter(function(t) { return t.plan_id === plan.id; });
    var rootTodos = planTodos.filter(function(t) { return t.parent_id === null; });
    var ref = useState(true);
    var expanded = ref[0];
    var setExpanded = ref[1];
    var total = planTodos.length;
    var done = planTodos.filter(function(t) { return t.status === 'done'; }).length;
    var rate = total > 0 ? Math.round((done / total) * 1000) / 10 : 0;
    var bc = plan.status === 'active' ? 'badge-active' : 'badge-completed';
    var childEls = null;
    if (expanded && rootTodos.length > 0) {
      childEls = html`<div class="tree-node root">${rootTodos.map(function(todo) {
        return html`<${TreeNode} key=${todo.id} todo=${todo} todos=${planTodos} />`;
      })}</div>`;
    }
    return html`<div style=${{ marginBottom: '16px' }}><div class="tree-row" style=${{ padding: '8px 10px', background: 'var(--surface)', borderRadius: 'var(--radius)', border: '1px solid var(--border)' }}><span class="tree-toggle" onClick=${function(e) { e.stopPropagation(); setExpanded(!expanded); }}>${expanded ? '\u25BC' : '\u25B6'}</span><span class="tree-icon">\uD83D\uDCCB</span><span class="tree-text" style=${{ fontWeight: 600, cursor: 'pointer' }} onClick=${function() { onPlanClick(plan.id); }}>${plan.name}</span><span class=${'badge ' + bc} style=${{ marginLeft: '8px' }}>${plan.status}</span><span class="tree-status">${rate}% (${done}/${total})</span></div>${childEls}</div>`;
  }

  window.PlanTree = function PlanTree(props) {
    var plans = props.plans;
    var todos = props.todos;
    var onPlanClick = props.onPlanClick;
    var activePlans = plans.filter(function(p) { return p.status === 'active'; });
    var completedPlans = plans.filter(function(p) { return p.status === 'completed'; });
    var unassignedTodos = todos.filter(function(t) { return !t.plan_id && !t.parent_id; });
    return html`<div class="tree-container"><h2 style=${{ fontSize: '16px', marginBottom: '16px' }}>Plan Tree</h2>${activePlans.map(function(plan) { return html`<${PlanTreeItem} key=${plan.id} plan=${plan} todos=${todos} onPlanClick=${onPlanClick} />`; })}${completedPlans.length > 0 && html`<div style=${{ marginTop: '24px' }}><h3 style=${{ color: 'var(--text-muted)', fontSize: '12px', marginBottom: '10px', textTransform: 'uppercase' }}>Completed Plans</h3>${completedPlans.map(function(plan) { return html`<${PlanTreeItem} key=${plan.id} plan=${plan} todos=${todos} onPlanClick=${onPlanClick} />`; })}</div>`}${unassignedTodos.length > 0 && html`<div style=${{ marginTop: '24px' }}><h3 style=${{ color: 'var(--text-muted)', fontSize: '12px', marginBottom: '10px', textTransform: 'uppercase' }}>Unassigned Tasks</h3><div class="tree-node root">${unassignedTodos.map(function(todo) { return html`<${TreeNode} key=${todo.id} todo=${todo} todos=${todos.filter(function(t) { return !t.plan_id; })} />`; })}</div></div>`}${plans.length === 0 && html`<div class="empty"><div class="empty-icon">\uD83C\uDF32</div><div class="empty-text">No plans to display</div></div>`}</div>`;
  };
})();
