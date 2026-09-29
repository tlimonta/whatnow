import React from 'react';
import { factLabels } from '../mockData.js';

function displayValue(value) {
  if (value === null || value === undefined) return 'Unknown';
  if (typeof value === 'boolean') return value ? 'Yes' : 'No';
  return String(value);
}

export default function FactList({ facts, missingFields }) {
  const knownFacts = Object.entries(facts).filter(([, value]) => value !== null && value !== undefined);

  return (
    <div className="facts-grid">
      <section className="subpanel" aria-labelledby="known-heading">
        <h3 id="known-heading">Known in this example</h3>
        <dl className="fact-list">
          {knownFacts.map(([key, value]) => (
            <div key={key}><dt>{factLabels[key] ?? key}</dt><dd>{displayValue(value)}</dd></div>
          ))}
        </dl>
      </section>
      <section className="subpanel" aria-labelledby="missing-heading">
        <h3 id="missing-heading">Still unknown</h3>
        <p className="muted small">These details are deliberately not filled in.</p>
        <dl className="fact-list">
          {missingFields.map((key) => (
            <div key={key}><dt>{factLabels[key] ?? key}</dt><dd>Unknown</dd></div>
          ))}
        </dl>
      </section>
    </div>
  );
}
