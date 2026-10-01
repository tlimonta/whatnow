import React from 'react';
import { factLabels, displayLabel, displayValue } from '../presentation.js';
import Icon from './Icon.jsx';

export default function FactList({ facts, missingFields }) {
  const values = facts ?? {};
  const fields = [...new Set([...Object.keys(factLabels), ...Object.keys(values), ...(missingFields ?? [])])];
  const knownFields = fields.filter((key) => values[key] != null);
  const unknownFields = fields.filter((key) => values[key] == null);
  return (
    <div className="facts-grid">
      <section className="fact-section known-facts" aria-labelledby="facts-heading">
        <div className="fact-section-heading"><h3 id="facts-heading"><Icon name="check" size={16} /> What we know</h3><span className="fact-count">{knownFields.length}</span></div>
        {knownFields.length ? <dl className="fact-list">{knownFields.map((key) => (
          <div key={key}><dt>{factLabels[key] ?? displayLabel(key)}</dt><dd>{displayValue(values[key])}</dd></div>
        ))}</dl> : <p className="muted small">No details confirmed yet.</p>}
      </section>
      <section className="fact-section unknown-facts" aria-labelledby="missing-heading">
        <div className="fact-section-heading"><h3 id="missing-heading"><Icon name="help" size={16} /> Still unknown</h3><span className="fact-count">{unknownFields.length}</span></div>
        {unknownFields.length ? <><p className="muted small">These details haven’t been confirmed.</p><ul className="unknown-list">{unknownFields.map((key) => (
          <li key={key}>{factLabels[key] ?? displayLabel(key)}</li>
        ))}</ul></> : <p className="muted small">No unknown facts listed.</p>}
      </section>
    </div>
  );
}
