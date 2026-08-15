---
paths: ["web/**"]
---

# Web application rules

## Registry-driven, always

No hardcoded list of metrics, clubs, seasons, or chart options anywhere in
`web/`. Every picker, axis, label, unit and precision comes from the published
metric registry. If a screen needs a metric the registry does not have, the fix
is a registry entry, not a literal in a component.

The test of a correct implementation: adding a metric to `metrics.yml` and
rebuilding makes it appear in the comparison builder with no change under
`web/`.

## Component sourcing

Order of preference, strictly:

1. A component that already exists in `@hannasage/projection-ui`
2. A component that should exist there, contributed upstream first
3. A local component, only when it is genuinely specific to this application

Before writing any local component, state which of the three applies and why.
Charts, form controls, tables, popovers and layout primitives are almost always
category 1 or 2. Something like a fixture-difficulty strip is category 3.

Known gaps in the package as of v0.1.5, all category 2: scatter with quadrants,
radar, bump chart, sparkline, combobox with typeahead, tabs, tooltip or popover,
badge, pagination.

## Theming

The package themes through `--ui-*` CSS custom properties written by
`ThemeProvider`. Do not write raw hex values into components. The one permitted
exception is the preview image renderer, which cannot read custom properties.

Verified: the package fallback tokens give 15.47:1 for text on background and
6.56:1 for muted on background. Muted fails a 7.0:1 body-copy floor, so do not
use `--ui-muted` for prose. Labels and secondary chrome only.

## Data access

All queries go through the DuckDB-WASM worker. No fetching of Parquet into
JavaScript memory and filtering by hand. No JSON side-channel of pre-aggregated
values.

The worker initialises lazily after first paint. Every data-dependent surface
renders a skeleton state and must be navigable while the engine loads. Do not
block the first paint on the WASM bundle.

## Honesty in the interface

- A metric outside its `available_from` range renders as an explicit gap with
  the reason, never as an empty area or a zero.
- Constructed metrics are visibly marked as constructed everywhere they appear,
  including axis labels and preview images, and link to their definition.
- Every view names its sources on screen.
- A comparison spanning a capability tier boundary says so on the chart.

## Forbidden

- No export, download, "copy data", or print-to-CSV affordance of any kind
- No `<form>` submission to a route that returns data
- No advertising, payment, affiliate, or third-party tracking code
- No `localStorage` or `sessionStorage` for anything other than user interface
  preference such as theme choice
- No route under `app/api/` that returns dataset rows. Preview image generation
  is the only permitted dynamic route.

## Accessibility

WCAG 2.2 AA is the floor and it is computed, not eyeballed. 4.5:1 minimum,
7.0:1 for body copy, 11px minimum interface type, 10px minimum inside SVG,
44px minimum touch targets, `prefers-reduced-motion` respected, and no meaning
carried by colour alone. Multi-series charts carry distinct dash patterns
through to the legend.
