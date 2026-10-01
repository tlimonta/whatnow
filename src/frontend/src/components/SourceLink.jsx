import React from 'react';
import Icon from './Icon.jsx';
import { officialSources } from '../presentation.js';

export default function SourceLink({ sourceId, workflowId }) {
  const workflowSources = Object.hasOwn(officialSources, workflowId) ? officialSources[workflowId] : null;
  const source = workflowSources && Object.hasOwn(workflowSources, sourceId) ? workflowSources[sourceId] : null;
  const hasReference = sourceId != null || workflowId != null;
  return (
    <div className="source-area">
      {source ? <><span className="source-label">Official guidance</span><a className="source-name" href={source.url} target="_blank" rel="noopener noreferrer">{source.name}<Icon name="external" size={13} /><span className="sr-only"> (opens in a new tab)</span></a></> : <p className="source-empty">{hasReference ? 'Guidance reference available below.' : 'No guidance reference provided.'}</p>}
      {hasReference && <details className="source-details"><summary>Reference details</summary><dl>
        {sourceId != null && <div><dt>Source ID</dt><dd><code>{sourceId}</code></dd></div>}
        {workflowId != null && <div><dt>Workflow ID</dt><dd><code>{workflowId}</code></dd></div>}
      </dl></details>}
    </div>
  );
}
