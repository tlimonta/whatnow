import React from 'react';
import FactList from './FactList.jsx';

export default function CaseSummary({ caseData, submittedDescription }) {
  return (
    <section className="panel" aria-labelledby="case-heading">
      <div className="section-heading">
        <div>
          <div className="eyebrow">Example case · {caseData.id}</div>
          <h2 id="case-heading">Case overview</h2>
        </div>
        <span className="demo-tag">Mock data</span>
      </div>
      <p className="muted">This is a fixed demonstration scenario. Its labels and facts were not derived from your description.</p>
      <div className="case-meta">
        <div><span>Case type</span><strong>Stolen phone <small>(demo)</small></strong></div>
        <div><span>Risk level</span><strong>High <small>(demo)</small></strong></div>
        <div><span>Case status</span><strong>Active <small>(demo)</small></strong></div>
      </div>
      <div className="description-box">
        <h3>Your description</h3>
        <p className="user-description">{submittedDescription}</p>
        <p className="muted small">Stored only in this page until you leave or refresh. It does not change the example case.</p>
      </div>
      <FactList facts={caseData.facts} missingFields={caseData.missing_fields} />
    </section>
  );
}
