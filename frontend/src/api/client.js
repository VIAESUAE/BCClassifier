const STORAGE = {
  apiBase: 'cardledger_api_base',
  apiKey: 'cardledger_openai_key',
  baseUrl: 'cardledger_openai_base',
  model: 'cardledger_openai_model',
}

export function getClientSettings() {
  if (typeof localStorage === 'undefined') {
    return { apiBase: '', apiKey: '', openaiBaseUrl: '', model: '' }
  }
  return {
    apiBase: localStorage.getItem(STORAGE.apiBase) || '',
    apiKey: localStorage.getItem(STORAGE.apiKey) || '',
    openaiBaseUrl: localStorage.getItem(STORAGE.baseUrl) || '',
    model: localStorage.getItem(STORAGE.model) || '',
  }
}

export function saveClientSettings(next) {
  localStorage.setItem(STORAGE.apiBase, next.apiBase || '')
  localStorage.setItem(STORAGE.apiKey, next.apiKey || '')
  localStorage.setItem(STORAGE.baseUrl, next.openaiBaseUrl || '')
  localStorage.setItem(STORAGE.model, next.model || '')
}

function apiBase() {
  const saved = getClientSettings().apiBase.trim()
  if (saved) return saved.replace(/\/$/, '')
  return (import.meta.env.VITE_API_BASE || '').replace(/\/$/, '')
}

const OPENROUTER_DEFAULT_BASE = 'https://openrouter.ai/api/v1'
const OPENROUTER_DEFAULT_MODEL = 'google/gemma-2-9b-it:free'

function authHeaders() {
  const s = getClientSettings()
  const headers = {}
  if (s.apiKey) {
    headers['X-OpenAI-Api-Key'] = s.apiKey
    headers['X-OpenAI-Base-Url'] = (s.openaiBaseUrl || OPENROUTER_DEFAULT_BASE).replace(/\/$/, '')
    headers['X-OpenAI-Model'] = s.model || OPENROUTER_DEFAULT_MODEL
  }
  return headers
}

async function request(path, options = {}) {
  const headers = { ...authHeaders(), ...(options.headers || {}) }
  const res = await fetch(`${apiBase()}${path}`, { ...options, headers })
  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      detail = body.detail || JSON.stringify(body)
    } catch {
      /* ignore */
    }
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail))
  }
  if (res.status === 204) return null
  return res.json()
}

export const api = {
  health: () => request('/health'),
  listCards: (params = {}) => {
    const qs = new URLSearchParams(params).toString()
    return request(`/cards${qs ? `?${qs}` : ''}`)
  },
  cardFilters: (lang = 'zh') => request(`/cards/filters?lang=${encodeURIComponent(lang)}`),
  ingestPreview: (file) => {
    const form = new FormData()
    form.append('file', file)
    return request('/ingest/preview', { method: 'POST', body: form })
  },
  ingestConfirm: (previewId, fields) =>
    request('/ingest/confirm', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ preview_id: previewId, fields }),
    }),
  ragQuery: (query, topK = 5) =>
    request('/rag/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, top_k: topK }),
    }),
  fileUrl: (path) => `${apiBase()}${path}`,
  testLlm: () => request('/health/llm-test'),
}
