export type Recommendation =
  'Worth a conversation' | 'Needs validation' | 'Watch'
export type Evidence = {
  id: string
  title: string
  quote: string
  kind: 'Observed' | 'Self-reported' | 'Provider summary'
  sourceUrl?: string
  isDemo?: boolean
  author: string
  source: string
  date: string
  interpretation: string
  limitation: string
}
export type Opportunity = {
  id: string
  name: string
  initials: string
  project: string
  handle: string
  recommendation: Recommendation
  category: string
  description: string
  demand: string
  trigger: string
  uncertainty: string
  thesis: string
  runId?: string
  isDemo?: boolean
  reviewStatus?: string
  market?: string
  participants: number | null
  hosting: number | null
  payment: number | null
  evidence: Evidence[]
  questions: string[]
  activity: { month: string; contributions: number }[]
}

// Synthetic fixtures only. Names, projects, quotations, and activity are invented.
export const opportunities: Opportunity[] = [
  {
    id: 'tracenest',
    name: 'Maya Chen',
    initials: 'MC',
    project: 'TraceNest',
    handle: 'maya-builds',
    category: 'Agent observability',
    recommendation: 'Worth a conversation',
    description:
      'An open-source replay and debugging toolkit for AI agents. Users are asking for a hosted version before the builder has launched one.',
    demand:
      'Two independent users requested managed hosting; one also expressed willingness to pay.',
    trigger:
      'A second hosting request appeared after the latest deterministic replay release.',
    uncertainty:
      'Company formation, revenue, and willingness to build a business are unknown.',
    thesis:
      'A developer workflow with visible friction and early demand for a managed product. The opportunity is to meet the builder before a company story becomes obvious.',
    participants: 6,
    hosting: 2,
    payment: 1,
    evidence: [
      {
        id: 'tn-1',
        title: 'A request for managed hosting',
        quote:
          'We keep running this locally to reproduce agent failures. Is a hosted version on the roadmap? We would pay to avoid maintaining it ourselves.',
        kind: 'Self-reported',
        author: 'Demo participant A',
        source: 'Synthetic GitHub discussion #42',
        date: 'Oct 18, 2026',
        interpretation:
          'Explicit willingness to pay, attached to a concrete maintenance problem.',
        limitation:
          'A stated preference is not a purchase or proof of production usage.',
      },
      {
        id: 'tn-2',
        title: 'A second team asks for a shared workspace',
        quote:
          'Can we share replay sessions across our team without running a separate server? A managed workspace would make this much easier.',
        kind: 'Self-reported',
        author: 'Demo participant B',
        source: 'Synthetic GitHub issue #57',
        date: 'Oct 21, 2026',
        interpretation:
          'An independent request for a managed collaboration workflow.',
        limitation:
          'Team size, budget, and organizational identity are unverified.',
      },
      {
        id: 'tn-3',
        title: 'Replay support shipped',
        quote:
          'Release 0.4 introduces deterministic replay and a session comparison view.',
        kind: 'Observed',
        author: 'Demo maintainer',
        source: 'Synthetic release v0.4',
        date: 'Oct 16, 2026',
        interpretation:
          'The fixture records a shipped response to an existing workflow problem.',
        limitation:
          'A release alone does not establish reliability, adoption, or commercial traction.',
      },
    ],
    questions: [
      'Walk me through the last real agent failure someone used TraceNest to debug.',
      'What would the two teams requesting hosting need before they paid?',
      'Do you want to build a company around this, and what would make you commit?',
      'Which parts of the workflow are poorly served by existing observability tools?',
    ],
    activity: [
      { month: 'May', contributions: 8 },
      { month: 'Jun', contributions: 11 },
      { month: 'Jul', contributions: 15 },
      { month: 'Aug', contributions: 22 },
      { month: 'Sep', contributions: 31 },
      { month: 'Oct', contributions: 43 },
    ],
  },
  {
    id: 'agentcanvas',
    name: 'Eli Brooks',
    initials: 'EB',
    project: 'AgentCanvas',
    handle: 'eli-canvas',
    category: 'Agent development',
    recommendation: 'Needs validation',
    description:
      'A visual workbench for building agent workflows. Strong community curiosity, with limited evidence of a recurring business use case.',
    demand:
      'Developers are exploring the interface; repeat usage and buying intent remain unproven.',
    trigger:
      'A new workflow-sharing release attracted questions from several contributors.',
    uncertainty:
      'Interest may reflect experimentation rather than a problem teams will pay to solve.',
    thesis:
      'An approachable product in an active category. First establish whether users return to solve the same expensive problem.',
    participants: 4,
    hosting: 0,
    payment: 0,
    evidence: [
      {
        id: 'ac-1',
        title: 'Interest in workflow sharing',
        quote:
          'This looks useful for experimenting. Can I share a workflow with someone who does not have it installed?',
        kind: 'Self-reported',
        author: 'Demo participant C',
        source: 'Synthetic GitHub discussion #19',
        date: 'Oct 20, 2026',
        interpretation:
          'A concrete feature request, but no evidence of paid or repeated usage.',
        limitation:
          'Curiosity and a feature request do not establish customer demand.',
      },
    ],
    questions: [
      'Who uses this every week, and what are they replacing?',
      'Which workflow costs users enough time that they would pay?',
      'What did you learn from users who tried the product and stopped?',
    ],
    activity: [
      { month: 'May', contributions: 6 },
      { month: 'Jun', contributions: 12 },
      { month: 'Jul', contributions: 19 },
      { month: 'Aug', contributions: 18 },
      { month: 'Sep', contributions: 26 },
      { month: 'Oct', contributions: 29 },
    ],
  },
  {
    id: 'evaldock',
    name: 'Sam Rivera',
    initials: 'SR',
    project: 'EvalDock',
    handle: 'sam-evals',
    category: 'Agent evaluation',
    recommendation: 'Watch',
    description:
      'A lightweight evaluation runner for agent deployments. Practical production discussions, but differentiation needs a closer look.',
    demand:
      'One participant describes a deployment use case; independent adoption is not established.',
    trigger:
      'Recent discussions focus on integrating evaluation checks into release pipelines.',
    uncertainty:
      'The advantage over established evaluation tools is not yet supported by evidence.',
    thesis:
      'The problem is relevant to production teams. Watch for a distinctive workflow and repeat demand beyond a single discussion.',
    participants: 3,
    hosting: 0,
    payment: 0,
    evidence: [
      {
        id: 'ed-1',
        title: 'A deployment workflow question',
        quote:
          'We are evaluating this for our release pipeline. Can the runner fail a build when an agent regression is detected?',
        kind: 'Self-reported',
        author: 'Demo participant D',
        source: 'Synthetic GitHub issue #31',
        date: 'Oct 17, 2026',
        interpretation:
          'A potential production workflow, still at the evaluation stage.',
        limitation: 'No confirmed deployment or independent proof of adoption.',
      },
    ],
    questions: [
      'Why would a team choose EvalDock over its current evaluation stack?',
      'Has the pipeline integration moved beyond an experiment?',
      'What signal would convince you the product solves a recurring problem?',
    ],
    activity: [
      { month: 'May', contributions: 10 },
      { month: 'Jun', contributions: 9 },
      { month: 'Jul', contributions: 14 },
      { month: 'Aug', contributions: 17 },
      { month: 'Sep', contributions: 18 },
      { month: 'Oct', contributions: 20 },
    ],
  },
]
