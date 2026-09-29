import React, { useEffect, useRef, useState } from 'react';
import IntakeForm from './components/IntakeForm.jsx';
import CaseSummary from './components/CaseSummary.jsx';
import ProgressBar from './components/ProgressBar.jsx';
import TaskCard from './components/TaskCard.jsx';
import { mockCase, mockTaskPresentation } from './mockData.js';

export default function App() {
  const [submittedDescription, setSubmittedDescription] = useState(null);
  const [tasks, setTasks] = useState(() => mockCase.tasks.map((task) => ({ ...task })));
  const caseHeading = useRef(null);

  useEffect(() => {
    if (submittedDescription !== null) caseHeading.current?.focus();
  }, [submittedDescription]);

  function toggleTask(id) {
    setTasks((current) => current.map((task) => task.id === id
      ? { ...task, status: task.status === 'completed' ? 'pending' : 'completed' }
      : task));
  }

  function returnToIntake() {
    setSubmittedDescription(null);
    setTasks(mockCase.tasks.map((task) => ({ ...task })));
  }

  return (
    <div className="app-shell">
      <header className="site-header">
        <div className="brand"><span className="brand-mark" aria-hidden="true">✳</span><span>WhatNow</span></div>
        <span className="header-label">Phase 1 prototype</span>
      </header>
      <main id="main-content">
        {submittedDescription === null ? (
          <IntakeForm onSubmit={setSubmittedDescription} />
        ) : (
          <div className="case-view">
            <div className="view-intro">
              <div><div className="eyebrow">A sample of what comes next</div><h1 ref={caseHeading} tabIndex="-1">Make sense of the next steps.</h1><p>This page uses local mock data. It is not personalized advice or verified procedural guidance.</p></div>
              <button className="text-button" type="button" onClick={returnToIntake}>← Start again</button>
            </div>
            <CaseSummary caseData={mockCase} submittedDescription={submittedDescription} />
            <section className="panel" aria-labelledby="plan-heading">
              <div className="section-heading"><div><div className="eyebrow">Demonstration only</div><h2 id="plan-heading">Action plan preview</h2></div><span className="demo-tag">Mock tasks</span></div>
              <p className="muted">These cards demonstrate the interface. They are not Spain procedures, official instructions, or a personalized plan.</p>
              <ProgressBar tasks={tasks} />
              <div className="task-list">{tasks.map((task) => <TaskCard key={task.id} task={task} presentation={mockTaskPresentation[task.id]} onToggle={toggleTask} />)}</div>
            </section>
          </div>
        )}
      </main>
      <footer className="site-footer">WhatNow · Frontend demonstration · No backend or AI connection</footer>
    </div>
  );
}
