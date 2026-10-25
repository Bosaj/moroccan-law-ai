import type {
  AnswerLang,
  AuditResult,
  BoIssue,
  Health,
  QueryResult,
  RedlineDiff,
} from './types'

export class ApiError extends Error {
  readonly status: number
  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response
  try {
    res = await fetch(path, init)
  } catch {
    // The browser could not reach the server at all (offline, server stopped, CORS).
    throw new ApiError('network', 0)
  }
  let body: unknown = null
  try {
    body = await res.json()
  } catch {
    body = null
  }
  if (!res.ok) {
    const message =
      body && typeof body === 'object' && 'error' in body ? String((body as { error: unknown }).error) : res.statusText
    throw new ApiError(message || 'request failed', res.status)
  }
  return body as T
}

const post = <T>(path: string, payload: unknown, signal?: AbortSignal) =>
  request<T>(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    signal,
  })

export const api = {
  health: () => request<Health>('/api/health'),
  boIssues: async () => (await request<{ count: number; issues: BoIssue[] }>('/api/bo-issues')).issues,
  query: (query: string, lang: AnswerLang, signal?: AbortSignal) =>
    post<QueryResult>('/api/query', { query, lang }, signal),
  diff: (oldText: string, newText: string, articleRef: string, signal?: AbortSignal) =>
    post<RedlineDiff>(
      '/api/bo-diff',
      { old_text: oldText, new_text: newText, article_ref: articleRef || 'Comparaison libre' },
      signal,
    ),
  auditContract: (contractText: string, lang: 'fr' | 'ar', signal?: AbortSignal) =>
    post<AuditResult>('/api/audit-contract', { contract_text: contractText, lang }, signal),
}
