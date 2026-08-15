# web

The Terrace web application. Next.js App Router, built on
`@hannasage/projection-ui`, with data queried in the browser by DuckDB-WASM over
static Parquet. There is no backend.

## Scripts

```
npm run dev             # local development server
npm run build           # production build
npm run start           # serve the production build
npm run lint            # eslint
npm run typecheck       # tsc --noEmit
npm run audit:contrast  # computed WCAG contrast audit (stub)
```

See `.claude/rules/web.md` for the rules that govern this directory: registry
driven always, component sourcing order, theming through `--ui-*` tokens, data
access through the worker, honesty in the interface, and the accessibility
floor.
