import React, { useState } from 'react';

export default function IntakeForm({ onSubmit, loading, error, headingRef }) {
  const [description, setDescription] = useState('');
  const [showError, setShowError] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    if (loading) return;
    if (!description.trim()) {
      setShowError(true);
      return;
    }
    setShowError(false);
    await onSubmit(description);
  }

  return (
    <section className="intake panel" aria-labelledby="intake-heading">
      <div className="eyebrow">A clearer place to start</div>
      <h1 id="intake-heading" ref={headingRef} tabIndex="-1">Tell us what happened.</h1>
      <p className="lead">WhatNow helps you organize a difficult situation into facts, open questions, and next steps.</p>
      <form onSubmit={handleSubmit} aria-busy={loading} noValidate>
        <label htmlFor="description">Describe what happened</label>
        <textarea
          id="description"
          name="description"
          value={description}
          onChange={(event) => { setDescription(event.target.value); setShowError(false); }}
          placeholder="For example: I can’t find my phone."
          rows="6"
          disabled={loading}
          required
          aria-describedby={`privacy-warning submission-note${showError ? ' description-error' : ''}${error ? ' api-error' : ''}`}
          aria-invalid={showError}
        />
        {showError && <p id="description-error" className="form-error" role="alert">Please describe what happened before continuing.</p>}
        <p id="privacy-warning" className="warning">Do not enter passwords, PINs, card numbers, or authentication codes.</p>
        <p id="submission-note" className="muted">Submitting sends your description to WhatNow to create a case.</p>
        {error && <p id="api-error" className="form-error" role="alert">{error}</p>}
        <p role="status">{loading ? 'Creating your case…' : ''}</p>
        <button className="primary-button" type="submit" disabled={loading}>{loading ? 'Creating case…' : 'Get help'} <span aria-hidden="true">→</span></button>
      </form>
    </section>
  );
}
