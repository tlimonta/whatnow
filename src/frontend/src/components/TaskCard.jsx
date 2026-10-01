import React from 'react';
import SourceLink from './SourceLink.jsx';
import { displayLabel } from '../presentation.js';

export default function TaskCard({ task, onStatusChange, saving, disabled, error }) {
  const completed = task.status === 'completed';
  return (
    <article className="task-card" aria-busy={saving}>
      <div className="task-topline"><span className="priority">{task.priority == null ? 'Priority not provided' : `${displayLabel(task.priority)} priority`}</span><span className={`status status-${task.status}`}>{displayLabel(task.status)}</span></div>
      <h3>{task.title}</h3>
      {task.description && <p>{task.description}</p>}
      <SourceLink sourceId={task.source_id} workflowId={task.workflow_id} />
      <button className="secondary-button" type="button" disabled={disabled} onClick={() => onStatusChange(task.id, completed ? 'pending' : 'completed')} aria-label={`Mark ${task.title} as ${completed ? 'pending' : 'completed'}`}>
        {saving ? 'Saving…' : completed ? 'Mark as pending' : 'Mark as complete'}
      </button>
      {task.status === 'skipped' && <button className="secondary-button" type="button" disabled={disabled} onClick={() => onStatusChange(task.id, 'pending')} aria-label={`Mark ${task.title} as pending`}>Mark as pending</button>}
      {error && <p className="form-error" role="alert">{error}</p>}
    </article>
  );
}
