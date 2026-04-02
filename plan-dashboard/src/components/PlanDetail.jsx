/* PlanDetail component */
(function() {
  var html = htm.bind(React.createElement);
  var useState = React.useState;
  var useMemo = React.useMemo;
  var useEffect = React.useEffect;

  function pCls(r) { return r < 30 ? 'low' : r < 70 ? 'mid' : 'high'; }

  function TodoRow(props) {
    var todo = props.todo, todos = props.todos, onUpdate = props.onUpdate;
    var children = todos.filter(function(t) { return t.parent_id === todo.id; });
    var ref = useState(true);
    var expanded = ref[0], setExpanded = ref[1];

    function toggleStatus(e) {
      e.stopPropagation();
      var next = todo.status === 'todo' ? 'in_progress' : todo.status === 'in_progress' ? 'done' : 'todo';
      window.DataAccess.setTodoStatus(todo.id, next).then(onUpdate);
    }

    var si = todo.status === 'done' ? '\u2705' : todo.status === 'in_progress' ? '\uD83D\uDD04' : '\u2B1C';
    var ti = todo.type === 'epic' ? '\uD83D\uDCC1' : todo.type === 'story' ? '\uD83D\uDCD6' : '\uD83D\uDCCC';
    var tc = todo.status === 'done' ? 'done' : '';

    var toggle = children.length > 0
      ? html`<span class="tree-toggle" onClick=${function(e){e.stopPropagation();setExpanded(!expanded)}}>${expanded?'\u25BC':'\u25B6'}</span>`
      : html`<span class="tree-toggle"></span>`;

    var childEls = null;
    if (expanded && children.length > 0) {
      childEls = html`<div class="tree-node">${children.map(function(c) {
        return html`<${TodoRow} key=${c.id} todo=${c} todos=${todos} onUpdate=${onUpdate} />`;
      })}</div>`;
    }

    return html`<div>
      <div class="tree-row">
        ${toggle}
        <span style=${{cursor:'pointer'}} onClick=${toggleStatus}>${si}</span>
        <span class="tree-icon">${ti}</span>
        <span class=${'tree-text '+tc}>${todo.content}</span>
      </div>
      ${childEls}
    </div>`;
  }

  window.PlanDetail = function PlanDetail(props) {
    var planId = props.planId, plans = props.plans, todos = props.todos, onBack = props.onBack, onUpdate = props.onUpdate;
    var plan = plans.find(function(p) { return p.id === planId; });
    var ref1 = useState(false), showAdd = ref1[0], setShowAdd = ref1[1];
    var ref2 = useState(''), newContent = ref2[0], setNewContent = ref2[1];
    var ref3 = useState('task'), newType = ref3[0], setNewType = ref3[1];
    var ref4 = useState([]), historyEntries = ref4[0], setHistoryEntries = ref4[1];
    var ref5 = useState(false), showAddHistory = ref5[0], setShowAddHistory = ref5[1];
    var ref6 = useState(''), newHistoryContent = ref6[0], setNewHistoryContent = ref6[1];
    var ref7 = useState('progress'), newHistoryType = ref7[0], setNewHistoryType = ref7[1];
    var ref8 = useState('assistant'), newHistoryRole = ref8[0], setNewHistoryRole = ref8[1];

    function loadHistory() {
      window.DataAccess.fetchHistory(planId).then(function(entries) {
        setHistoryEntries(entries);
      });
    }

    useEffect(function() {
      loadHistory();
    }, [planId]);

    function handleAddHistory(e) {
      e.preventDefault();
      if (!newHistoryContent.trim()) return;
      window.DataAccess.addHistory(planId, newHistoryContent.trim(), newHistoryRole, newHistoryType).then(function() {
        setNewHistoryContent('');
        setShowAddHistory(false);
        loadHistory();
      });
    }

    var sortedHistory = historyEntries.slice().sort(function(a, b) {
      return b.id - a.id;
    });

    var planTodos = useMemo(function() { return todos.filter(function(t) { return t.plan_id === planId; }); }, [todos, planId]);
    var rootTodos = useMemo(function() { return planTodos.filter(function(t) { return t.parent_id === null; }); }, [planTodos]);
    var stats = useMemo(function() {
      var total = planTodos.length;
      var done = planTodos.filter(function(t) { return t.status === 'done'; }).length;
      return { total: total, done: done, rate: total > 0 ? Math.round(done / total * 1000) / 10 : 0 };
    }, [planTodos]);

    if (!plan) {
      return html`<div>
        <button class="back-btn" onClick=${onBack}>\u2190 Back</button>
        <div class="empty"><div class="empty-icon">?</div><div class="empty-text">Plan not found</div></div>
      </div>`;
    }

    function handleAddTodo(e) {
      e.preventDefault();
      if (!newContent.trim()) return;
      window.DataAccess.addTodo({ content: newContent.trim(), type: newType, plan_id: planId }).then(function() {
        setNewContent(''); setShowAdd(false); onUpdate();
      });
    }

    function onEnd() { window.DataAccess.endPlan(planId).then(function() { onUpdate(); onBack(); }); }
    function onDelete() { window.DataAccess.deletePlan(planId).then(function() { onUpdate(); onBack(); }); }

    var bc = plan.status === 'active' ? 'badge-active' : plan.status === 'completed' ? 'badge-completed' : 'badge-cancelled';

    var addForm = null;
    if (showAdd) {
      addForm = html`<div style=${{background:'var(--surface)',border:'1px solid var(--primary)',borderRadius:'var(--radius)',padding:'12px 16px',marginBottom:'12px'}}>
        <form onSubmit=${handleAddTodo}>
          <div style=${{display:'flex',gap:'8px',marginBottom:'8px'}}>
            <select value=${newType} onChange=${function(e){setNewType(e.target.value)}} style=${{padding:'6px',background:'var(--bg)',border:'1px solid var(--border)',borderRadius:'4px',color:'var(--text)'}}>
              <option value="epic">Epic</option><option value="story">Story</option><option value="task">Task</option>
            </select>
            <input type="text" placeholder="Task content..." value=${newContent} onInput=${function(e){setNewContent(e.target.value)}} style=${{flex:1,padding:'6px 10px',background:'var(--bg)',border:'1px solid var(--border)',borderRadius:'4px',color:'var(--text)'}} />
          </div>
          <div style=${{display:'flex',justifyContent:'flex-end',gap:'6px'}}>
            <button type="button" class="btn btn-sm" onClick=${function(){setShowAdd(false)}}>Cancel</button>
            <button type="submit" class="btn btn-sm btn-primary">Add</button>
          </div>
        </form>
      </div>`;
    }

    var rootEls = rootTodos.map(function(todo) {
      return html`<${TodoRow} key=${todo.id} todo=${todo} todos=${planTodos} onUpdate=${onUpdate} />`;
    });

    return html`<div>
      <button class="back-btn" onClick=${onBack}>\u2190 Back to Dashboard</button>
      <div class="plan-detail">
        <div class="plan-detail-header">
          <div>
            <div class="plan-detail-name">${plan.name}</div>
            <div class="plan-detail-meta">
              <span class=${'badge '+bc}>${plan.status}</span>
              ${plan.working_dir&&html`<span>${plan.working_dir}</span>`}
              ${plan.model&&html`<span>${plan.model}</span>`}
              ${plan.started_at&&html`<span>Started: ${new Date(plan.started_at).toLocaleString('ko-KR')}</span>`}
            </div>
          </div>
          <div style=${{display:'flex',gap:'6px'}}>
            ${plan.status==='active'&&html`<button class="btn btn-sm" onClick=${onEnd}>Complete Plan</button>`}
            <button class="btn btn-sm btn-danger" onClick=${onDelete}>Delete</button>
          </div>
        </div>
        ${stats.total > 0 && html`<div style=${{marginTop:'12px'}}>
          <div class="progress-bar" style=${{height:'8px'}}>
            <div class=${'progress-bar-fill '+pCls(stats.rate)} style=${{width:stats.rate+'%'}}></div>
          </div>
          <div style=${{fontSize:'11px',color:'var(--text-muted)',marginTop:'4px'}}>${stats.rate}% (${stats.done}/${stats.total} tasks)</div>
        </div>`}
      </div>
      ${plan.prompt && html`<div style=${{background:'var(--surface)',border:'1px solid var(--border)',borderRadius:'var(--radius)',padding:'12px 16px',marginBottom:'16px',fontSize:'12px',color:'var(--text-muted)',whiteSpace:'pre-wrap'}}>
        <strong style=${{color:'var(--text)'}}>Prompt:</strong>${'\n'+plan.prompt}
      </div>`}
      <div style=${{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:'12px'}}>
        <h3 style=${{fontSize:'14px'}}>Tasks</h3>
        ${plan.status==='active'&&html`<button class="btn btn-sm btn-primary" onClick=${function(){setShowAdd(!showAdd)}}>+ Add Task</button>`}
      </div>
      ${addForm}
      <div class="tree-node root">${rootEls}</div>
      ${rootTodos.length===0&&html`<div class="empty" style=${{padding:'30px'}}><div class="empty-text">No tasks in this plan</div></div>`}
      <div style=${{marginTop:'24px'}}>
        <div style=${{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:'12px'}}>
          <h3 style=${{fontSize:'14px'}}>Session History</h3>
          ${plan.status==='active'&&html`<button class="btn btn-sm btn-primary" onClick=${function(){setShowAddHistory(!showAddHistory)}}>+ Log Entry</button>`}
        </div>
        ${showAddHistory && html`<div style=${{background:'var(--surface)',border:'1px solid var(--primary)',borderRadius:'var(--radius)',padding:'12px 16px',marginBottom:'12px'}}>
          <form onSubmit=${handleAddHistory}>
            <div style=${{display:'flex',gap:'8px',marginBottom:'8px'}}>
              <select value=${newHistoryRole} onChange=${function(e){setNewHistoryRole(e.target.value)}} style=${{padding:'6px',background:'var(--bg)',border:'1px solid var(--border)',borderRadius:'4px',color:'var(--text)'}}>
                <option value="assistant">Assistant</option>
                <option value="user">User</option>
              </select>
              <select value=${newHistoryType} onChange=${function(e){setNewHistoryType(e.target.value)}} style=${{padding:'6px',background:'var(--bg)',border:'1px solid var(--border)',borderRadius:'4px',color:'var(--text)'}}>
                <option value="progress">Progress</option>
                <option value="note">Note</option>
                <option value="error">Error</option>
                <option value="decision">Decision</option>
              </select>
            </div>
            <div style=${{display:'flex',gap:'8px',marginBottom:'8px'}}>
              <input type="text" placeholder="Log message..." value=${newHistoryContent} onInput=${function(e){setNewHistoryContent(e.target.value)}} style=${{flex:1,padding:'6px 10px',background:'var(--bg)',border:'1px solid var(--border)',borderRadius:'4px',color:'var(--text)'}} />
            </div>
            <div style=${{display:'flex',justifyContent:'flex-end',gap:'6px'}}>
              <button type="button" class="btn btn-sm" onClick=${function(){setShowAddHistory(false)}}>Cancel</button>
              <button type="submit" class="btn btn-sm btn-primary">Add</button>
            </div>
          </form>
        </div>`}
        ${sortedHistory.length > 0 ? html`<div style=${{display:'flex',flexDirection:'column',gap:'0'}}>
          ${sortedHistory.map(function(entry) {
            var roleIcon = entry.role === 'user' ? '\uD83D\uDC64' : '\uD83E\uDD16';
            var typeColor = entry.entry_type === 'progress' ? 'var(--primary)' : entry.entry_type === 'error' ? '#e74c3c' : entry.entry_type === 'decision' ? '#9b59b6' : 'var(--text-muted)';
            var typeLabel = entry.entry_type || 'progress';
            var timeStr = entry.created_at ? new Date(entry.created_at).toLocaleString('ko-KR') : '';
            return html`<div style=${{display:'flex',gap:'10px',padding:'10px 12px',borderBottom:'1px solid var(--border)',alignItems:'flex-start'}}>
              <span style=${{fontSize:'16px',flexShrink:0}}>${roleIcon}</span>
              <div style=${{flex:1,minWidth:0}}>
                <div style=${{display:'flex',gap:'8px',alignItems:'center',marginBottom:'4px'}}>
                  <span style=${{fontSize:'11px',padding:'1px 6px',borderRadius:'3px',background:typeColor,color:'#fff',fontWeight:500}}>${typeLabel}</span>
                  <span style=${{fontSize:'11px',color:'var(--text-muted)'}}>${timeStr}</span>
                </div>
                <div style=${{fontSize:'13px',color:'var(--text)',whiteSpace:'pre-wrap',wordBreak:'break-word'}}>${entry.content}</div>
              </div>
            </div>`;
          })}
        </div>` : html`<div class="empty" style=${{padding:'20px'}}><div class="empty-text">No session history yet</div></div>`}
      </div>
    </div>`;
  };
})();
