/* App - main application */
(function() {
  var html = htm.bind(React.createElement);
  var useState = React.useState;
  var useEffect = React.useEffect;
  var useCallback = React.useCallback;

  var TABS = [
    { key: 'dashboard', label: 'Dashboard' },
    { key: 'tree', label: 'Plan Tree' },
    { key: 'timeline', label: 'Timeline' },
  ];

  function App() {
    var ref1 = useState('dashboard'), activeTab = ref1[0], setActiveTab = ref1[1];
    var ref2 = useState([]), plans = ref2[0], setPlans = ref2[1];
    var ref3 = useState([]), todos = ref3[0], setTodos = ref3[1];
    var ref4 = useState(false), showAddModal = ref4[0], setShowAddModal = ref4[1];
    var ref5 = useState(null), selectedPlanId = ref5[0], setSelectedPlanId = ref5[1];

    var loadData = useCallback(function() {
      return Promise.all([
        window.DataAccess.fetchPlans(),
        window.DataAccess.fetchTodos()
      ]).then(function(results) {
        setPlans(results[0]);
        setTodos(results[1]);
      });
    }, []);

    useEffect(function() {
      loadData();
      window.DataAccess.startWatching(loadData);
      return function() { window.DataAccess.stopWatching(); };
    }, [loadData]);

    function onPlanClick(planId) {
      setSelectedPlanId(planId);
    }

    function goBack() {
      setSelectedPlanId(null);
    }

    if (selectedPlanId !== null) {
      return html`
        <div class="app">
          <div class="titlebar">Plan Dashboard</div>
          <div class="content">
            <${PlanDetail} planId=${selectedPlanId} plans=${plans} todos=${todos} onBack=${goBack} onUpdate=${loadData} />
          </div>
        </div>
      `;
    }

    return html`
      <div class="app">
        <div class="titlebar">Plan Dashboard</div>
        <div class="tabs">
          ${TABS.map(function(tab) {
            return html`
              <div
                key=${tab.key}
                class=${'tab' + (activeTab === tab.key ? ' active' : '')}
                onClick=${function() { setActiveTab(tab.key); }}
              >${tab.label}</div>
            `;
          })}
        </div>
        <div class="content">
          ${activeTab === 'dashboard' && html`
            <${Dashboard}
              plans=${plans}
              todos=${todos}
              onAdd=${function() { setShowAddModal(true); }}
              onPlanClick=${onPlanClick}
              onUpdate=${loadData}
            />
          `}
          ${activeTab === 'tree' && html`
            <${PlanTree}
              plans=${plans}
              todos=${todos}
              onPlanClick=${onPlanClick}
              onUpdate=${loadData}
            />
          `}
          ${activeTab === 'timeline' && html`
            <${Timeline}
              plans=${plans}
              todos=${todos}
              onPlanClick=${onPlanClick}
            />
          `}
        </div>
        ${showAddModal && html`
          <${AddPlanModal}
            onClose=${function() { setShowAddModal(false); }}
            onCreated=${function() { setShowAddModal(false); loadData(); }}
          />
        `}
      </div>
    `;
  }

  var root = ReactDOM.createRoot(document.getElementById('root'));
  root.render(html`<${App} />`);
})();
