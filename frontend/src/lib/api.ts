import { opportunities, type Opportunity } from '../data/opportunities'

export type RunSnapshot = {
  run_id: string
  thesis: string
  mode: 'live' | 'demo'
  status: string
  modules: {
    name: string
    label: string
    role: string
    status: string
    message: string | null
  }[]
  opportunity_count: number
  warnings: string[]
}
const base = (import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000').replace(
  /\/$/,
  '',
)
async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${base}${path}`, init)
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new Error(
      typeof body.detail === 'string'
        ? body.detail
        : `Research request failed (${response.status}).`,
    )
  }
  return response.json()
}
export const api = {
  startRun(thesis: string) {
    return request<RunSnapshot>('/api/runs', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ thesis }),
    })
  },
  getRun(id: string) {
    return request<RunSnapshot>(`/api/runs/${encodeURIComponent(id)}`)
  },
  cancelRun(id: string) {
    return request<RunSnapshot>(`/api/runs/${encodeURIComponent(id)}/cancel`, {
      method: 'POST',
    })
  },
  async listOpportunities(runId?: string): Promise<Opportunity[]> {
    return runId
      ? request<Opportunity[]>(
          `/api/runs/${encodeURIComponent(runId)}/opportunities`,
        )
      : opportunities
  },
  async getOpportunity(id: string): Promise<Opportunity | null> {
    return id.includes(':')
      ? request<Opportunity>(`/api/opportunities/${encodeURIComponent(id)}`)
      : (opportunities.find((item) => item.id === id) ?? null)
  },
  async listSaved(ids: string[]) {
    const results = await Promise.allSettled(
      ids.map((id) => api.getOpportunity(id)),
    )
    const items: Opportunity[] = []
    const unavailable: string[] = []
    results.forEach((result, index) => {
      if (result.status === 'fulfilled' && result.value)
        items.push(result.value)
      else unavailable.push(ids[index])
    })
    return { items, unavailable }
  },
}
export function readSaved(): string[] {
  try {
    const value: unknown = JSON.parse(
      localStorage.getItem('pull:saved') ?? '[]',
    )
    return Array.isArray(value)
      ? value.filter(
          (id): id is string =>
            typeof id === 'string' &&
            (id.includes(':') || opportunities.some((item) => item.id === id)),
        )
      : []
  } catch {
    return []
  }
}
