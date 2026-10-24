import { opportunities } from '../data/opportunities'

// Replace this adapter with authenticated FastAPI calls when the backend is ready.
// Every thesis currently returns the same clearly labeled synthetic scenario.
export const api = {
  async listOpportunities() {
    return opportunities
  },
  async getOpportunity(id: string) {
    return opportunities.find((item) => item.id === id) ?? null
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
            opportunities.some((item) => item.id === id),
        )
      : []
  } catch {
    return []
  }
}
