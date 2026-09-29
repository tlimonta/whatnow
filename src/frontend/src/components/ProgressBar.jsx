import React from 'react';

export default function ProgressBar({ tasks }) {
  const completed = tasks.filter((task) => task.status === 'completed').length;
  const percent = tasks.length ? Math.round((completed / tasks.length) * 100) : 0;

  return (
    <div className="progress-wrap">
      <div className="progress-copy"><strong>Demo progress</strong><span>{completed} of {tasks.length} tasks complete · {percent}%</span></div>
      <progress value={completed} max={tasks.length || 1} aria-label="Demo tasks completed">{percent}%</progress>
    </div>
  );
}
