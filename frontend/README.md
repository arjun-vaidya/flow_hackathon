# Gradient frontend

React + TypeScript + Vite implementation of the supplied discovery, shortlist, and founder-brief designs. Uses Tailwind CSS with custom component styles, Radix dialog primitives in a shadcn-style wrapper, React Router, TanStack Query, Recharts, and Lucide icons.

## Run

Use Node 22.12+ (or a supported newer release) and npm.

```sh
cd frontend
npm ci
npm run dev
```

Open the local address printed by Vite, normally `http://127.0.0.1:5173`.

```sh
npm run build
npm test
npm run preview
```

For a browser smoke check, keep `npm run dev` running in another terminal and run `npm run test:browser`. The check uses installed Google Chrome in an isolated headless context and saves desktop/mobile screenshots to the ignored `test-results/` folder. Override `GRADIENT_PREVIEW_URL` if Vite uses a different port.

## Working flows

- Enter a thesis or choose a suggested one; start or cancel simulated research.
- Browse and filter three fictional opportunities; compare two side by side.
- Open a builder brief, inspect source excerpts and limitations, and filter evidence.
- Save builders in browser local storage and revisit them at `/saved`.
- Export a labeled synthetic Markdown brief, including evidence and meeting questions.
- Use responsive layouts, keyboard navigation, and focus-managed dialogs.

## Connect the backend

`src/lib/api.ts` supports both local demo fixtures and the research-module API. Select **Research modules** to start a real backend run, inspect per-module progress and view assembled shortlist/brief results. Set `VITE_API_URL` (default `http://127.0.0.1:8000`). API failures never fall back to demo data. See [the integration handoff](../docs/MODULE_INTEGRATION.md) for backend setup and `npm run test:integration`.

Saved links remain local to this browser. Server runs expire after one hour, restart, or capacity eviction; export briefs for a retained copy. Workspace-scoped persistent storage and authentication remain pending.

`src/data/opportunities.ts` contains entirely synthetic data. Demo-mode searches return the same three example builders and make no sponsor calls. Research mode uses the configured backend; live discovery requires Peter’s registered research implementations. Shared accounts are not implemented. Never add sponsor API secrets to browser code or `VITE_*` variables.

Static hosting must rewrite non-asset paths to `index.html` for React Router deep links. `vercel.json` supplies this when `frontend/` is selected as the Vercel project root. The backend remains a separate service.
