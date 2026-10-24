# Gradient: product and build plan

## Customer and hypothesis

**Buyer:** a pre-seed fund investing in AI infrastructure or developer tools.

**User:** an associate, partner, or scout deciding which builders merit a meeting.

**Hypothesis:** repeated, specific public demand for a builder's work can help an investor discover and assess opportunities beyond popularity metrics and standard company lists.

Success means new, meeting-worthy opportunities with verifiable evidence and less review time. It does not mean predicting investment returns, proving product-market fit, or predicting a funding round.

## Market context

Broad founder search is competitive. [Harmonic](https://support.harmonic.ai/en/articles/12844015-harmonic-integrations-playbook) offers thesis-driven research, monitoring, and briefs. [Evertrace](https://www.evertrace.ai/) monitors early founder signals across multiple sources. [GitDealFlow](https://gitdealflow.com/) analyzes public engineering activity. An open-source [OSS Opportunity Radar](https://github.com/wushidiguo/opportunity-radar) already mines issues for commercialization opportunities.

Gradient's proposed focus is the complete investor decision: connect independently expressed demand to the builder, commercial alternatives, timing, and counter-evidence, with inspectable sources. This is a differentiation hypothesis to validate, not a claim that no competitor offers it.

Investor guidance supports investigating adoption and community engagement beyond stars: [Bessemer](https://www.bvp.com/atlas/measuring-the-engagement-of-an-open-source-software-community) and [Unusual Ventures](https://www.unusual.vc/field-guide/series-a-fundraising-for-an-open-source-company/). These sources do not validate Gradient's performance or willingness to pay.

## End-to-end workflow

1. **Thesis:** accept a sector, stage, and optional geography; derive explicit inclusion and exclusion criteria through Nicrron.
2. **Discovery:** use reproducible GitHub searches to discover a bounded set of relevant public repositories. Save the search and collection time.
3. **Evidence:** collect descriptions, releases, issues, comments, and discussions. Separate requests, reported usage, willingness to pay, and general interest.
4. **Builder identification:** connect repositories to explicitly linked public profiles and companies. Preserve uncertainty when identity or company formation is unconfirmed.
5. **Market context:** use Akta to research companies, competing products, and relevant news. Missing coverage remains unknown.
6. **Verification:** check citations, identity links, independent demand, dates, and contradictory evidence. Revise or remove unsupported claims.
7. **Shortlist:** rank candidates against the fund's criteria, then generate three readable briefs and first-meeting questions.

## Agent responsibilities and sponsor roles

The demo uses three tool-calling agents in one LangGraph StateGraph. Each has role-specific instructions, restricted tools, run-local history, and structured output. Agents choose source queries; code validates results, controls graph transitions, and enforces budgets. [Backend design and agent graph](BACKEND_DESIGN.md) owns the demo's execution limits and API.

| Agent | Functional responsibility and tools | Structured result |
| --- | --- | --- |
| Scout | Interpret the thesis, choose GitHub searches, and inspect project demand and explicit builder links. | Candidates, sourced demand, identity uncertainty. |
| Market Researcher | Choose Akta company, competitor, and news queries to assess commercial alternatives and contrary evidence. | Attributed commercial context and unknowns. |
| Verifier | Read evidence by ID, reread permitted original sources, assess claim support, and request a targeted Scout or Market Researcher repair. | Claim reviews and an optional research request. |

First pass: Scout → Market Researcher → Verifier → code router. The router sends at most one targeted repair to Scout or Market Researcher, then returns directly to Verifier. Final code checks citation references, deduplicates source/account IDs, and ranks reviewed candidates. Unresolved claims become unknown or are omitted when the repair allowance is spent. Model review remains fallible.

Shared graph state contains thesis/criteria, candidates, evidence, reviews, artifact references, and remaining budgets. Roundtable stores versioned agent outputs and task messages; downstream agents read the recorded predecessor version. All model calls use Nicrron. PRISM receives actual exchanges with shared run/session identity plus agent and graph-version labels.

Verify tool-capable model support, sponsor APIs, and account access before implementation.

## Evidence contract

Each evidence item should include:

- Source URL and source type.
- Source event date when available, plus collection time.
- Relevant passage or structured source fields.
- Claim the item supports.
- Whether the statement is observed, self-reported, inferred, or unknown.
- Identity-link evidence and any contradictory information.

Deduplicate comments and participants so repeated posts do not become independent demand. Multiple model opinions about the same source do not count as independent evidence.

| Source observation | Permitted conclusion | Unsupported conclusion |
| --- | --- | --- |
| A repository has many stars | Public interest | Paying customers or revenue |
| A commenter describes deployment | Self-reported usage | Independently verified production adoption |
| A user requests paid hosting | Expressed commercial interest | A completed purchase |
| A profile lists an employer | Stated affiliation | The employer is a customer |
| A person maintains a repository | Public maintainer identity | They founded a company or want VC funding |
| No funding record is found | Funding status unknown | The project is unfunded |

Rank opportunities for human review. Do not present arbitrary founder-quality scores as predictions of personal ability or startup success.

## Interface

### 1. Search

Thesis, sector, optional geography, and a clear indication of which data sources are covered. Do not silently exclude unknown locations.

### 2. Shortlist

Three opportunities with a plain-language rationale, recent trigger, evidence strength, and unknowns. Avoid rewarding popularity by default.

### 3. Founder brief

Builder, shipped product, demand timeline, fund fit, competitors, counter-evidence, citations, and questions for a first meeting.

**Ambitious feature:** a clickable evidence map connecting a user problem to a project, builder, commercial context, and fund fit. Every connection opens its supporting evidence.

Potential design-partner suggestions are an extension. Suggested companies must be labeled as prospects; do not imply existing customer relationships or offer introductions the fund cannot make.

## Hackathon scope

- One sector: AI developer infrastructure.
- A bounded discovery run across relevant public repositories.
- Three deeply researched candidate briefs.
- Working use of all four sponsor tools.
- Source links, a demand timeline, and explicit uncertainty.
- One genuine failure discovered and corrected, with PRISM evaluation evidence.

Defer broad industry coverage, bulk outreach, full CRM integrations, fundraising predictions, and private-network inference. Do not automatically contact founders or commenters.

## PRISM evaluation plan

The [event resources](https://nyc-vc-hack.devpost.com/resources) describe both 50+ initial agent runs and 20+ runs on fixed inputs. Budget for both, using named versions and a stable evaluation set.

1. Instrument the workflow before tuning it.
2. Collect initial runs across realistic inputs, including missing data and ambiguous identity cases.
3. Connect the editor to PRISM's MCP and investigate a real failure using its tools.
4. Add an evaluation rule through MCP, for example: customer claims require explicit source support.
5. Correct the application or prompt and rerun the same fixed inputs.
6. Demonstrate the actual v1/v2 result with trace identifiers. Do not intentionally weaken the baseline or fabricate improvement.

Additional useful evaluations: every factual claim has a supporting source; missing funding data stays unknown; repository maintainers are not automatically labeled founders; independent demand counts are deduplicated.

## Build order

- [ ] Verify access to Nicrron, Akta, Roundtable, and PRISM with one successful exchange each.
- [ ] Establish permitted use and display of sponsor data under the event accounts.
- [ ] Manually assemble one useful, sourced brief to define the target output.
- [ ] Implement thesis parsing and reproducible public project discovery.
- [ ] Collect and normalize evidence with source dates and provenance.
- [ ] Build the Scout, Market Researcher, and Verifier agent graph with Roundtable handoffs and bounded repair routing.
- [ ] Integrate Akta company and competitor research.
- [ ] Instrument and evaluate the workflow with PRISM.
- [ ] Build the three screens around the working pipeline.
- [ ] Complete the evidence map if the core workflow is reliable.
- [ ] Run the live demo and prepare the submission.

No item is complete at repository creation.

## Suggested collaboration split

For two builders, one owns discovery, evidence, and Akta; the other owns agent coordination, UI, and Nicrron. Both integrate PRISM early and share evaluation and demo preparation.

With a third builder, assign agent coordination and PRISM separately. With a fourth, assign customer discovery, research QA, and submission ownership. Use focused feature branches and pull requests into `main`.

## Validation and business model

Show real briefs to investors and record actual feedback:

- Which builders did you already know?
- Which would you meet, and why?
- What evidence is missing or misleading?
- Does this change your decision or save research time?
- Would you try a paid pilot, and what would it need to deliver?

Initial distribution: participating funds, developer-tool investors, and scouts. Test a recurring fund subscription through paid pilots; pricing and willingness to pay are unvalidated. Never invent interview results or describe AI-simulated feedback as customer evidence.

## Demo and submission

Demo a thesis, real discovery results, a candidate brief, original evidence, and the verified correction of a real failure. The ranking must follow evidence rather than a predetermined story about which project should win.

Required submission assets:

- [ ] Project name and description.
- [ ] Track 1: Sourcing and any sponsor award entry.
- [ ] One-page founder brief: problem, customer, interview evidence, market size, competition, business model, and why now.
- [ ] Description and evidence of actual use of all four sponsor tools.
- [ ] Code repository link.
- [ ] Live demo link.
- [ ] Demo video of three minutes or less.
- [ ] Live demonstration to judges.

The event judges design, uniqueness, technical execution, and business feasibility. A working, inspectable recommendation serves all four better than a broad interface with mocked integrations.

Target **October 24, 2026, 4:00 p.m. ET**. The official pages contain a conflicting 4:30 reference; use the earlier deadline unless organizers clarify. The content award has separate social-post requirements and is optional; publishing this repository does not enter it.
