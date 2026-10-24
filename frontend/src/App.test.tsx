import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import App from './App'
import { readSaved } from './lib/api'

function mount(path = '/') {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[path]}>
        <App />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}
beforeEach(() => {
  // Isolate storage from Node 25's experimental process-wide implementation.
  // Actual browser persistence is covered by scripts/check-browser.mjs.
  const values = new Map<string, string>()
  vi.stubGlobal('localStorage', {
    get length() {
      return values.size
    },
    clear: () => values.clear(),
    getItem: (key: string) => values.get(key) ?? null,
    setItem: (key: string, value: string) => values.set(key, String(value)),
    removeItem: (key: string) => values.delete(key),
    key: (index: number) => [...values.keys()][index] ?? null,
  })
  vi.spyOn(window, 'scrollTo').mockImplementation(() => {})
  vi.stubGlobal(
    'ResizeObserver',
    class {
      observe() {}
      unobserve() {}
      disconnect() {}
    },
  )
})
afterEach(() => {
  cleanup()
  vi.restoreAllMocks()
  vi.unstubAllGlobals()
})

describe('sourcing workflow', () => {
  it('runs a thesis through the simulated workflow and opens an inspectable brief', async () => {
    const user = userEvent.setup()
    mount()
    const submit = screen.getByRole('button', { name: 'Find opportunities' })
    expect((submit as HTMLButtonElement).disabled).toBe(true)
    await user.click(
      screen.getByRole('button', { name: 'AI agent monitoring' }),
    )
    await user.click(submit)
    expect(screen.getByText('SIMULATED RESEARCH')).toBeTruthy()
    await screen.findByText(
      'Builders worth a closer look.',
      {},
      { timeout: 6000 },
    )
    await user.click(await screen.findByRole('link', { name: 'Maya Chen' }))
    await screen.findByText('The users are asking. Is there a company here?')
    await user.click(
      screen.getByRole('button', { name: /A request for managed hosting/ }),
    )
    const dialog = screen.getByRole('dialog')
    expect(within(dialog).getByText('What it doesn’t establish')).toBeTruthy()
    expect(within(dialog).getByText(/no external source URL/)).toBeTruthy()
    await user.keyboard('{Escape}')
    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull())
  }, 12000)

  it('filters builders, compares two, and persists saved builders across mounts', async () => {
    const user = userEvent.setup()
    mount('/shortlist')
    await screen.findByRole('link', { name: 'Maya Chen' })
    await user.click(screen.getByRole('button', { name: 'Needs validation' }))
    expect(screen.queryByRole('link', { name: 'Maya Chen' })).toBeNull()
    expect(screen.getByRole('link', { name: 'Eli Brooks' })).toBeTruthy()
    await user.click(
      screen.getByRole('button', { name: /All recommendations/ }),
    )
    await user.click(
      screen.getByRole('checkbox', { name: 'Compare TraceNest' }),
    )
    await user.click(
      screen.getByRole('checkbox', { name: 'Compare AgentCanvas' }),
    )
    expect(
      (
        screen.getByRole('checkbox', {
          name: 'Compare EvalDock',
        }) as HTMLInputElement
      ).disabled,
    ).toBe(true)
    await user.click(screen.getByRole('button', { name: 'Compare (2/2)' }))
    expect(
      within(screen.getByRole('dialog')).getByText('Maya Chen'),
    ).toBeTruthy()
    expect(
      within(screen.getByRole('dialog')).getByText('Eli Brooks'),
    ).toBeTruthy()
    await user.keyboard('{Escape}')
    await user.click(screen.getByRole('button', { name: 'Save TraceNest' }))
    expect(readSaved()).toEqual(['tracenest'])
    cleanup()
    mount('/saved')
    expect(await screen.findByRole('link', { name: 'Maya Chen' })).toBeTruthy()
    expect(screen.queryByRole('link', { name: 'Eli Brooks' })).toBeNull()
    await user.click(screen.getByRole('button', { name: 'Unsave TraceNest' }))
    expect(screen.getByText('Your research shelf is ready.')).toBeTruthy()
  })

  it('cancels simulated research without navigating to results', async () => {
    mount()
    fireEvent.change(screen.getByRole('textbox'), {
      target: { value: 'Agents' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Find opportunities' }))
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }))
    expect(screen.queryByText('SIMULATED RESEARCH')).toBeNull()
    expect(
      (
        screen.getByRole('button', {
          name: 'Find opportunities',
        }) as HTMLButtonElement
      ).disabled,
    ).toBe(false)
  })

  it('recovers from malformed storage and unknown builder links', async () => {
    localStorage.setItem('pull:saved', '{broken')
    expect(readSaved()).toEqual([])
    localStorage.setItem('pull:saved', '["tracenest", "nonexistent", 42]')
    expect(readSaved()).toEqual(['tracenest'])
    mount('/builders/missing')
    expect(await screen.findByText('Builder not found.')).toBeTruthy()
  })
})

describe('research module integration', () => {
  it('starts a real API run and displays module failures without demo fallback', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ run_id: 'test-run' }),
      })
      .mockResolvedValue({
        ok: true,
        json: async () => ({
          run_id: 'test-run',
          thesis: 'Replay',
          mode: 'live',
          status: 'partial',
          opportunity_count: 0,
          modules: [
            {
              name: 'market',
              label: 'Market research',
              role: 'market',
              status: 'failed',
              message: 'Provider unavailable',
            },
          ],
          warnings: [],
        }),
      })
    vi.stubGlobal('fetch', fetchMock)
    const user = userEvent.setup()
    mount()
    await user.click(screen.getByRole('button', { name: 'Research modules' }))
    await user.type(screen.getByRole('textbox'), 'Replay')
    await user.click(screen.getByRole('button', { name: 'Find opportunities' }))
    await screen.findByText('Provider unavailable')
    expect(fetchMock.mock.calls[0][0]).toContain('/api/runs')
    expect(JSON.parse(fetchMock.mock.calls[0][1].body)).toEqual({
      thesis: 'Replay',
    })
    expect(screen.queryByText('SIMULATED RESEARCH')).toBeNull()
    expect(screen.queryByText('Maya Chen')).toBeNull()
  })

  it('shows API failure instead of substituting fictional opportunities', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: false,
        status: 404,
        json: async () => ({ detail: 'Run expired. Start a new search.' }),
      }),
    )
    mount('/shortlist?run=expired')
    await screen.findByText('Run expired. Start a new search.')
    expect(screen.queryByText('Maya Chen')).toBeNull()
  })
})
