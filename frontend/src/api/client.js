const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok && res.status === 422) {
    const err = await res.json();
    throw { status: 422, ...err };
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: 'Network error' }));
    throw { status: res.status, ...err };
  }
  return res.json();
}

export async function healthCheck() {
  return request('/health');
}

export async function postInterview(sessionId, userInput) {
  return request('/interview', {
    method: 'POST',
    body: JSON.stringify({ session_id: sessionId, user_input: userInput }),
  });
}

export async function postEvaluate(profile) {
  return request('/evaluate', {
    method: 'POST',
    body: JSON.stringify(profile),
  });
}

export async function postTranslate(text, sourceLang = 'auto', targetLang = 'hi') {
  return request('/translate', {
    method: 'POST',
    body: JSON.stringify({ text, source_lang: sourceLang, target_lang: targetLang }),
  });
}

export async function postStories(state, district = '', schemeIds = []) {
  return request('/stories', {
    method: 'POST',
    body: JSON.stringify({ state, district, scheme_ids: schemeIds }),
  });
}
