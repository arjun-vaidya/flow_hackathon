import { lazy, Suspense, useEffect, useState } from 'react'
import {
  Link,
  NavLink,
  Route,
  Routes,
  useLocation,
  useNavigate,
  useParams,
} from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  ArrowDown,
  ArrowLeft,
  ArrowRight,
  Bookmark,
  Check,
  CheckCheck,
  ChevronRight,
  Compass,
  Download,
  GitBranch,
  Github,
  Layers3,
  LoaderCircle,
  Search,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
  Users,
  X,
} from 'lucide-react'
import { Dialog } from './components/ui/dialog'
import ResearchRun from './components/ResearchRun'
import { api, readSaved } from './lib/api'
import type {
  Evidence,
  Opportunity,
  Recommendation,
} from './data/opportunities'

const recommendations: Recommendation[] = [
  'Worth a conversation',
  'Needs validation',
  'Watch',
]
const ActivityChart = lazy(() => import('./components/ActivityChart'))
const topics = [
  'AI agent monitoring',
  'Deterministic replay',
  'Warm sandboxing',
  'Local LLM runners',
]
const stages = [
  'Interpreting your investment thesis',
  'Looking for signs of user demand',
  'Connecting projects to their builders',
  'Checking evidence and open questions',
]
function Badge({ value }: { value: Recommendation }) {
  return (
    <span
      className={`badge ${value === 'Worth a conversation' ? 'green' : value === 'Needs validation' ? 'amber' : 'gray'}`}
    >
      <span className="status-dot" />
      {value}
    </span>
  )
}
function SaveButton({
  item,
  saved,
  toggle,
  compact = false,
}: {
  item: Opportunity
  saved: string[]
  toggle: (id: string) => void
  compact?: boolean
}) {
  const active = saved.includes(item.id)
  return (
    <button
      className={compact ? 'icon-button' : 'button secondary'}
      aria-label={`${active ? 'Unsave' : 'Save'} ${item.project}`}
      aria-pressed={active}
      onClick={() => toggle(item.id)}
    >
      <Bookmark size={16} fill={active ? 'currentColor' : 'none'} />
      {!compact && (active ? 'Saved' : 'Save builder')}
    </button>
  )
}

export default function App() {
  const [saved, setSaved] = useState<string[]>(readSaved)
  const [notice, setNotice] = useState('')
  const [about, setAbout] = useState(false)
  const [lastRun, setLastRun] = useState<string>()
  const location = useLocation()
  useEffect(() => {
    window.scrollTo?.(0, 0)
    const queryRun = new URLSearchParams(location.search).get('run')
    const pathRun = location.pathname.startsWith('/runs/')
      ? location.pathname.split('/')[2]
      : undefined
    const briefId = location.pathname.startsWith('/builders/')
      ? decodeURIComponent(location.pathname.split('/')[2])
      : ''
    if (queryRun || pathRun || briefId.includes(':'))
      setLastRun(queryRun ?? pathRun ?? briefId.split(':')[0])
    else if (location.pathname === '/shortlist') setLastRun(undefined)
  }, [location.pathname, location.search])
  useEffect(() => {
    if (notice) {
      const timer = setTimeout(() => setNotice(''), 4000)
      return () => clearTimeout(timer)
    }
  }, [notice])
  function toggle(id: string) {
    const next = saved.includes(id)
      ? saved.filter((value) => value !== id)
      : [...saved, id]
    setSaved(next)
    try {
      localStorage.setItem('pull:saved', JSON.stringify(next))
    } catch {
      setNotice('Saved for this session. Browser storage is unavailable.')
    }
  }
  return (
    <>
      <header className="topbar">
        <div className="header-left">
          <button type="button" className="about-button">
            About
          </button>
        </div>
        <nav className="main-nav" aria-label="Main navigation">
          <NavLink to="/" end>
            <Compass size={15} />
            Discover
          </NavLink>
          <NavLink to={lastRun ? `/shortlist?run=${lastRun}` : '/shortlist'}>
            <Layers3 size={15} />
            Shortlist
          </NavLink>
          <NavLink to="/saved">
            <Bookmark size={15} />
            Saved<span className="nav-count">{saved.length}</span>
          </NavLink>
        </nav>
      </header>
      <Routes>
        <Route path="/" element={<Discover />} />
        <Route path="/runs/:runId" element={<ResearchRun />} />
        <Route
          path="/shortlist"
          element={<Shortlist saved={saved} toggle={toggle} />}
        />
        <Route
          path="/saved"
          element={<Shortlist saved={saved} toggle={toggle} savedOnly />}
        />
        <Route
          path="/builders/:id"
          element={<Brief saved={saved} toggle={toggle} />}
        />
        <Route
          path="*"
          element={
            <main className="page">
              <Empty
                title="This page wandered off."
                text="Head back to discovery to find your next conversation."
              />
            </main>
          }
        />
      </Routes>
      <footer className="footer">
        <div className="footer-main">
          <div className="footer-intro">
            <Link to="/" className="footer-brand" aria-label="Gradient home">
              <span className="footer-brand-icon">
                <Layers3 size={17} strokeWidth={1.5} />
              </span>
              <span>Gradient</span>
            </Link>
            <p>
              Venture intelligence connecting technical builders, public demand,
              and the evidence behind your next conversation.
            </p>
          </div>
          <nav className="footer-column" aria-label="Platform">
            <h2>PLATFORM</h2>
            <Link to="/">Signal discovery</Link>
            <Link to="/shortlist">Builder shortlist</Link>
            <Link to="/saved">Saved builders</Link>
          </nav>
          <nav className="footer-column" aria-label="Project">
            <h2>PROJECT</h2>
            <button onClick={() => setAbout(true)}>About Gradient</button>
            <a
              href="https://github.com/arjun-vaidya/flow_hackathon/blob/main/docs/PROJECT_PLAN.md"
              target="_blank"
              rel="noreferrer"
            >
              Methodology
            </a>
            <a
              href="https://github.com/arjun-vaidya/flow_hackathon/blob/main/docs/ARCHITECTURE.md"
              target="_blank"
              rel="noreferrer"
            >
              Architecture
            </a>
          </nav>
          <nav className="footer-column" aria-label="Resources">
            <h2>RESOURCES</h2>
            <a
              href="https://github.com/arjun-vaidya/flow_hackathon"
              target="_blank"
              rel="noreferrer"
            >
              Source code
            </a>
            <a
              href="https://github.com/arjun-vaidya/flow_hackathon/tree/main/frontend#readme"
              target="_blank"
              rel="noreferrer"
            >
              Documentation
            </a>
            <button onClick={() => setAbout(true)}>Data & limitations</button>
          </nav>
        </div>
        <div className="footer-bottom">
          <span>
            © {new Date().getFullYear()} Gradient. Built for discovery.
          </span>
          <span className="footer-status">
            <span className="status-dot" />
            Demo and module research · Source availability varies
          </span>
          <a
            href="https://github.com/arjun-vaidya/flow_hackathon/issues"
            target="_blank"
            rel="noreferrer"
          >
            Feedback
            <ArrowRight size={12} />
          </a>
        </div>
      </footer>
      <Dialog
        open={about}
        onOpenChange={setAbout}
        title="A preview of Gradient"
        description="Demo scenarios and connected research have separate data sources."
      >
        <div className="dialog-body">
          <p>
            Demo mode uses three fictional builders for every thesis. Research
            modules mode starts a backend run and displays only the outputs
            returned by registered modules, with citations and unresolved
            questions.
          </p>
          <p>
            Saved links stay in this browser. Module runs are currently held in
            memory: they expire after one hour, server restart, or capacity
            eviction. Export a brief to keep a copy. Authentication and shared
            workspaces are not connected.
          </p>
          <div className="integration-grid">
            {[
              'NicrronNinoo · reasoning',
              'Akta · company context',
              'Roundtable · agent handoffs',
              'PRISM · evaluations',
            ].map((label) => (
              <div key={label}>
                <strong>{label}</strong>
                <span>Planned · not connected</span>
              </div>
            ))}
          </div>
        </div>
      </Dialog>
      {notice && (
        <div className="toast" role="status">
          {notice}
          <button
            className="icon-button"
            aria-label="Dismiss notification"
            onClick={() => setNotice('')}
          >
            <X size={15} />
          </button>
        </div>
      )}
    </>
  )
}

function Discover() {
  const [thesis, setThesis] = useState('')
  const [mode, setMode] = useState('demo')
  const [starting, setStarting] = useState(false)
  const [startError, setStartError] = useState('')
  const [step, setStep] = useState<number | null>(null)
  const navigate = useNavigate()
  useEffect(() => {
    if (step === null) return
    const timer = setTimeout(() => {
      if (step < stages.length - 1) setStep(step + 1)
      else navigate(`/shortlist?thesis=${encodeURIComponent(thesis.trim())}`)
    }, 650)
    return () => clearTimeout(timer)
  }, [step, thesis, navigate])
  async function start() {
    if (!thesis.trim() || step !== null || starting) return
    if (mode === 'demo') {
      setStep(0)
      return
    }
    setStarting(true)
    setStartError('')
    try {
      const run = await api.startRun(thesis.trim())
      navigate(`/runs/${run.run_id}`)
    } catch (error) {
      setStartError(
        error instanceof Error
          ? error.message
          : 'Cannot connect to research server.',
      )
    } finally {
      setStarting(false)
    }
  }
  return (
    <main className="discovery">
      <div className="hero-brand">
        <h1>Gradient</h1>
        <p className="brand-subtitle">VENTURE INTELLIGENCE</p>
      </div>
      <div className="filter-tabs mode-tabs" aria-label="Research mode">
        <button
          disabled={starting || step !== null}
          aria-pressed={mode === 'demo'}
          className={mode === 'demo' ? 'active' : ''}
          onClick={() => setMode('demo')}
        >
          Demo
        </button>
        <button
          disabled={starting || step !== null}
          aria-pressed={mode === 'modules'}
          className={mode === 'modules' ? 'active' : ''}
          onClick={() => setMode('modules')}
        >
          Research modules
        </button>
      </div>
      {startError && (
        <p className="note-box" role="alert">
          {startError}
        </p>
      )}
      <form
        className="search-panel"
        onSubmit={(event) => {
          event.preventDefault()
          start()
        }}
      >
        <label htmlFor="thesis" className="eyebrow">
          WHAT ARE YOU LOOKING FOR?
        </label>
        <div className="search-input-row">
          <Search size={23} strokeWidth={1.5} />
          <input
            id="thesis"
            autoComplete="off"
            placeholder="e.g. Tools for testing and monitoring AI agents"
            maxLength={500}
            value={thesis}
            disabled={step !== null || starting}
            onChange={(event) => setThesis(event.target.value)}
            onKeyDown={(event) => {
              if ((event.metaKey || event.ctrlKey) && event.key === 'Enter') {
                event.preventDefault()
                start()
              }
            }}
          />
        </div>
        <div className="search-bottom">
          <span>
            <ShieldCheck size={14} />
            Public signals. Evidence you can inspect.
          </span>
          <button
            className="button primary"
            disabled={!thesis.trim() || step !== null || starting}
          >
            {step !== null || starting ? (
              <>
                <LoaderCircle className="spin" size={16} />
                {starting ? 'Starting research…' : 'Exploring demo…'}
              </>
            ) : (
              <>
                Find opportunities
                <ArrowRight size={17} />
              </>
            )}
          </button>
        </div>
      </form>
      <div className="explore">
        <span>Try a thesis</span>
        {topics.map((topic) => (
          <button
            disabled={step !== null || starting}
            key={topic}
            onClick={() => setThesis(topic)}
          >
            {topic}
            <ArrowRight size={12} />
          </button>
        ))}
      </div>
      {step !== null && (
        <section className="research-progress" aria-live="polite">
          <div>
            <span className="eyebrow">SIMULATED RESEARCH</span>
            <button className="text-button" onClick={() => setStep(null)}>
              Cancel
            </button>
          </div>
          {stages.map((label, index) => (
            <p className={index > step ? 'pending' : ''} key={label}>
              {index < step ? (
                <Check size={15} />
              ) : index === step ? (
                <LoaderCircle size={15} className="spin" />
              ) : (
                <span className="empty-dot" />
              )}
              {label}
            </p>
          ))}
        </section>
      )}
    </main>
  )
}

function Empty({ title, text }: { title: string; text: string }) {
  return (
    <div className="empty-state">
      <Compass size={30} strokeWidth={1.3} />
      <h2>{title}</h2>
      <p>{text}</p>
      <Link className="button primary" to="/">
        Explore a thesis
        <ArrowRight size={15} />
      </Link>
    </div>
  )
}

function Shortlist({
  saved,
  toggle,
  savedOnly = false,
}: {
  saved: string[]
  toggle: (id: string) => void
  savedOnly?: boolean
}) {
  const location = useLocation()
  const runId = new URLSearchParams(location.search).get('run') ?? undefined
  const { data: run } = useQuery({
    queryKey: ['run', runId],
    queryFn: () => api.getRun(runId!),
    enabled: !!runId,
    refetchInterval: (query) =>
      ['queued', 'running'].includes(query.state.data?.status ?? '')
        ? 700
        : false,
    retry: false,
  })
  const {
    data: result,
    isPending,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ['opportunities', runId, savedOnly ? saved : null],
    queryFn: async () =>
      savedOnly
        ? api.listSaved(saved)
        : {
            items: await api.listOpportunities(runId),
            unavailable: [] as string[],
          },
    refetchInterval:
      runId && (!run || ['queued', 'running'].includes(run.status))
        ? 1500
        : false,
    retry: false,
  })
  const data = result?.items ?? []
  useEffect(() => {
    if (run && !['queued', 'running'].includes(run.status)) void refetch()
  }, [run?.status, refetch])
  const [filter, setFilter] = useState('All recommendations')
  const [selected, setSelected] = useState<string[]>([])
  const [comparing, setComparing] = useState(false)
  const [evidence, setEvidence] = useState<Evidence | null>(null)
  const thesis =
    new URLSearchParams(location.search).get('thesis') ||
    run?.thesis ||
    (runId ? 'Research results' : 'AI agent monitoring')
  const available = data.filter((item) => !savedOnly || saved.includes(item.id))
  const visible = available.filter(
    (item) =>
      filter === 'All recommendations' || item.recommendation === filter,
  )
  const compared = data.filter((item) => selected.includes(item.id))
  return (
    <main className="page shortlist-page">
      <div className="breadcrumb">
        <Link to="/">Workspace</Link>
        <ChevronRight size={12} />
        {savedOnly ? 'Saved builders' : 'Discovery shortlist'}
      </div>
      <div className="page-heading">
        <div>
          <span className="eyebrow">
            {savedOnly ? 'YOUR RESEARCH SHELF' : 'FOLLOW THE DEMAND'}
          </span>
          <h1>
            {savedOnly
              ? 'Keep the promising ones close.'
              : 'Builders worth a closer look.'}
          </h1>
          <p>
            {savedOnly
              ? 'A few conversations to come back to. Saved locally in this browser.'
              : 'The signal, the timing, and the questions still worth asking.'}
          </p>
        </div>
        <button
          className="button secondary"
          disabled={selected.length !== 2}
          onClick={() => setComparing(true)}
        >
          <Layers3 size={15} />
          Compare {selected.length > 0 ? `(${selected.length}/2)` : 'builders'}
        </button>
      </div>
      <div className="results-toolbar">
        <span className="thesis-chip">
          <Search size={14} />
          {savedOnly ? 'Saved opportunities' : thesis}
        </span>
        <span className="result-count">{available.length} opportunities</span>
        <span className="demo-inline">
          {runId
            ? run?.mode === 'demo'
              ? 'SYNTHETIC MODULE RESULTS'
              : 'MODULE RESULTS'
            : savedOnly
              ? 'SAVED RESEARCH'
              : 'DEMO DATA'}
        </span>
        <Link to="/" className="text-button">
          Edit thesis
          <SlidersHorizontal size={14} />
        </Link>
      </div>
      {!savedOnly && !runId && (
        <p className="fixture-note">
          Example AI infrastructure results · this preview uses the same
          fictional builders for every thesis.
        </p>
      )}
      {runId && (
        <p className="fixture-note">
          <Link to={`/runs/${runId}`}>View module progress and warnings</Link> ·
          Results update as modules finish.
        </p>
      )}
      {result?.unavailable.map((id) => (
        <p className="note-box" key={id}>
          Saved brief unavailable: the run may have expired or the server is
          offline.
          <button className="text-button" onClick={() => toggle(id)}>
            Remove saved link
          </button>
        </p>
      ))}
      {error && (
        <p role="alert" className="note-box">
          {error.message}
        </p>
      )}
      <div className="filter-tabs" aria-label="Filter recommendations">
        {['All recommendations', ...recommendations].map((label) => (
          <button
            aria-pressed={filter === label}
            className={filter === label ? 'active' : ''}
            key={label}
            onClick={() => setFilter(label)}
          >
            {label}
            {label === 'All recommendations' && <span>{available.length}</span>}
          </button>
        ))}
      </div>
      {isPending ? (
        <div className="empty-state" role="status">
          <LoaderCircle className="spin" />
          Loading opportunities…
        </div>
      ) : isError ? (
        <div className="empty-state">
          <h2>Couldn’t load the shortlist.</h2>
          <button className="button primary" onClick={() => refetch()}>
            Try again
          </button>
        </div>
      ) : visible.length === 0 ? (
        <Empty
          title={
            savedOnly && available.length === 0
              ? 'Your research shelf is ready.'
              : 'No builders in this view.'
          }
          text={
            savedOnly && available.length === 0
              ? 'Save a builder from the shortlist to keep their brief here.'
              : runId
                ? 'Modules have not supplied a matching, cited builder yet. Check module progress for details.'
                : 'Choose another recommendation filter to see more builders.'
          }
        />
      ) : (
        <div className="opportunity-list">
          {visible.map((item, index) => (
            <article className="opportunity-card" key={item.id}>
              <div className="card-heading">
                <div className={`avatar avatar-${item.id}`}>
                  {item.initials}
                </div>
                <div className="builder-title">
                  <div>
                    <Link to={`/builders/${item.id}`}>{item.name}</Link>
                    <span className="title-dot">·</span>
                    <span>{item.project}</span>
                  </div>
                  <p>
                    <Github size={12} />
                    {item.handle}
                    <span>·</span>
                    {item.runId
                      ? `Review: ${item.reviewStatus}`
                      : 'Public maintainer in demo'}
                  </p>
                </div>
                <Badge value={item.recommendation} />
                <SaveButton item={item} saved={saved} toggle={toggle} compact />
              </div>
              {item.isDemo && (
                <p className="fixture-note">Synthetic integration fixture</p>
              )}
              <p className="opportunity-description">{item.description}</p>
              <div className="signal-grid">
                <div>
                  <span className="eyebrow">
                    <Users size={12} />
                    STRONGEST DEMAND SIGNAL
                  </span>
                  <p>{item.demand}</p>
                </div>
                <div>
                  <span className="eyebrow">
                    <GitBranch size={12} />
                    WHY NOW
                  </span>
                  <p>{item.trigger}</p>
                </div>
                <div>
                  <span className="eyebrow">
                    <Search size={12} />
                    STILL UNKNOWN
                  </span>
                  <p>{item.uncertainty}</p>
                </div>
              </div>
              {index === 0 && (
                <div className="card-evidence">
                  <span className="eyebrow">A CLOSER LOOK AT THE SIGNAL</span>
                  <div>
                    {item.evidence.slice(0, 2).map((source) => (
                      <button
                        key={source.id}
                        className="quote-preview"
                        onClick={() => setEvidence(source)}
                      >
                        <span>“{source.quote}”</span>
                        <small>
                          {source.source}
                          <ArrowRight size={13} />
                        </small>
                      </button>
                    ))}
                  </div>
                </div>
              )}
              <div className="card-footer">
                <label className="compare-checkbox">
                  <input
                    type="checkbox"
                    aria-label={`Compare ${item.project}`}
                    checked={selected.includes(item.id)}
                    disabled={
                      selected.length === 2 && !selected.includes(item.id)
                    }
                    onChange={() =>
                      setSelected(
                        selected.includes(item.id)
                          ? selected.filter((id) => id !== item.id)
                          : [...selected, item.id],
                      )
                    }
                  />
                  Compare<span className="sr-only"> {item.project}</span>
                </label>
                <span className="category-label">{item.category}</span>
                <Link
                  to={`/builders/${item.id}`}
                  className="text-button strong"
                >
                  Open builder brief
                  <ArrowRight size={15} />
                </Link>
              </div>
            </article>
          ))}
        </div>
      )}
      <div className="end-note">
        <CheckCheck size={16} />
        Every recommendation includes its uncertainty. Every claim has a place
        to look closer.
      </div>
      <EvidenceDialog evidence={evidence} close={() => setEvidence(null)} />
      <Dialog
        open={comparing}
        onOpenChange={setComparing}
        title="Two builders, side by side"
        description="Compare the evidence, its limitations, and what you would need to learn next."
        wide
      >
        <div className="comparison-grid">
          {compared.map((item) => (
            <article key={item.id}>
              <span className="eyebrow">{item.project}</span>
              <h2>{item.name}</h2>
              <Badge value={item.recommendation} />
              <h3>Demand</h3>
              <p>{item.demand}</p>
              <h3>Why now</h3>
              <p>{item.trigger}</p>
              <h3>Unknown</h3>
              <p>{item.uncertainty}</p>
              <Link
                className="text-button"
                to={`/builders/${item.id}`}
                onClick={() => setComparing(false)}
              >
                Read brief
                <ArrowRight size={14} />
              </Link>
            </article>
          ))}
        </div>
      </Dialog>
    </main>
  )
}

function EvidenceDialog({
  evidence,
  close,
}: {
  evidence: Evidence | null
  close: () => void
}) {
  return (
    <Dialog
      open={!!evidence}
      onOpenChange={(open) => {
        if (!open) close()
      }}
      title={evidence?.title ?? 'Evidence'}
      description={
        evidence?.sourceUrl
          ? 'Source excerpt supplied by a research module. Inspect the original and its limitations.'
          : 'Synthetic source excerpt · created to demonstrate the evidence review workflow.'
      }
    >
      {evidence && (
        <div className="dialog-body">
          <div className="source-meta">
            <span className="source-tag">{evidence.kind}</span>
            <span>{evidence.date}</span>
          </div>
          <blockquote>“{evidence.quote}”</blockquote>
          <p className="muted">
            {evidence.author} · {evidence.source}
          </p>
          <h3>What this supports</h3>
          <p>{evidence.interpretation}</p>
          <h3>What it doesn’t establish</h3>
          <p>{evidence.limitation}</p>
          <div className="note-box">
            {evidence.sourceUrl ? (
              <a href={evidence.sourceUrl} target="_blank" rel="noreferrer">
                Open original source ↗
              </a>
            ) : (
              'This is a fictional excerpt, with no external source URL.'
            )}
            {evidence.isDemo && ' Synthetic integration fixture.'}
          </div>
        </div>
      )}
    </Dialog>
  )
}

function Brief({
  saved,
  toggle,
}: {
  saved: string[]
  toggle: (id: string) => void
}) {
  const { id = '' } = useParams()
  const runId = id.includes(':') ? id.split(':')[0] : undefined
  const { data: run } = useQuery({
    queryKey: ['run', runId],
    queryFn: () => api.getRun(runId!),
    enabled: !!runId,
    refetchInterval: (query) =>
      ['queued', 'running'].includes(query.state.data?.status ?? '')
        ? 700
        : false,
    retry: false,
  })
  const {
    data: item,
    isPending,
    isError,
    error: briefError,
    refetch,
  } = useQuery({
    queryKey: ['opportunity', id],
    queryFn: () => api.getOpportunity(id),
    refetchInterval:
      runId && (!run || ['queued', 'running'].includes(run.status))
        ? 1500
        : false,
    retry: false,
  })
  useEffect(() => {
    if (run && !['queued', 'running'].includes(run.status)) void refetch()
  }, [run?.status, refetch])
  const [evidence, setEvidence] = useState<Evidence | null>(null)
  const [kind, setKind] = useState('All evidence')
  useEffect(() => {
    setKind('All evidence')
  }, [id])
  function download() {
    if (!item) return
    const content = `# ${item.project} — ${item.name}\n\n${item.runId && !item.isDemo ? `MODULE RESEARCH — REVIEW: ${item.reviewStatus}` : 'FICTIONAL DEMO — NOT VERIFIED RESEARCH'}\n\nRecommendation: ${item.recommendation}\n\n${item.thesis}\n\n## Demand\n${item.demand}\n\n## Why now\n${item.trigger}\n\n## Unknown\n${item.uncertainty}\n\n## Evidence${item.runId && !item.isDemo ? '' : ' (synthetic)'}\n${item.evidence.map((source) => `### ${source.title}\n${source.source} · ${source.date} · ${source.kind}\n\n> ${source.quote}\n\nInterpretation: ${source.interpretation}\nLimitation: ${source.limitation}\nSource: ${source.sourceUrl ?? 'Synthetic fixture'}`).join('\n\n')}\n\n## Meeting questions\n${item.questions.map((question) => `- ${question}`).join('\n')}`
    const url = URL.createObjectURL(
      new Blob([content], { type: 'text/markdown' }),
    )
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = `gradient-${item.id.replaceAll(':', '-')}-${item.runId ? 'research' : 'demo'}-brief.md`
    anchor.click()
    setTimeout(() => URL.revokeObjectURL(url), 1000)
  }
  if (isPending)
    return (
      <main className="page empty-state" role="status">
        Loading brief…
      </main>
    )
  if (isError)
    return (
      <main className="page empty-state">
        <h2>Couldn’t load this brief.</h2>
        <p>{briefError?.message}</p>
        <button className="button primary" onClick={() => refetch()}>
          Try again
        </button>
      </main>
    )
  if (!item)
    return (
      <main className="page">
        <Empty
          title="Builder not found."
          text="Explore the shortlist to open an available brief."
        />
      </main>
    )
  return (
    <main className="page brief-page">
      <div className="breadcrumb">
        <Link to={item.runId ? `/shortlist?run=${item.runId}` : '/shortlist'}>
          <ArrowLeft size={12} />
          Opportunities
        </Link>
        <ChevronRight size={12} />
        {item.category}
        <ChevronRight size={12} />
        {item.name}
      </div>
      <div className="page-heading brief-heading">
        <div>
          <div className="eyebrow">
            BUILDER BRIEF{' '}
            <span className="demo-inline">
              {item.runId && !item.isDemo
                ? `REVIEW: ${item.reviewStatus}`
                : 'DEMO DATA'}
            </span>
          </div>
          <h1>
            {item.project}
            <span className="project-dot" />
          </h1>
          <p>
            Built by {item.name} <span>·</span> Company formation unconfirmed
          </p>
        </div>
        <div className="button-group">
          <button className="button secondary" onClick={download}>
            <Download size={15} />
            Export brief
          </button>
          <SaveButton item={item} saved={saved} toggle={toggle} />
        </div>
      </div>
      <div className="brief-layout">
        <div className="brief-main">
          <section className="thesis-card">
            <div className="eyebrow">
              <Sparkles size={14} />
              THE INVESTMENT QUESTION
            </div>
            <h2>
              {item.runId && item.reviewStatus !== 'reviewed'
                ? 'What does the evidence establish?'
                : item.recommendation === 'Worth a conversation'
                  ? 'The users are asking. Is there a company here?'
                  : item.recommendation === 'Needs validation'
                    ? 'There is interest. Is the problem recurring?'
                    : 'A relevant problem. A distinct answer?'}
            </h2>
            <p>{item.thesis}</p>
            <Badge value={item.recommendation} />
          </section>
          <div className="brief-reasons">
            <article>
              <span className="eyebrow">
                {item.runId ? 'PROJECT DESCRIPTION' : 'WHY IT FITS'}
              </span>
              <p>{item.description}</p>
            </article>
            <article>
              <span className="eyebrow">WHY NOW</span>
              <p>{item.trigger}</p>
            </article>
            <article>
              <span className="eyebrow">WHAT’S UNCERTAIN</span>
              <p>{item.uncertainty}</p>
            </article>
          </div>
          <section className="brief-section">
            <div className="section-heading">
              <h2>
                {item.runId && item.reviewStatus !== 'reviewed'
                  ? 'Sources awaiting review.'
                  : 'Demand, in their words.'}
              </h2>
              <span className="eyebrow">
                {item.runId && !item.isDemo
                  ? 'MODULE EVIDENCE'
                  : 'SYNTHETIC · LAST 90 DAYS'}
              </span>
            </div>
            <p className="muted">
              Look for a problem that repeats, and people asking for a better
              answer.
            </p>
            <div className="metric-grid">
              <div>
                <strong>
                  {item.participants === null
                    ? 'Unknown'
                    : String(item.participants).padStart(2, '0')}
                </strong>
                <span>Public participants</span>
              </div>
              <div>
                <strong>
                  {item.hosting === null
                    ? 'Unknown'
                    : String(item.hosting).padStart(2, '0')}
                </strong>
                <span>Hosting requests</span>
              </div>
              <div>
                <strong>
                  {item.payment === null
                    ? 'Unknown'
                    : String(item.payment).padStart(2, '0')}
                </strong>
                <span>Stated willingness to pay</span>
              </div>
            </div>
            <p className="metric-note">
              {item.runId
                ? 'Unknown counts have not been established by the research modules.'
                : 'Illustrative counts. Categories overlap; willingness to pay is not revenue.'}
            </p>
            <div className="filter-tabs compact">
              {[
                'All evidence',
                'Self-reported',
                'Observed',
                'Provider summary',
              ].map((label) => (
                <button
                  key={label}
                  className={kind === label ? 'active' : ''}
                  aria-pressed={kind === label}
                  onClick={() => setKind(label)}
                >
                  {label}
                </button>
              ))}
            </div>
            <div className="evidence-list">
              {item.evidence
                .filter(
                  (source) => kind === 'All evidence' || source.kind === kind,
                )
                .map((source) => (
                  <button
                    className="evidence-card"
                    key={source.id}
                    onClick={() => setEvidence(source)}
                  >
                    <div>
                      <span className="source-tag">{source.kind}</span>
                      <span>{source.date}</span>
                    </div>
                    <h3>
                      {source.title}
                      <ArrowRight size={15} />
                    </h3>
                    <p>“{source.quote}”</p>
                    <small>
                      <Github size={12} />
                      {source.source}
                    </small>
                  </button>
                ))}
              {!item.evidence.some(
                (source) => kind === 'All evidence' || source.kind === kind,
              ) && (
                <p className="note-box">
                  No {kind.toLowerCase()} evidence in this brief.
                </p>
              )}
            </div>
          </section>
          {item.activity.length > 0 && (
            <section className="brief-section">
              <div className="section-heading">
                <h2>A builder who keeps shipping.</h2>
                <span className="eyebrow">ILLUSTRATIVE ACTIVITY</span>
              </div>
              <p className="muted">
                Development activity is context, not proof of adoption.
              </p>
              <Suspense
                fallback={<p className="muted">Loading activity chart…</p>}
              >
                <ActivityChart activity={item.activity} />
              </Suspense>
            </section>
          )}
          <section className="brief-section">
            <div className="section-heading">
              <h2>The market question.</h2>
              <span className="source-tag">
                {item.runId
                  ? `Review: ${item.reviewStatus}`
                  : 'Research pending'}
              </span>
            </div>
            <p className="muted">
              {item.market ??
                'Company and competitor enrichment will appear here once connected. No competitive advantage has been verified.'}
            </p>
            {!item.runId && (
              <>
                <div className="market-row">
                  <span>Existing observability and evaluation platforms</span>
                  <span>Compare workflow depth</span>
                </div>
                <div className="market-row">
                  <span>Internal scripts and self-hosted tools</span>
                  <span>Validate switching pain</span>
                </div>
              </>
            )}
          </section>
          <section className="brief-section questions" id="meeting-questions">
            <span className="eyebrow">MAKE THE FIRST CONVERSATION COUNT</span>
            <h2>Start here, not with the pitch.</h2>
            <ol>
              {item.questions.map((question) => (
                <li key={question}>{question}</li>
              ))}
            </ol>
          </section>
        </div>
        <aside className="brief-sidebar">
          <section className="dossier">
            <span className="eyebrow">THE BUILDER</span>
            <div className={`avatar large avatar-${item.id}`}>
              {item.initials}
            </div>
            <h2>{item.name}</h2>
            <p>
              {item.runId
                ? 'Identity supplied by discovery module'
                : 'Project maintainer · fictional profile'}
            </p>
            <div className="profile-handle">
              <Github size={15} />
              {item.handle}
            </div>
            <dl>
              <div>
                <dt>Project relationship</dt>
                <dd>
                  {item.runId ? 'See identity evidence' : 'Maintainer in demo'}
                </dd>
              </div>
              <div>
                <dt>Company role</dt>
                <dd>Unknown</dd>
              </div>
              <div>
                <dt>Location</dt>
                <dd>Unknown</dd>
              </div>
              <div>
                <dt>Revenue</dt>
                <dd>Unknown</dd>
              </div>
              <div>
                <dt>Fundraising</dt>
                <dd>Unknown</dd>
              </div>
            </dl>
            <a href="#meeting-questions" className="button primary">
              Prepare for a meeting
              <ArrowDown size={14} />
            </a>
          </section>
          <section className="integrity-card">
            <ShieldCheck size={21} />
            <h3>Leave room for uncertainty.</h3>
            <p>
              Repository ownership does not prove company ownership. Public
              interest does not prove a business.
            </p>
            <div>
              <Check size={13} />
              Claims keep their context
            </div>
            <div>
              <Check size={13} />
              Unknowns stay visible
            </div>
            <div>
              <Check size={13} />
              No invented confidence score
            </div>
          </section>
        </aside>
      </div>
      <EvidenceDialog evidence={evidence} close={() => setEvidence(null)} />
    </main>
  )
}
