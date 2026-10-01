import React, { useEffect, useRef, useState } from 'react';
import IntakeForm from './components/IntakeForm.jsx';
import CaseSummary from './components/CaseSummary.jsx';
import ProgressBar from './components/ProgressBar.jsx';
import TaskCard from './components/TaskCard.jsx';
import { createCase, updateTaskStatus } from './api.js';

export default function App() {
  const [caseData, setCaseData] = useState(null);
  const [creating, setCreating] = useState(false);
  const [creationError, setCreationError] = useState('');
  const [savingTaskId, setSavingTaskId] = useState(null);
  const [taskError, setTaskError] = useState(null);
  const [announcement, setAnnouncement] = useState('');
  const requestInFlight = useRef(false);
  const caseHeading = useRef(null);
  const intakeHeading = useRef(null);
  const caseId = caseData?.id;

  useEffect(() => {
    if (caseId) caseHeading.current?.focus();
    else intakeHeading.current?.focus();
  }, [caseId]);

  async function submitCase(message) {
    if (requestInFlight.current) return;
    requestInFlight.current = true;
    setCreating(true);
    setCreationError('');
    try {
      setCaseData(await createCase(message));
    } catch (error) {
      setCreationError(error.message);
    } finally {
      requestInFlight.current = false;
      setCreating(false);
    }
  }

  async function changeTaskStatus(taskId, status) {
    if (requestInFlight.current) return;
    requestInFlight.current = true;
    setSavingTaskId(taskId);
    setTaskError(null);
    setAnnouncement('');
    try {
      setCaseData(await updateTaskStatus(caseData.id, taskId, status));
      setAnnouncement('Task status saved.');
    } catch (error) {
      setTaskError({ id: taskId, message: `${error.message} Showing the last confirmed case state.` });
    } finally {
      requestInFlight.current = false;
      setSavingTaskId(null);
    }
  }

  function returnToIntake() {
    if (requestInFlight.current) return;
    setCaseData(null);
    setTaskError(null);
    setCreationError('');
    setAnnouncement('');
  }

  return (
    <div className="app-shell">
      <header className="site-header">
        <div className="brand"><span className="brand-mark" aria-hidden="true">✳</span><span>WhatNow</span></div>
        <span className="header-label">Your next steps</span>
      </header>
      <main id="main-content">
        {!caseData ? (
          <IntakeForm onSubmit={submitCase} loading={creating} error={creationError} headingRef={intakeHeading} />
        ) : (
          <div className="case-view">
            <div className="view-intro">
              <div><div className="eyebrow">Your case</div><h1 ref={caseHeading} tabIndex="-1">Make sense of the next steps.</h1><p>Review the facts and available actions for your case.</p></div>
              <button className="text-button" type="button" disabled={savingTaskId !== null} onClick={returnToIntake}>← Start again</button>
            </div>
            <CaseSummary caseData={caseData} />
            <section className="panel" aria-labelledby="plan-heading">
              <div className="section-heading"><h2 id="plan-heading">Action plan</h2></div>
              <ProgressBar tasks={caseData.tasks} />
              <p role="status" className="muted">{savingTaskId !== null ? 'Saving task status… Other task controls are paused until saving finishes.' : announcement}</p>
              <div className="task-list">{caseData.tasks.map((task) => <TaskCard key={task.id} task={task} onStatusChange={changeTaskStatus} saving={savingTaskId === task.id} disabled={savingTaskId !== null} error={taskError?.id === task.id ? taskError.message : ''} />)}</div>
            </section>
          </div>
        )}
      </main>
      <footer className="site-footer">WhatNow · Facts, open questions, and next steps</footer>
    </div>
  );
}
