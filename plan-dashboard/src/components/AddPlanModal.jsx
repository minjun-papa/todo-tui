/* AddPlanModal component */
(function() {
  var html = htm.bind(React.createElement);
  var useState = React.useState;

  window.AddPlanModal = function AddPlanModal(props) {
    var onClose = props.onClose;
    var onCreated = props.onCreated;
    var ref1 = useState(''), name = ref1[0], setName = ref1[1];
    var ref2 = useState(''), workingDir = ref2[0], setWorkingDir = ref2[1];
    var ref3 = useState(''), model = ref3[0], setModel = ref3[1];
    var ref4 = useState(''), prompt = ref4[0], setPrompt = ref4[1];

    function onSubmit(e) {
      e.preventDefault();
      if (!name.trim()) return;
      window.DataAccess.createPlan({
        name: name.trim(),
        working_dir: workingDir.trim() || null,
        model: model.trim() || null,
        prompt: prompt.trim() || null,
      }).then(onCreated);
    }

    return html`<div class="modal-overlay" onClick=${onClose}>
      <div class="modal" onClick=${function(e){e.stopPropagation()}}>
        <h2>New Plan</h2>
        <form onSubmit=${onSubmit}>
          <div class="form-group">
            <label>Plan Name *</label>
            <input type="text" placeholder="e.g. Todo TUI Dashboard Migration" value=${name} onInput=${function(e){setName(e.target.value)}} />
          </div>
          <div class="form-group">
            <label>Working Directory</label>
            <input type="text" placeholder="/path/to/project" value=${workingDir} onInput=${function(e){setWorkingDir(e.target.value)}} />
          </div>
          <div class="form-group">
            <label>Model</label>
            <input type="text" placeholder="claude-sonnet-4-20250514" value=${model} onInput=${function(e){setModel(e.target.value)}} />
          </div>
          <div class="form-group">
            <label>Prompt</label>
            <textarea placeholder="Plan objective..." value=${prompt} onInput=${function(e){setPrompt(e.target.value)}}></textarea>
          </div>
          <div class="modal-actions">
            <button type="button" class="btn" onClick=${onClose}>Cancel</button>
            <button type="submit" class="btn btn-primary">Create Plan</button>
          </div>
        </form>
      </div>
    </div>`;
  };
})();
