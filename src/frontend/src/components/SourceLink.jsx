import React from 'react';

export default function SourceLink({ sourceId, workflowId }) {
  return (
    <div className="source-area">
      <span className="source-label">References</span>
      {sourceId != null && <span>Source ID: {sourceId}</span>}
      {workflowId != null && <span>Workflow ID: {workflowId}</span>}
      {sourceId == null && workflowId == null && <span>No source or workflow reference provided.</span>}
    </div>
  );
}
