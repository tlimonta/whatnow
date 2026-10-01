import React, { useEffect, useRef, useState } from 'react';
import IntakeForm from './components/IntakeForm.jsx';
import CaseSummary from './components/CaseSummary.jsx';
import ProgressBar from './components/ProgressBar.jsx';
import TaskCard from './components/TaskCard.jsx';
import Icon from './components/Icon.jsx';
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
      <a className="skip-link" href="#main-content">Skip to content</a>
      <header className="site-header">
        <div className="brand-lockup">
          <div className="brand"><span className="brand-mark"><Icon name="arrow-right" size={23} /></span><span>WhatNow<span className="brand-period">.</span></span></div>
          <span className="brand-caption">Clarity, then action.</span>
        </div>
        <ol className="header-steps" aria-label="Your progress">
          <li className={!caseData ? 'is-current' : 'is-done'} aria-current={!caseData ? 'step' : undefined}><span className="header-step-number">{caseData ? <Icon name="check" size={13} /> : '01'}</span><span>Your situation</span></li>
          <li className={caseData ? 'is-current' : ''} aria-current={caseData ? 'step' : undefined}><span className="header-step-number">02</span><span>Your next steps</span></li>
        </ol>
      </header>
      <main id="main-content" tabIndex="-1">
        {!caseData ? (
          <IntakeForm onSubmit={submitCase} loading={creating} error={creationError} headingRef={intakeHeading} />
        ) : (
          <div className="case-view page-enter" key={caseData.id}>
            <div className="case-toolbar">
              <span className="eyebrow">Your situation, made clearer</span>
              <button className="text-button" type="button" disabled={savingTaskId !== null} onClick={returnToIntake}><Icon name="arrow-left" size={16} /> Start again</button>
            </div>
            <CaseSummary caseData={caseData} headingRef={caseHeading} />
            <section className={`action-plan${caseData.tasks.length ? '' : ' is-empty'}`} aria-labelledby="plan-heading">
              <div className="plan-overview">
                <span className="eyebrow">Moving forward</span>
                <h2 id="plan-heading">Your action plan</h2>
                <p className="plan-intro">{caseData.tasks.length ? 'One step at a time. Mark each action as complete when you’re ready.' : 'Review the facts and open questions above.'}</p>
                <ProgressBar tasks={caseData.tasks} />
              </div>
              <div className="plan-body">
                <p role="status" aria-live="polite" className={`save-notice${savingTaskId !== null || announcement ? ' is-visible' : ''}`}>
                  {(savingTaskId !== null || announcement) && <Icon name={savingTaskId !== null ? 'clock' : 'check'} size={16} />}
                  {savingTaskId !== null ? 'Saving your update. Other task controls are paused until it’s saved.' : announcement}
                </p>
                <ol className="task-list">{caseData.tasks.map((task, index) => (
                  <li className="task-list-item" key={task.id} style={{ '--card-delay': `${Math.min(index, 5) * 45}ms` }}>
                    <TaskCard task={task} index={index} onStatusChange={changeTaskStatus} saving={savingTaskId === task.id} disabled={savingTaskId !== null} error={taskError?.id === task.id ? taskError.message : ''} />
                  </li>
                ))}</ol>
              </div>
            </section>
          </div>
        )}
      </main>
      <footer className="site-footer"><span>Facts. Open questions. Next steps.</span><span className="footer-signoff">A clearer way forward.</span></footer>
    </div>
  );
}
