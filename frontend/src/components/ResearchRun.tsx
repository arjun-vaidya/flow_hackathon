import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { api } from '../lib/api'

export default function ResearchRun() {
  const { runId = '' } = useParams()
  const [error, setError] = useState('')
  const {
    data,
    isPending,
    error: loadError,
    refetch,
  } = useQuery({
    queryKey: ['run', runId],
    queryFn: () => api.getRun(runId),
    refetchInterval: (query) =>
      ['queued', 'running'].includes(query.state.data?.status ?? '')
        ? 700
        : false,
    retry: false,
  })
  const active = data && ['queued', 'running'].includes(data.status)
  return (
    <main className="page run-page">
      <div className="page-heading">
        <div>
          <span className="eyebrow">RESEARCH WORKSPACE</span>
          <h1>Following the evidence.</h1>
          <p>{data?.thesis}</p>
        </div>
      </div>
      {isPending && <p role="status">Loading research…</p>}
      {loadError && (
        <div role="alert">
          <p>{loadError.message}</p>
          <button className="button secondary" onClick={() => refetch()}>
            Try again
          </button>
        </div>
      )}
      {data && (
        <>
          <p className="fixture-note">
            {data.mode === 'demo'
              ? 'Synthetic integration fixture'
              : 'Connected research modules'}{' '}
            · Run {data.status}
          </p>
          <section className="research-progress" aria-live="polite">
            {data.modules.map((module) => (
              <div key={module.name} className="module-progress-row">
                <div>
                  <strong>{module.label}</strong>
                  <p>{module.message ?? module.role}</p>
                </div>
                <span className="source-tag">{module.status}</span>
              </div>
            ))}
          </section>
          <p>
            {data.opportunity_count} opportunities assembled so far. Findings
            remain provisional until reviewed.
          </p>
          <div className="button-group">
            <Link
              className="button primary"
              to={`/shortlist?run=${runId}&thesis=${encodeURIComponent(data.thesis)}`}
            >
              View opportunities
            </Link>
            {active && (
              <button
                className="button secondary"
                onClick={async () => {
                  try {
                    await api.cancelRun(runId)
                    await refetch()
                  } catch (e) {
                    setError(
                      e instanceof Error ? e.message : 'Could not cancel run.',
                    )
                  }
                }}
              >
                Cancel research
              </button>
            )}
            <Link className="text-button" to="/">
              New search
            </Link>
          </div>
          {data.warnings.map((warning) => (
            <p className="note-box" key={warning}>
              {warning}
            </p>
          ))}
        </>
      )}
      {error && <p role="alert">{error}</p>}
    </main>
  )
}
