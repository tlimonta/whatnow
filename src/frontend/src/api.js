const baseUrl = (import.meta.env?.VITE_API_BASE_URL ?? '').trim().replace(/\/+$/, '');

export class ApiError extends Error {
  constructor(message, status = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

const errorMessages = {
  422: 'The request could not be validated. Check your input and try again.',
  404: 'The requested case or task could not be found.',
  503: 'AI intake is not configured or is currently unavailable. Please try again later.',
  502: 'The AI provider request failed. Please try again later.',
  500: 'The server could not complete the request. A verified workflow may be unavailable.',
};

async function request(path, { method = 'GET', body } = {}) {
  let response;
  try {
    response = await fetch(`${baseUrl}${path}`, {
      method,
      headers: { Accept: 'application/json', ...(body ? { 'Content-Type': 'application/json' } : {}) },
      ...(body ? { body: JSON.stringify(body) } : {}),
    });
  } catch {
    throw new ApiError('Cannot reach the server. Check your connection. The request outcome could not be confirmed.');
  }
  if (!response.ok) {
    throw new ApiError(errorMessages[response.status] ?? `The server request failed (HTTP ${response.status}).`, response.status);
  }
  let data;
  try {
    data = await response.json();
  } catch {
    throw new ApiError('The server returned an unreadable response. The request outcome could not be confirmed.', response.status);
  }
  if (!data || typeof data !== 'object' || !data.id || !Array.isArray(data.tasks)) {
    throw new ApiError('The server returned an unexpected case response. The request outcome could not be confirmed.', response.status);
  }
  return data;
}

export function createCase(message) {
  if (typeof message !== 'string' || !message.trim()) {
    return Promise.reject(new ApiError('Please describe what happened before continuing.', 422));
  }
  return request('/api/cases', { method: 'POST', body: { message } });
}

export function getCase(caseId) {
  return request(`/api/cases/${encodeURIComponent(caseId)}`);
}

export function updateTaskStatus(caseId, taskId, status) {
  if (!['pending', 'completed', 'skipped'].includes(status)) {
    return Promise.reject(new ApiError('Select a supported task status.', 422));
  }
  return request(`/api/cases/${encodeURIComponent(caseId)}/tasks/${encodeURIComponent(taskId)}`, {
    method: 'PATCH', body: { status },
  });
}
