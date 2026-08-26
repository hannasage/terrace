/*
 * Terrace report skeleton.
 *
 * Copy this whole file into the artifact, then do three things:
 *
 *   1. Replace THEMES with the two theme objects report_style returned. They
 *      paste in as they arrive, colors and planColors both. Do not retype a hex.
 *   2. Replace DATA and CITES with the real values from the query tools.
 *   3. Replace the panels. PanelBrief and PanelSources show the required shape;
 *      the middle panels are yours.
 *
 * Everything else is fixed: the shell, the theming, the popover engine, the
 * chart idiom. It works as it stands, so run it before editing and keep it
 * running as you go.
 *
 * The only import is React. The artifact sandbox installs nothing, so a chart
 * library is not an option, which is why the charts here are hand rolled SVG.
 */

import React, {
  useState,
  useRef,
  useEffect,
  useCallback,
  useMemo,
  createContext,
  useContext,
} from "react";

/* ------------------------------------------------------------------ themes */
/* Replace both objects with the pair from report_style. Nothing else changes:
 * the CSS token block below is generated from whatever is here. */

const THEMES = [
  {
    id: "projection",
    name: "Projection",
    isDark: true,
    colors: {
      bg: "#07090C", surface: "#0D1117", faint: "#0A0E14", border: "#1B2535",
      text: "#DDE3EE", muted: "#8396AB", accent: "#C9F53A", dim: "#8CB025",
      blue: "#5B9CF6", orange: "#F97316", red: "#F87171", purple: "#C084FC",
      textOnAccent: "#07090C",
    },
    planColors: [
      { label: "Chartreuse", value: "#C9F53A" },
      { label: "Sky", value: "#5B9CF6" },
      { label: "Tangerine", value: "#F97316" },
      { label: "Lavender", value: "#C084FC" },
      { label: "Coral", value: "#F87171" },
      { label: "Mint", value: "#34D399" },
      { label: "Gold", value: "#FBBF24" },
      { label: "Rose", value: "#FB7185" },
      { label: "Cyan", value: "#22D3EE" },
      { label: "Slate", value: "#94A3B8" },
    ],
  },
  {
    id: "coastal-day",
    name: "Coastal Day",
    isDark: false,
    colors: {
      bg: "#f6f8fa", surface: "#ffffff", faint: "#f0f3f6", border: "#d0d7de",
      text: "#24292f", muted: "#57606a", accent: "#0969da", dim: "#0550ae",
      blue: "#218bff", orange: "#bc4c00", red: "#cf222e", purple: "#8250df",
      textOnAccent: "#ffffff",
    },
    planColors: [
      { label: "Navy", value: "#023047" },
      { label: "Ocean", value: "#0e7490" },
      { label: "Rust", value: "#9a3800" },
      { label: "Dusk", value: "#4a2890" },
      { label: "Crimson", value: "#b01828" },
      { label: "Moss", value: "#2a6040" },
      { label: "Amber", value: "#7a5000" },
      { label: "Berry", value: "#842050" },
      { label: "Lagoon", value: "#006880" },
      { label: "Slate", value: "#4a5568" },
    ],
  },
];

const DARK = THEMES.find((t) => t.isDark) || THEMES[0];
const LIGHT = THEMES.find((t) => !t.isDark) || THEMES[0];

/* ------------------------------------------------------------- report data */
/* Replace with tool output. Two shapes matter and both come straight from the
 * query tools: a series keyed by season, and a gap that stays a gap.
 *
 * A season a club did not play is ABSENT from the series map. Absence is the
 * gap signal: it breaks a line and prints "No figure" in a table. Never write a
 * zero, and never carry a season forward to fill a hole. */

const META = {
  title: "Report title",
  subtitle: "One line saying what was asked and over what range",
  metric: "Points",
  metricKind: "constructed", // straight from list_metrics
  metricDefinition: "docs/metrics/points.md",
  sources: ["engsoccerdata", "football-data"],
};

const SEASONS = ["2021/22", "2022/23", "2023/24", "2024/25"];

const DATA = {
  clubs: [
    {
      id: "arsenal",
      name: "Arsenal",
      short: "Arsenal",
      plan: 0, // index into planColors
      series: { "2021/22": 69, "2022/23": 84, "2023/24": 89, "2024/25": 74 },
    },
    {
      id: "luton-town",
      name: "Luton Town",
      short: "Luton",
      plan: 1,
      // 2023/24 only. The other seasons are absent, not zero.
      series: { "2023/24": 26 },
    },
  ],
};

const CITES = [
  {
    id: 1,
    group: "Season tables",
    title: "engsoccerdata, England results",
    publisher: "James Curley",
    date: "retrieved 2026",
    url: "https://github.com/jalapic/engsoccerdata",
  },
  {
    id: 2,
    group: "Cross-checks",
    title: "Football-Data.co.uk, England E0",
    publisher: "Football-Data",
    date: "retrieved 2026",
    url: "https://www.football-data.co.uk/englandm.php",
  },
];

const GAP_NOTE = "gap in a line = season outside the Premier League";
const NO_FIGURE = "No figure";

/* -------------------------------------------------------------------- css */

const rgba = (hex, a) => {
  const v = hex.replace("#", "");
  const n = parseInt(v.length === 3 ? v.replace(/./g, "$&$&") : v, 16);
  return `rgba(${(n >> 16) & 255},${(n >> 8) & 255},${n & 255},${a})`;
};

/* Derived tokens sit alongside the vendored ones so every fill and stroke can
 * read a var(). A hardcoded hex inside the SVG is the known trap. */
const tokenBlock = (t) => {
  const c = t.colors;
  const plan = t.planColors.map((p, i) => `--plan${i}:${p.value};`).join("");
  return `.tr-root[data-theme="${t.id}"]{
--bg:${c.bg};--surface:${c.surface};--faint:${c.faint};--line:${c.border};
--text:${c.text};--muted:${c.muted};--acc:${c.accent};--dim:${c.dim};
--accFg:${c.textOnAccent};--neg:${c.red};--grid:${c.border};
--lineSoft:${rgba(c.text, 0.09)};--zebra:${rgba(c.text, 0.035)};
--track:${rgba(c.text, 0.1)};--accSoft:${rgba(c.accent, 0.16)};
--negSoft:${rgba(c.red, 0.1)};--negLine:${rgba(c.red, 0.32)};
--headBg:${rgba(c.bg, 0.94)};--shadow:0 8px 32px ${rgba(c.bg, 0.8)};
${plan}}`;
};

const BASE_CSS = `
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@800&family=DM+Mono:wght@400;500&family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,700&display=swap');
.tr-root{--sp1:4px;--sp2:8px;--sp3:12px;--sp4:16px;--sp5:24px;--sp6:32px;--sp7:48px;
background:var(--bg);color:var(--text);min-height:100vh;
font-family:'DM Sans',system-ui,sans-serif;font-size:15px;line-height:1.62;
-webkit-font-smoothing:antialiased;}
.tr-root *{box-sizing:border-box;}
.wrap{max-width:900px;margin:0 auto;padding:0 var(--sp4) var(--sp7);}
.head{position:sticky;top:0;z-index:30;background:var(--headBg);
backdrop-filter:blur(8px);border-bottom:1px solid var(--line);
padding:var(--sp3) var(--sp4);display:flex;align-items:center;gap:var(--sp3);}
.head h1{font-family:'Syne',system-ui,sans-serif;font-weight:800;font-size:16px;
margin:0;letter-spacing:-0.01em;}
.count{font-family:'DM Mono',ui-monospace,monospace;font-size:11px;
color:var(--muted);margin-left:auto;}
.eyebrow{font-family:'DM Mono',ui-monospace,monospace;font-size:11px;
text-transform:uppercase;letter-spacing:0.08em;color:var(--muted);}
.faint{color:var(--muted);}
h2{font-family:'Syne',system-ui,sans-serif;font-weight:800;font-size:26px;
margin:var(--sp5) 0 var(--sp3);letter-spacing:-0.02em;}
h3{font-size:15px;margin:var(--sp5) 0 var(--sp2);font-weight:700;}
p{margin:0 0 var(--sp3);}
.sub{color:var(--muted);}
.card{background:var(--surface);border:1px solid var(--line);border-radius:2px;
padding:var(--sp4);margin:var(--sp3) 0;}
.grid{display:grid;grid-template-columns:1fr;gap:var(--sp3);}
@media(min-width:720px){.grid{grid-template-columns:repeat(2,1fr);}}
table{width:100%;border-collapse:collapse;font-family:'DM Mono',ui-monospace,monospace;
font-size:12px;}
th,td{text-align:right;padding:var(--sp2);border-bottom:1px solid var(--lineSoft);}
th:first-child,td:first-child{text-align:left;}
th{color:var(--muted);font-weight:500;text-transform:uppercase;font-size:10px;
letter-spacing:0.06em;}
tbody tr:nth-child(odd){background:var(--zebra);}
td.nofig{color:var(--muted);font-style:normal;}
.chart{margin:var(--sp4) 0;}
.chartbox{overflow-x:auto;}
.chart svg{width:100%;height:auto;display:block;}
.legend{display:flex;flex-wrap:wrap;gap:var(--sp3);margin-top:var(--sp2);
font-family:'DM Mono',ui-monospace,monospace;font-size:11px;color:var(--muted);}
.legend div{display:flex;align-items:center;gap:var(--sp1);}
.legend svg{width:20px;height:8px;flex:none;}
.nofig-block{border:1px dashed var(--line);border-radius:2px;padding:var(--sp4);
margin:var(--sp3) 0;background:var(--faint);}
.catch{border-left:2px solid var(--negLine);background:var(--negSoft);
padding:var(--sp3) var(--sp4);margin:var(--sp3) 0;}
.cite{font-family:'DM Mono',ui-monospace,monospace;font-size:11px;color:var(--acc);
background:none;border:0;padding:0 1px;cursor:pointer;position:relative;
top:-0.32em;vertical-align:baseline;line-height:1;}
.cite:focus-visible,.tw:focus-visible{outline:2px solid var(--acc);outline-offset:2px;}
.pop{position:fixed;z-index:60;max-width:320px;background:var(--surface);
border:1px solid var(--line);border-radius:2px;padding:var(--sp3);
box-shadow:var(--shadow);font-size:13px;}
.pop h4{margin:0 0 var(--sp1);font-size:11px;text-transform:uppercase;
letter-spacing:0.06em;color:var(--muted);font-family:'DM Mono',ui-monospace,monospace;}
.pop p{margin:0 0 var(--sp1);}
.pop a{color:var(--acc);}
.neg{color:var(--neg);}
.bar{display:flex;gap:var(--sp2);align-items:center;flex-wrap:wrap;
margin:var(--sp3) 0;}
.sel{position:relative;}
.sel>button,.pager button{font-family:'DM Mono',ui-monospace,monospace;font-size:12px;
background:var(--surface);color:var(--text);border:1px solid var(--line);
border-radius:2px;padding:var(--sp2) var(--sp3);cursor:pointer;min-height:44px;}
.sel>button[aria-expanded="true"]{border-color:var(--acc);}
.menu{position:absolute;top:calc(100% + 4px);left:0;z-index:40;min-width:220px;
background:var(--surface);border:1px solid var(--line);border-radius:2px;
box-shadow:var(--shadow);padding:var(--sp1);max-height:60vh;overflow:auto;}
.menu button{display:flex;width:100%;gap:var(--sp2);align-items:center;
background:none;border:0;color:var(--text);text-align:left;padding:var(--sp2);
cursor:pointer;font-size:13px;min-height:44px;}
.menu button[aria-current="true"]{color:var(--acc);}
.menu button:hover{background:var(--zebra);}
.dot{width:12px;height:12px;border-radius:2px;border:1px solid var(--lineSoft);
flex:none;}
.pager{display:flex;justify-content:space-between;gap:var(--sp2);
margin-top:var(--sp6);padding-top:var(--sp4);border-top:1px solid var(--line);}
.pager button:disabled{opacity:0.45;cursor:default;}
.gloss{margin:0;}
.gloss dt{font-family:'DM Mono',ui-monospace,monospace;font-size:12px;
color:var(--acc);margin-top:var(--sp3);}
.gloss dd{margin:0;color:var(--muted);font-size:14px;}
.colophon{margin-top:var(--sp7);padding-top:var(--sp4);
border-top:1px solid var(--line);font-size:12px;color:var(--muted);}
@media(prefers-reduced-motion:reduce){*{transition:none!important;
animation:none!important;}}
`;

const CSS = BASE_CSS + THEMES.map(tokenBlock).join("\n");

/* ---------------------------------------------------------- popover engine */
/* One shared engine for every annotation. Three behaviours were learned the
 * hard way and are load bearing: a delayed close so the pointer can travel into
 * the card, ignoring scroll for a moment after opening so the browser's own
 * focus scroll does not dismiss it on mobile, and tap toggles. */

const PopCtx = createContext(null);
const fine = () =>
  typeof window !== "undefined" &&
  window.matchMedia("(hover: hover) and (pointer: fine)").matches;

function PopHost({ children }) {
  const [pop, setPop] = useState(null);
  const timer = useRef(null);
  const openedAt = useRef(0);

  const close = useCallback(() => {
    clearTimeout(timer.current);
    setPop(null);
  }, []);

  const open = useCallback((id, node, rect) => {
    clearTimeout(timer.current);
    openedAt.current = Date.now();
    const w = Math.min(320, window.innerWidth - 24);
    let left = Math.min(Math.max(12, rect.left), window.innerWidth - w - 12);
    const below = window.innerHeight - rect.bottom;
    const flip = below < 180;
    setPop({
      id,
      node,
      style: {
        left,
        width: w,
        ...(flip
          ? { bottom: window.innerHeight - rect.top + 8 }
          : { top: rect.bottom + 8 }),
      },
    });
  }, []);

  const delayedClose = useCallback(() => {
    clearTimeout(timer.current);
    timer.current = setTimeout(() => setPop(null), 220);
  }, []);

  const hold = useCallback(() => clearTimeout(timer.current), []);

  useEffect(() => {
    if (!pop) return undefined;
    const onDown = (e) => {
      if (!e.target.closest(".pop") && !e.target.closest("[data-pop]")) close();
    };
    const onKey = (e) => e.key === "Escape" && close();
    const onScroll = () => {
      if (Date.now() - openedAt.current > 400) close();
    };
    document.addEventListener("mousedown", onDown);
    document.addEventListener("keydown", onKey);
    window.addEventListener("scroll", onScroll, true);
    return () => {
      document.removeEventListener("mousedown", onDown);
      document.removeEventListener("keydown", onKey);
      window.removeEventListener("scroll", onScroll, true);
    };
  }, [pop, close]);

  return (
    <PopCtx.Provider value={{ pop, open, close, delayedClose, hold }}>
      {children}
      {pop && (
        <div
          className="pop"
          style={pop.style}
          role="dialog"
          onMouseEnter={hold}
          onMouseLeave={delayedClose}
        >
          {pop.node}
        </div>
      )}
    </PopCtx.Provider>
  );
}

function Trigger({ id, node, as = "button", className, children, label, ...rest }) {
  const ctx = useContext(PopCtx);
  const ref = useRef(null);
  const As = as;
  const isOpen = ctx.pop && ctx.pop.id === id;

  const show = () => ctx.open(id, node, ref.current.getBoundingClientRect());

  return (
    <As
      ref={ref}
      data-pop
      type={as === "button" ? "button" : undefined}
      className={className}
      aria-label={label}
      aria-expanded={isOpen ? true : undefined}
      onClick={() => (isOpen ? ctx.close() : show())}
      onMouseEnter={() => fine() && show()}
      onMouseLeave={() => fine() && ctx.delayedClose()}
      {...rest}
    >
      {children}
    </As>
  );
}

function Cite({ n }) {
  const c = CITES.find((x) => x.id === n);
  if (!c) return null;
  const node = (
    <div>
      <h4>Source {c.id}</h4>
      <p>{c.title}</p>
      <p className="faint">
        {c.publisher}, {c.date}
      </p>
      <p>
        <a href={c.url} target="_blank" rel="noreferrer">
          Open source
        </a>
      </p>
    </div>
  );
  return (
    <Trigger id={"c" + n} node={node} className="cite" label={`Source ${n}: ${c.title}`}>
      [{n}]
    </Trigger>
  );
}

/* ------------------------------------------------------------------- chart */
/* The idiom, held without exception. Fixed viewBox with named margins, scales
 * named px and py with stated bounds, gridlines from a literal tick array,
 * every text aria-hidden, one role="img" with an aria-label that reads the
 * series in words, and a legend whose swatches reproduce the exact stroke.
 *
 * Gaps are the part to copy most carefully. segments() splits a series into
 * contiguous runs so an absent season becomes empty space, never a straight
 * line drawn across it. */

function segments(series) {
  const out = [];
  let run = [];
  SEASONS.forEach((s, i) => {
    const v = series[s];
    if (v === undefined || v === null) {
      if (run.length) out.push(run);
      run = [];
    } else {
      run.push([i, v]);
    }
  });
  if (run.length) out.push(run);
  return out;
}

function SeriesChart({ clubs, bounds = [0, 100], ticks = [0, 25, 50, 75, 100] }) {
  const W = 340, H = 216, L = 30, R = 12, T = 14, B = 34;
  const [lo, hi] = bounds;
  const px = (i) => L + (i / Math.max(1, SEASONS.length - 1)) * (W - L - R);
  const py = (v) => H - B - ((v - lo) / (hi - lo)) * (H - T - B);

  const desc =
    `${META.metric} by season. ` +
    clubs
      .map((c) => {
        const said = SEASONS.map((s) =>
          c.series[s] === undefined ? `${s} no figure` : `${s} ${c.series[s]}`
        ).join(", ");
        return `${c.name}: ${said}`;
      })
      .join("; ") +
    ".";

  return (
    <div className="chart">
      <div className="eyebrow faint">{META.metric} by season</div>
      <div className="chartbox">
        <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label={desc}>
          {ticks.map((v) => (
            <g key={v}>
              <line
                x1={L} x2={W - R} y1={py(v)} y2={py(v)}
                stroke="var(--grid)" strokeWidth="1" opacity="0.35"
              />
              <text
                x={L - 6} y={py(v) + 3} textAnchor="end" fill="var(--muted)"
                fontFamily="'DM Mono',monospace" fontSize="10" aria-hidden="true"
              >
                {v}
              </text>
            </g>
          ))}
          {SEASONS.map((s, i) => (
            <text
              key={s} x={px(i)} y={H - 10} textAnchor="middle" fill="var(--muted)"
              fontFamily="'DM Mono',monospace" fontSize="10" aria-hidden="true"
            >
              {s.slice(2)}
            </text>
          ))}
          {clubs.map((c, ci) => {
            const stroke = `var(--plan${c.plan})`;
            const dash = ci === 1 ? "6 3" : undefined;
            return (
              <g key={c.id}>
                {segments(c.series).map((run, ri) => (
                  <polyline
                    key={ri}
                    fill="none"
                    stroke={stroke}
                    strokeWidth="2"
                    strokeDasharray={dash}
                    points={run.map(([i, v]) => `${px(i)},${py(v)}`).join(" ")}
                  />
                ))}
                {segments(c.series)
                  .flat()
                  .map(([i, v]) => (
                    <circle
                      key={i} cx={px(i)} cy={py(v)} r="3.2"
                      fill={stroke} stroke="var(--bg)" strokeWidth="1"
                    />
                  ))}
              </g>
            );
          })}
        </svg>
      </div>
      <div className="legend">
        {clubs.map((c, ci) => (
          <div key={c.id}>
            <svg viewBox="0 0 20 8" aria-hidden="true">
              <line
                x1="0" x2="20" y1="4" y2="4"
                stroke={`var(--plan${c.plan})`} strokeWidth="2"
                strokeDasharray={ci === 1 ? "6 3" : undefined}
              />
            </svg>
            {c.name}
          </div>
        ))}
        <div>{GAP_NOTE}</div>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ panels */

function PanelBrief() {
  return (
    <section>
      <h2>The brief</h2>
      <p>
        State the question and the answer in the first two sentences. Say what the
        range is and why it was chosen.
        <Cite n={1} />
      </p>

      <div className="card">
        <h3>Reading key</h3>
        <p className="sub">
          Observed quantities keep their common names. Constructed quantities take
          capitalised acronyms and are defined below with their formula. The two
          are never used interchangeably. {META.metric} is{" "}
          <strong>{META.metricKind}</strong>, defined in {META.metricDefinition}.
        </p>
        <p className="sub">
          A season a club did not play carries no value. It shows as {NO_FIGURE} in
          a table and as a break in a line. It is never a zero.
        </p>
      </div>

      <h3>Glossary</h3>
      <dl className="gloss">
        <dt>{META.metric}</dt>
        <dd>Define the metric in one sentence, in the reader's terms.</dd>
      </dl>

      <h3>Equations</h3>
      <table>
        <thead>
          <tr><th>Term</th><th>Formula</th><th>Note</th></tr>
        </thead>
        <tbody>
          <tr>
            <td>{META.metric}</td>
            <td>3 x wins + draws</td>
            <td>A competition rule, not a law of the game.</td>
          </tr>
        </tbody>
      </table>
    </section>
  );
}

function PanelSeries() {
  return (
    <section>
      <h2>The series</h2>
      <SeriesChart clubs={DATA.clubs} />

      <table>
        <thead>
          <tr>
            <th>Club</th>
            {SEASONS.map((s) => (<th key={s}>{s}</th>))}
          </tr>
        </thead>
        <tbody>
          {DATA.clubs.map((c) => (
            <tr key={c.id}>
              <td>{c.name}</td>
              {SEASONS.map((s) => {
                const v = c.series[s];
                return v === undefined ? (
                  <td key={s} className="nofig"
                      aria-label={`${c.name}, ${s}, no figure`}>
                    {NO_FIGURE}
                  </td>
                ) : (
                  <td key={s}>{v}</td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>

      <div className="nofig-block">
        <h3>No comparable figure</h3>
        <p>
          Say which values are absent and why the gap exists. Then say why the
          obvious substitute was rejected: a partial figure that reads as complete
          is worse than an absent one.
        </p>
      </div>
    </section>
  );
}

function PanelSources() {
  const groups = [...new Set(CITES.map((c) => c.group))];
  return (
    <section>
      <h2>Sources</h2>

      <div className="card">
        <h3>Validation performed</h3>
        <p className="sub">
          Name the arithmetic checks that were actually run and passed. Every
          figure here comes from the Terrace pipeline, reconciled across{" "}
          {META.sources.join(" and ")}, with unmatched clubs failing the build
          rather than being guessed.
        </p>
      </div>

      <div className="catch">
        <h3>Where the evidence is thinnest</h3>
        <p>
          Say what a careful reader should distrust. An honest limitation is worth
          more than a confident summary.
        </p>
      </div>

      {groups.map((g) => (
        <div key={g}>
          <h3>{g}</h3>
          {CITES.filter((c) => c.group === g).map((c) => (
            <p key={c.id} className="sub">
              [{c.id}]{" "}
              <a href={c.url} target="_blank" rel="noreferrer">{c.title}</a>
              <br />
              {c.publisher}, {c.date}
            </p>
          ))}
        </div>
      ))}
    </section>
  );
}

const PANELS = [
  { n: "01", s: "The brief", C: PanelBrief },
  { n: "02", s: "The series", C: PanelSeries },
  { n: "03", s: "Sources", C: PanelSources },
];

/* --------------------------------------------------------------- selectors */

function Menu({ label, children, width }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);
  useEffect(() => {
    if (!open) return undefined;
    const onDown = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    };
    const onKey = (e) => e.key === "Escape" && setOpen(false);
    document.addEventListener("mousedown", onDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);
  return (
    <div className="sel" ref={ref}>
      <button type="button" aria-expanded={open} onClick={() => setOpen(!open)}>
        {label}
      </button>
      {open && (
        <div className="menu" style={width ? { minWidth: width } : undefined}
             onClick={() => setOpen(false)}>
          {children}
        </div>
      )}
    </div>
  );
}

/* Tri state: system, dark, light. The system preference is watched live and
 * nothing is stored, so the choice resets on reload by design. */
function PaletteSelector({ mode, setMode }) {
  const options = [
    { id: "system", name: "Auto", swatch: DARK.colors.accent },
    { id: DARK.id, name: DARK.name, swatch: DARK.colors.accent },
    { id: LIGHT.id, name: LIGHT.name, swatch: LIGHT.colors.accent },
  ];
  const current = options.find((o) => o.id === mode) || options[0];
  return (
    <Menu label={`Theme: ${current.name}`}>
      {options.map((o) => (
        <button key={o.id} type="button" aria-current={o.id === mode}
                onClick={() => setMode(o.id)}>
          <span className="dot" style={{ background: o.swatch }} />
          {o.name}
        </button>
      ))}
    </Menu>
  );
}

/* ------------------------------------------------------------------- shell */

function Shell() {
  const [i, setI] = useState(0);
  const [mode, setMode] = useState("system");
  const [sysDark, setSysDark] = useState(true);

  useEffect(() => {
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const sync = () => setSysDark(mq.matches);
    sync();
    mq.addEventListener("change", sync);
    return () => mq.removeEventListener("change", sync);
  }, []);

  const theme = mode === "system" ? (sysDark ? DARK.id : LIGHT.id) : mode;
  const Panel = PANELS[i].C;
  const css = useMemo(() => CSS, []);

  return (
    <div className="tr-root" data-theme={theme}>
      <style>{css}</style>
      <PopHost>
        <header className="head">
          <h1>{META.title}</h1>
          <span className="count">
            {PANELS[i].n} / {PANELS[PANELS.length - 1].n}
          </span>
        </header>

        <div className="wrap">
          <div className="bar">
            <Menu label={`${PANELS[i].n} ${PANELS[i].s}`} width={260}>
              {PANELS.map((p, k) => (
                <button key={p.n} type="button" aria-current={k === i}
                        onClick={() => setI(k)}>
                  <span className="eyebrow">{p.n}</span>
                  {p.s}
                </button>
              ))}
            </Menu>
            <PaletteSelector mode={mode} setMode={setMode} />
          </div>

          <p className="eyebrow faint">{META.subtitle}</p>

          <Panel />

          <nav className="pager">
            <button type="button" disabled={i === 0} onClick={() => setI(i - 1)}>
              {i === 0 ? "Start" : `Back: ${PANELS[i - 1].s}`}
            </button>
            <button type="button" disabled={i === PANELS.length - 1}
                    onClick={() => setI(i + 1)}>
              {i === PANELS.length - 1 ? "End" : `Next: ${PANELS[i + 1].s}`}
            </button>
          </nav>

          <div className="colophon">
            Built from the Terrace pipeline. Sources: {META.sources.join(", ")}.
            Constructed values are named as constructed and defined in the brief.
          </div>
        </div>
      </PopHost>
    </div>
  );
}

export default function App() {
  return <Shell />;
}
