# Terrace report format

The house format for a Terrace report artifact. It is the working paper register:
a single file, sectioned, argued from evidence, with the constraints on the
evidence stated inline rather than tucked into a footnote.

Derived from FORMAT-STANDARD.md and from the Premier League working paper built
against it. Where this file and a reader's own instructions disagree, the reader
wins.

Read this with the skeleton in `template.jsx`. The skeleton is the shell, the
theming, the popover engine and one worked chart, all of it fixed. Copy it rather
than composing it, and spend the effort on the analysis instead.

---

## 1. Voice

**Em-dashes are banned outright**, prose and headers both. Commas, colons, or two
sentences. En-dashes too. A reader searching the output for one finds nothing.

**Banned vocabulary.** delve, leverage, robust, pivotal, crucial, seamless,
tapestry, testament, underscore, boasts, nuanced, multifaceted, landscape, realm,
navigate, foster, garner, showcase, intricate, notably, importantly.

**Banned transition glue.** moreover, furthermore, consequently, "it is important
to note".

**Banned constructions.**

- Contrastive framing. "not just X, but Y". "isn't merely, it's".
- Rhetorical question then answer. "What changed? The math did."
- A pivot to grand abstraction at the end of a section.
- Reflexive three part rhythmic lists. An intentional triplet is fine. Every
  paragraph wearing one is not.

Vary sentence length. Minimal bold. Terminal periods dropped from section titles.
No summary paragraph closing every section. Rationale and process notes stay in
the chat, never in the artifact.

## 2. Structure

One panel mounted at a time, never a long scroll. Five panels is the target:

1. **The brief.** Abstract, the thesis, a reading key, a glossary, the equations
   for anything constructed.
2. **The ranking.** The headline ordering, with the clubs that carry too little
   evidence listed separately rather than ranked badly.
3. **The matrix.** The underlying grid, sortable, every value visible.
4. **One overlay.** The comparison or second layer the question actually asked
   for.
5. **Sources.** The validation card, then the numbered bibliography.

Nine panels is the ceiling and it costs more than it returns. Five carries every
honesty surface at roughly 40 percent of the length.

Shell furniture, all of it in the skeleton: a sticky compact letterhead with a
position counter, a dropdown section nav (not a horizontal scroll strip, not a
wrapped grid, both were built and rejected), and a prev/next pager with
truncating labels.

## 3. Type and surface

Syne 800 for display, DM Mono for eyebrows, labels and all data, DM Sans for
body. Sharp 2px radius, hairline rules, no gradients. Every font declaration
carries a fallback stack, so a blocked font fetch degrades instead of breaking.

Single column at base, widening at `min-width: 720px`.

## 4. Themes

Two themes ship, one dark and one light, swapped by the palette selector in the
skeleton. `report_style` returns the resolved pair with their full tokens. Never
invent a palette: every colour comes from the vendored registry.

Theming is CSS custom properties scoped by `data-theme` on the root element. No
context, no prop drilling, no localStorage. The selector is tri state: system,
dark, light, with the system preference watched live.

`report_style` also returns computed contrast for each theme. Read it before
assigning a colour a job:

- `text` and `muted` are safe for words in every theme.
- `accent` is not. In some light themes it sits below the 4.5:1 text floor
  against its own background, and `accent_safe_for_text` says so per theme. Where
  it is false, accent is a graphical colour only. Never set body text, a label or
  a source marker in it.
- Check `accent_safe_for_graphics` before using accent for a gridline or another
  essential graphical object, which need 3.0:1.

## 5. Charts

Hand rolled SVG. No chart library: the artifact sandbox cannot install one, and
the idiom below is shorter than configuring one anyway.

Fixed conventions, held without exception:

- A fixed `viewBox` with named margins, `W H L R T B`.
- Two scale functions, always named `px` and `py`, linear, with the domain stated
  as explicit bounds rather than derived silently from the data.
- Gridlines from a literal tick array, `stroke="var(--grid)"`, the tick label a
  sibling `text` in the same `g`.
- Every `text` inside a chart is `aria-hidden="true"`, DM Mono, 10px minimum.
- The chart itself is `role="img"` with an `aria-label` that reads the whole
  series in words. Generate it from the data, do not summarise it.
- A legend below, whose swatches are mini inline SVGs reproducing the exact
  stroke, dash and fill used in the chart.
- Dots carry a `stroke="var(--bg)"` halo so overlaps stay readable.

**Meaning never rests on colour alone.** The dash vocabulary is fixed:

| Pattern | Meaning |
|---|---|
| solid | observed, a reported figure |
| `3 2` | constructed or estimated, not reported |
| `6 3` | the second series in a head to head |
| `2 3` | a reference line, such as a league average |

Estimates are hollow and dashed. Positive and negative values keep their signs,
printed, so no reading depends on colour. Where a cell is tinted by band, the
number is printed too, so colour is a second reading rather than the only one.

## 6. Honesty surfaces

These are the reason the format exists. None is optional.

**Observed against constructed.** Observed quantities keep their common names.
Constructed quantities take capitalised acronyms and are defined in the glossary
with their formula in the equations table. State the rule in the reading key, then
hold it. A constructed value is never described as a measurement. Where a
threshold or weight was chosen, the equations note says it was chosen: "the chosen
yardstick, not a law."

**Gaps.** A gap is a finding, never a zero and never interpolated.

- In a line chart, split the series into contiguous runs and draw each as its own
  polyline. The gap is literal empty space, and the legend says what it means.
- In a table, the null render is the words `No figure`. Not a dash, not a blank,
  not a zero.
- Where a whole layer is missing, a `No comparable figure` block states why the
  gap exists and why the obvious substitute was rejected. A partial figure that
  would mislead is worse than an absent one, and the block says so.

**Sources.** Raised bracketed `[n]` markers in the accent colour where contrast
allows, otherwise in text colour, keyed to a numbered bibliography grouped by
role. Position them with `vertical-align: baseline` plus `position: relative` and
`top: -0.32em`, not `vertical-align: super`, which fights the line height. A
marker is annotation, never a highlight.

**Validation card.** Open the sources panel by naming the arithmetic checks that
were actually run and passed. Follow it with where the evidence is thinnest. An
honest limitation section is worth more than a confident one.

## 7. Accessibility

WCAG 2.2 AA is the floor and it is computed, never eyeballed. `report_style`
returns the ratios; use them.

- 4.5:1 minimum, 7.0:1 for body copy, verified against both themes.
- 3.0:1 for gridlines and essential graphical objects.
- 11px minimum for UI type, 10px minimum for SVG type.
- No meaning in colour alone.
- 44px minimum touch targets. `prefers-reduced-motion` respected. Disabled
  controls at 0.45 opacity or higher.
- Span and superscript triggers get their own `focus-visible` rules.
- The known trap is a hardcoded hex inside SVG that bypasses the token palette.
  Every fill and stroke reads a `var(--token)`.
