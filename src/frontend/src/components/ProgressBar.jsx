import React from 'react';

export default function ProgressBar({ tasks }) {
  if (!tasks.length) return <p className="empty-plan">No verified action plan is available for this case. There are no tasks to track.</p>;
  const completed = tasks.filter((task) => task.status === 'completed').length;
  const percent = Math.round((completed / tasks.length) * 100);
  return (
    <div className="progress-wrap">
      <div className="progress-copy"><strong>Your progress</strong><span className="progress-value">{percent}%</span></div>
      <div className="progress-track" role="progressbar" aria-label="Tasks completed" aria-valuemin={0} aria-valuemax={tasks.length} aria-valuenow={completed} aria-valuetext={`${completed} of ${tasks.length} tasks complete`}><span className="progress-fill" style={{ width: `${percent}%` }} /></div>
      <p className="progress-note">{completed} of {tasks.length} tasks complete{completed === tasks.length ? ' · All done' : ''}</p>
    </div>
  );
}
