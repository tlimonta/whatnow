import React from 'react';
import { factLabels, displayLabel, displayValue } from '../presentation.js';

export default function FactList({ facts, missingFields }) {
  const values = facts ?? {};
  const fields = [...new Set([...Object.keys(factLabels), ...Object.keys(values), ...(missingFields ?? [])])];
  const unknownFields = fields.filter((key) => values[key] == null);
  return (
    <div className="facts-grid">
      <section className="subpanel" aria-labelledby="facts-heading">
        <h3 id="facts-heading">Case facts</h3>
        <dl className="fact-list">{fields.map((key) => (
          <div key={key}><dt>{factLabels[key] ?? displayLabel(key)}</dt><dd>{displayValue(values[key])}</dd></div>
        ))}</dl>
      </section>
      <section className="subpanel" aria-labelledby="missing-heading">
        <h3 id="missing-heading">Still unknown</h3>
        {unknownFields.length ? <dl className="fact-list">{unknownFields.map((key) => (
          <div key={key}><dt>{factLabels[key] ?? displayLabel(key)}</dt><dd>Unknown</dd></div>
        ))}</dl> : <p className="muted small">No unknown facts listed.</p>}
      </section>
    </div>
  );
}
