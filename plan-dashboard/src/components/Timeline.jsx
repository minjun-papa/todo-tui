/* Timeline component */
(function() {
  var html = htm.bind(React.createElement);
  var useMemo = React.useMemo;

  function formatTime(isoStr) {
    if (!isoStr) return '';
    var d = new Date(isoStr);
    return d.toLocaleString('ko-KR', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  }

  function formatDuration(sa, ea) {
    if (!sa) return '';
    var s = new Date(sa), e = ea ? new Date(ea) : new Date();
    var m = Math.floor((e - s) / 60000);
    if (m < 60) return m + 'm';
    var h = Math.floor(m / 60);
    if (h < 24) return h + 'h ' + (m % 60) + 'm';
    return Math.floor(h / 24) + 'd ' + (h % 24) + 'h';
  }

  function pCls(r) { return r < 30 ? 'low' : r < 70 ? 'mid' : 'high'; }

  window.Timeline = function Timeline(props) {
    var plans = props.plans, todos = props.todos, onPlanClick = props.onPlanClick;
    var sorted = useMemo(function() {
      return [].concat(plans).sort(function(a, b) {
        return (new Date(b.started_at || 0)) - (new Date(a.started_at || 0));
      });
    }, [plans]);

    var items = sorted.map(function(p) {
      var pt = todos.filter(function(t) { return t.plan_id === p.id; });
      var total = pt.length;
      var done = pt.filter(function(t) { return t.status === 'done'; }).length;
      var rate = total > 0 ? Math.round(done / total * 1000) / 10 : 0;
      var isC = p.status === 'completed';
      return html`<div key=${p.id} class=${'timeline-item' + (isC ? ' completed' : '')} style=${{cursor:'pointer'}} onClick=${function(){onPlanClick(p.id)}}>
        <div class="timeline-time">${formatTime(p.started_at)}${p.ended_at?' -> '+formatTime(p.ended_at):' (ongoing)'}</div>
        <div class="timeline-name">${p.name}</div>
        <div class="timeline-meta">
          ${p.model&&html`<span>${p.model}</span>`}
          <span>${formatDuration(p.started_at, p.ended_at)}</span>
          <span>${p.source||''}</span>
        </div>
        ${total>0&&html`<div class="timeline-progress">
          <div class="progress-bar">
            <div class=${'progress-bar-fill '+pCls(rate)} style=${{width:rate+'%'}}></div>
          </div>
          <div style=${{fontSize:'11px',color:'var(--text-muted)',marginTop:'4px'}}>${rate}% (${done}/${total})</div>
        </div>`}
      </div>`;
    });

    return html`<div>
      <h2 style=${{fontSize:'16px',marginBottom:'16px'}}>Timeline</h2>
      ${sorted.length===0&&html`<div class="empty"><div class="empty-icon">\u23F1</div><div class="empty-text">No plans in timeline</div></div>`}
      <div class="timeline">${items}</div>
    </div>`;
  };
})();
