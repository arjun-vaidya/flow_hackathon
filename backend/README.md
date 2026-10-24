# Gradient backend

Modular source collection for Peter's single-process backend plan. Each source implements `DataSource.collect()`. The coordinator starts independent requests concurrently, ingests each finished result, and calls an organizer with the current evidence snapshot. The organizer can return follow-up requests without changing the scheduling code.

**Implemented:** GitHub public repository/issue/comment collection, Akta news/company adapters, source registration, bounded scheduling, per-source outcomes, progress callbacks, evidence normalization/deduplication, and a FastAPI collection endpoint.

**Not implemented:** Nicrron reasoning, the LangGraph Scout/Market/Verifier graph, Roundtable persistence, PRISM tracing/evaluation, website crawling, durable jobs, authentication, or durable shared workspaces. The current response has `phase: "collection"` and empty `briefs`. A complete collection is not a completed investment recommendation. No missing integration is simulated as successful.

## Research module integration

The separate research-module scheduler and frontend connection are implemented in `gradient/integration/`. Peter supplies Scout/Market/Verifier implementations; the integration collects their typed outputs, validates references, combines them into opportunities, and serves progress, partial results, cancellation and briefs. See [the module handoff](../docs/MODULE_INTEGRATION.md) for the contract, ownership split, registration, API routes and explicit synthetic test harness. Without registered implementations, modules report unavailable.

The collection endpoint below retains its original behavior and is not the endpoint used by the new research UI.

## Local setup

From the repository root, using Python 3.11+:

```sh
python3 -m venv backend/.venv
backend/.venv/bin/pip install -r backend/requirements-dev.lock -e 'backend[dev]'
backend/.venv/bin/uvicorn gradient.main:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/docs` for interactive API documentation. Run one Uvicorn worker: concurrency admission is an in-memory lock, not a distributed lock. This is a local development service; public deployment still needs authentication and deployment controls.

Optional credentials: copy `.env.example` to `backend/.env`, supply your own `GITHUB_TOKEN` / `AKTA_API_KEY`, and add `--env-file backend/.env` to the launch command. The GitHub adapter works without a token subject to public rate limits. Akta reports `unavailable` when its key is absent. Secrets are only sent in provider-specific request headers.

## API

- `GET /healthz`: process health and current `collection` phase.
- `GET /api/sources`: source names, supported operations, and credential availability.
- `POST /api/research`: await collection and return evidence, grouped subjects, events, source results, and warnings.

```json
{
  "thesis": "Find builders working on debugging AI agents",
  "github_query": "agent debugging in:name,description",
  "sources": ["github", "akta"]
}
```

Until thesis planning is connected, `github_query` is sent directly to GitHub search. If omitted, the thesis is used literally; the server does not claim to interpret it. Akta receives the thesis as an open-ended news query. Both run concurrently.

For agent-directed work, pass explicit requests instead:

```json
{
  "thesis": "Research commercial context for a known company",
  "requests": [
    {"source": "akta", "operation": "company", "query": "KNOWN_AKTA_UUID"},
    {"source": "akta", "operation": "news", "query": "agent evaluation", "limit": 3}
  ]
}
```

Company enrichment requires a known company identifier accepted by Akta. It does not establish a company relationship for a GitHub maintainer. Website access is not part of this adapter.

HTTP 200 can contain `complete` or `partial` collection results. HTTP 502 means no source completed usefully; 504 means no useful result before timeouts; 429 rejects overlapping runs. All source outcomes remain inspectable. A successful empty search counts as a completed source, with no evidence or fabricated brief.

## Extension contract

```python
class YourSource:
    @property
    def info(self) -> SourceInfo:
        return SourceInfo(name="your-source", operations=("search",), available=True)

    async def collect(self, request: SourceRequest) -> SourceBatch:
        # Fetch a permitted source, normalize its records into Evidence, and
        # return partial with warnings when coverage is incomplete.
        ...

registry.register(YourSource())
```

Each `Evidence` record has a stable provider/item ID, a public or explicitly authenticated citation URL, a subject ID, excerpt, attribution label, optional stable author ID/publication date, and collection timestamp. `evidence_id` is returned with every record and referenced by groups. Separate comments remain distinct; repeated posts from one account count as one participant within the group. Participant IDs are **not** independent customer or demand counts. No fuzzy name-based entity merging is performed.

The main research extension is `ResultOrganizer.on_result(thesis, result, evidence)`. It runs after each source result, including failures, and can return a tuple of `SourceRequest`s. For example, an agent can request Akta enrichment once it has an explicitly supported company identifier. Every follow-up passes through the same registry, deduplication, limits, and timeouts. Create one organizer per run; store agent history there, not on shared source instances. The default `EvidenceOrganizer` only groups evidence through the store; it makes no model calls.

`ResearchCoordinator.run(..., on_progress=listener)` emits queued/running/terminal events. A callback can later publish these to SSE or a run store; the HTTP route currently returns the event history with the final result. Adapters do not write shared state. The coordinator owns the evidence store, and snapshots contain immutable records.

### Bounds and cancellation

- 120 seconds per run; 20 seconds per source call/organizer callback.
- Up to three source calls in flight, eight admitted requests including follow-ups.
- At most six repositories reserved across GitHub search requests and ten total issue/comment records per repository visit.
- Up to 100 deduplicated evidence records in the combined store.
- Duplicate source/operation/query requests are not rerun; no automatic retries that could repeat paid calls.
- Slow/failed sources do not erase successful results. The run cancels unfinished work at its deadline. Parent task cancellation also cancels child work.
- Source implementations must use cancellation-friendly async I/O and must not suppress `CancelledError` or block the event loop. The contract cannot forcibly stop an arbitrary blocking plug-in.

GitHub discovery is a bounded best-match sample, not comprehensive coverage. Current GitHub collection does not fetch READMEs, profiles, releases, or discussions. Akta summaries retain `provider_summary` attribution; they are not quoted as original article text. The company record citation points to Akta's API rather than falsely attributing enrichment claims to the company's homepage. Structural URL validation does not independently verify the cited content.

## Verification

```sh
cd backend
.venv/bin/pytest -q
.venv/bin/ruff check gradient tests examples
.venv/bin/pyrefly check
.venv/bin/python examples/live_github.py
```

Unit/integration tests use fake sources and HTTPX mock transports; they spend no sponsor credits. The optional final command makes a small live public GitHub request. Akta's request/response mappings are tested against documented fixtures; live sponsor access still needs verification.

API contracts consulted: [GitHub repository search](https://docs.github.com/en/rest/search/search#search-repositories), [Akta news](https://docs.akta.pro/docs/news-signals/quick-start), and [Akta company enrichment](https://docs.akta.pro/docs/company-data/quick-start).
