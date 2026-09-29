import React, { useState } from 'react';

export default function IntakeForm({ onSubmit }) {
  const [description, setDescription] = useState('');
  const [showError, setShowError] = useState(false);

  function handleSubmit(event) {
    event.preventDefault();
    if (!description.trim()) {
      setShowError(true);
      return;
    }
    setShowError(false);
    onSubmit(description);
  }

  return (
    <section className="intake panel" aria-labelledby="intake-heading">
      <div className="eyebrow">A clearer place to start</div>
      <h1 id="intake-heading">Tell us what happened.</h1>
      <p className="lead">WhatNow helps you organize a difficult situation into facts, open questions, and next steps. This first version shows a sample case using local demo data.</p>
      <form onSubmit={handleSubmit}>
        <label htmlFor="description">Describe what happened</label>
        <textarea
          id="description"
          name="description"
          value={description}
          onChange={(event) => { setDescription(event.target.value); setShowError(false); }}
          placeholder="For example: I can’t find my phone."
          rows="6"
          required
          aria-describedby={`privacy-warning demo-note${showError ? ' description-error' : ''}`}
          aria-invalid={showError}
        />
        {showError && <p id="description-error" className="form-error" role="alert">Please describe what happened before continuing.</p>}
        <p id="privacy-warning" className="warning">Do not enter passwords, PINs, card numbers, or authentication codes.</p>
        <p id="demo-note" className="muted">Your text stays in this page. Submitting opens a fixed demonstration case; it is not analyzed.</p>
        <button className="primary-button" type="submit">Get help <span aria-hidden="true">→</span></button>
      </form>
    </section>
  );
}
