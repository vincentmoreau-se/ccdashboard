# Frontend (React + Vite + TypeScript)

SPA consuming the backend API. Run all commands from `frontend/`.

## Commands

```bash
npm install
npm run dev        # Vite dev server on :5173 (expects backend on :8000)
npm run build      # tsc -b && vite build
npm test           # Vitest unit tests (jsdom)
npm run test:e2e   # Playwright browser e2e (boots backend+frontend itself)
```

## Structure

| Path | Responsibility |
|---|---|
| `src/api/client.ts` | typed fetchers + TS interfaces mirroring backend models |
| `src/api/sse.ts` | `subscribeLive` EventSource wrapper (reconnect on error) |
| `src/lib/format.ts` | `formatTokens`, `formatCost`, `formatDuration` |
| `src/components/` | `KpiCard`, `UnknownCostBadge`, `CostTokenChart` |
| `src/pages/` | `Overview`, `Projects`, `ProjectDetail`, `Session`, `Live` |
| `src/App.tsx` / `main.tsx` | router + QueryClient/Router providers |

## Conventions

- **Data fetching:** TanStack Query (`useQuery`), keyed by route param. Each
  page reads currency via `queryKey: ["config"]` and passes it to `formatCost`
  (fallback `"€"` while loading) — no hardcoded currency symbols.
- **Types:** `src/api/client.ts` interfaces must stay in lockstep with backend
  Pydantic models; backend `datetime|None` maps to `string|null`.
- **Unknown cost:** render `UnknownCostBadge` wherever a cost may be unknown;
  `formatCost(value, currency, known)` returns `"n/a"` when `!known`.
- **Charts:** Recharts with `isAnimationActive={false}` — the enter-animation
  renders blank in headless capture and adds no value here; keep it off.
- **Live page** is the only SSE consumer; everything else is REST.

## Testing

- Unit (Vitest): logic + light component smoke tests; `src/test/setup.ts` wires
  `@testing-library/jest-dom` (referenced from `vite.config.ts` `setupFiles`).
  `test.include` is scoped to `src/**` so Vitest ignores the Playwright spec.
- E2E (`tests/e2e/`, `@playwright/test`): structural assertions resilient to
  variable real data; screenshots → `docs/superpowers/e2e-screenshots/`
  (gitignored). `playwright.config.ts` auto-boots both servers.
