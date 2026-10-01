import React from 'react';

export default function ProgressBar({ tasks }) {
  if (!tasks.length) return <p className="muted">No verified action plan is available for this case. There are no tasks to track.</p>;
  const completed = tasks.filter((task) => task.status === 'completed').length;
  const percent = Math.round((completed / tasks.length) * 100);
  return (
    <div className="progress-wrap">
      <div className="progress-copy"><strong>Progress</strong><span>{completed} of {tasks.length} tasks complete · {percent}%</span></div>
      <progress value={completed} max={tasks.length} aria-label="Tasks completed">{percent}%</progress>
    </div>
  );
}
