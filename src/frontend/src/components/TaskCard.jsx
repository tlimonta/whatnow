import React from 'react';
import SourceLink from './SourceLink.jsx';
import Icon from './Icon.jsx';
import { displayLabel } from '../presentation.js';

export default function TaskCard({ task, index = 0, onStatusChange, saving, disabled, error }) {
  const completed = task.status === 'completed';
  return (
    <article className={`task-card${completed ? ' is-completed' : ''}`} aria-busy={saving}>
      <span className="task-sequence" aria-hidden="true">{completed ? <Icon name="check" size={17} /> : String(index + 1).padStart(2, '0')}</span>
      <div className="task-content">
        <div className="task-topline"><span className={`priority priority-${String(task.priority ?? 'unknown').toLowerCase()}`}>{task.priority == null ? 'Priority not provided' : `${displayLabel(task.priority)} priority`}</span><span className={`status status-${task.status}`}>{displayLabel(task.status)}</span></div>
        <h3 className="task-title">{task.title}</h3>
        {task.description && <p className="task-description">{task.description}</p>}
        <SourceLink sourceId={task.source_id} workflowId={task.workflow_id} />
        <div className="task-actions">
          <button className="secondary-button completion-button" type="button" disabled={disabled} onClick={() => onStatusChange(task.id, completed ? 'pending' : 'completed')} aria-label={`Mark ${task.title} as ${completed ? 'pending' : 'completed'}`}>
            <Icon name={saving ? 'clock' : completed ? 'arrow-left' : 'check'} size={15} />{saving ? 'Saving…' : completed ? 'Mark as pending' : 'Mark as complete'}
          </button>
          {task.status === 'skipped' && <button className="secondary-button" type="button" disabled={disabled} onClick={() => onStatusChange(task.id, 'pending')} aria-label={`Mark ${task.title} as pending`}>Mark as pending</button>}
        </div>
        {error && <p className="form-error task-error" role="alert">{error}</p>}
      </div>
    </article>
  );
}
