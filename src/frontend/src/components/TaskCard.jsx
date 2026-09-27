import React from 'react';
import SourceLink from './SourceLink.jsx';

export default function TaskCard({ task, presentation, onToggle }) {
  const completed = task.status === 'completed';

  return (
    <article className="task-card">
      <div className="task-topline"><span className="priority">{presentation.priority} priority · demo</span><span className="status">{completed ? 'Completed' : 'Pending'}</span></div>
      <h3>{task.title}</h3>
      <p>{presentation.explanation}</p>
      <SourceLink />
      <button className="secondary-button" type="button" onClick={() => onToggle(task.id)} aria-label={`Mark ${task.title} as ${completed ? 'pending' : 'completed'}`}>
        {completed ? 'Mark as pending' : 'Mark as complete'}
      </button>
    </article>
  );
}
