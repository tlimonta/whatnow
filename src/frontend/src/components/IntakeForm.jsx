import React, { useRef, useState } from 'react';
import Icon from './Icon.jsx';

const examples = [
  { label: 'My phone was stolen', message: 'My phone was stolen in Spain.' },
  { label: 'I lost my phone', message: 'I lost my phone and I’m not sure where it is.' },
  { label: 'I’m not sure what happened', message: 'I can’t find my phone. I’m not sure if I lost it or if it was stolen.' },
];

export default function IntakeForm({ onSubmit, loading, error, headingRef }) {
  const [description, setDescription] = useState('');
  const [showError, setShowError] = useState(false);
  const textareaRef = useRef(null);

  async function handleSubmit(event) {
    event.preventDefault();
    if (loading) return;
    if (!description.trim()) {
      setShowError(true);
      textareaRef.current?.focus();
      return;
    }
    setShowError(false);
    await onSubmit(description);
  }

  function useExample(message) {
    setDescription(message);
    setShowError(false);
    textareaRef.current?.focus();
  }

  return (
    <section className="intake page-enter" aria-labelledby="intake-heading">
      <div className="intake-intro">
        <div className="eyebrow"><span className="eyebrow-line" /> A clearer place to start</div>
        <h1 id="intake-heading" ref={headingRef} tabIndex="-1">Let’s find your<br /><span>next step.</span></h1>
        <p className="lead">When something goes wrong, it helps to know where to start. Turn your situation into facts, open questions, and a plan.</p>
        <ol className="intake-guide" aria-label="How WhatNow works">
          <li><span className="guide-number">01</span><div><h2>Start with your story</h2><p>Share what happened, in your own words.</p></div></li>
          <li><span className="guide-number">02</span><div><h2>See the full picture</h2><p>Separate what’s known from what’s still unclear.</p></div></li>
          <li><span className="guide-number">03</span><div><h2>Take the next step</h2><p>Follow the available actions and track your progress.</p></div></li>
        </ol>
        <p className="intake-reassurance">You don’t need to have all the answers to begin.</p>
      </div>
      <div className={`intake-panel panel${loading ? ' is-processing' : ''}`}>
        <div className="intake-panel-heading"><span className="section-index">01 / YOUR SITUATION</span><Icon name="file" size={21} /></div>
        <h2>Tell us what happened.</h2>
        <p className="form-intro">A few details are enough to get started.</p>
        <form onSubmit={handleSubmit} aria-busy={loading} noValidate>
          <div className="field-heading"><label htmlFor="description">Your description</label><span>In your own words</span></div>
          <textarea
            ref={textareaRef}
            id="description"
            name="description"
            value={description}
            onChange={(event) => { setDescription(event.target.value); setShowError(false); }}
            placeholder="What happened? Where were you? Share what you know so far…"
            rows="6"
            disabled={loading}
            required
            aria-describedby={`privacy-warning submission-note${showError ? ' description-error' : ''}${error ? ' api-error' : ''}`}
            aria-invalid={showError}
          />
          {showError && <p id="description-error" className="form-error" role="alert">Please describe what happened before continuing.</p>}
          <div className="example-prompts">
            <span className="example-label">Need a starting point?</span>
            <div className="example-chips">{examples.map((example) => (
              <button key={example.label} className="example-chip" type="button" disabled={loading} onClick={() => useExample(example.message)}><Icon name="plus" size={13} />{example.label}</button>
            ))}</div>
          </div>
          <div id="privacy-warning" className="privacy-warning"><Icon name="lock" size={18} /><p><strong>Keep sensitive details to yourself.</strong> Do not enter passwords, PINs, card numbers, or authentication codes.</p></div>
          {error && <div id="api-error" className="form-error api-error" role="alert"><Icon name="help" size={19} /><div><strong>We couldn’t create your case.</strong><p>{error}</p></div></div>}
          <div className="form-actions">
            <button className="primary-button" type="submit" disabled={loading}>{loading ? <><span className="loading-spinner" aria-hidden="true" /> Creating your case…</> : <>Find my next steps <Icon name="arrow-right" size={18} /></>}</button>
            <p id="submission-note">Submitting sends your description to WhatNow to create a case.</p>
          </div>
        </form>
        <div className="processing-status" role="status" aria-live="polite" aria-atomic="true">
          {loading && <div className="processing-message"><Icon name="clock" size={22} /><div><strong>Making sense of your situation</strong><p>We’re preparing your case and available actions. This may take a moment.</p></div></div>}
        </div>
      </div>
    </section>
  );
}
