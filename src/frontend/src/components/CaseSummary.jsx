import React from 'react';
import FactList from './FactList.jsx';
import { displayLabel } from '../presentation.js';

export default function CaseSummary({ caseData }) {
  return (
    <section className="panel" aria-labelledby="case-heading">
      <div className="section-heading"><div><div className="eyebrow">Case · {caseData.id}</div><h2 id="case-heading">Case overview</h2></div></div>
      <div className="case-meta">
        <div><span>Case type</span><strong>{displayLabel(caseData.case_type)}</strong></div>
        <div><span>Risk level</span><strong>{caseData.risk_level == null ? 'Not assessed' : displayLabel(caseData.risk_level)}</strong></div>
        <div><span>Case status</span><strong>{displayLabel(caseData.status)}</strong></div>
      </div>
      <div className="description-box"><h3>Your description</h3><p className="user-description">{caseData.initial_message ?? 'Unknown'}</p></div>
      <FactList facts={caseData.facts} missingFields={caseData.missing_fields} />
    </section>
  );
}
