import React from 'react';
import FactList from './FactList.jsx';
import Icon from './Icon.jsx';
import { displayLabel } from '../presentation.js';

export default function CaseSummary({ caseData, headingRef }) {
  const context = [
    { key: 'location', icon: 'map-pin', label: 'Location' },
    { key: 'device_type', icon: 'file', label: 'Device' },
    { key: 'incident_time', icon: 'clock', label: 'Incident time' },
  ].filter(({ key }) => caseData.facts?.[key] != null);

  return (
    <section className="case-summary panel" aria-labelledby="case-heading">
      <div className="case-summary-header">
        <div className="case-heading-group">
          <span className="eyebrow">Your case overview</span>
          <h1 className="case-title" id="case-heading" ref={headingRef} tabIndex="-1">{caseData.case_type == null ? 'Your situation' : displayLabel(caseData.case_type)}</h1>
        </div>
        <div className="case-status">
          <span className={`status status-${caseData.status}`}>{displayLabel(caseData.status)}</span>
          <span className={`priority priority-${caseData.risk_level ?? 'unknown'}`}>{caseData.risk_level == null ? 'Risk not assessed' : `${displayLabel(caseData.risk_level)} risk`}</span>
        </div>
      </div>
      {context.length > 0 && <div className="case-context">{context.map(({ key, icon, label }) => (
        <span className="context-item" key={key}><Icon name={icon} size={15} /><span className="sr-only">{label}: </span>{String(caseData.facts[key])}</span>
      ))}</div>}
      <div className="description-box"><h3>In your words</h3><p className="user-description">{caseData.initial_message ?? 'No description provided.'}</p></div>
      <FactList facts={caseData.facts} missingFields={caseData.missing_fields} />
      <details className="case-reference"><summary>Case reference</summary><p>Case ID: <code>{caseData.id}</code></p></details>
    </section>
  );
}
