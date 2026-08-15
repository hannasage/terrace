"use client";

import { Badge, Button, Card } from "@hannasage/projection-ui";

// Scaffold smoke test. Renders components straight from @hannasage/projection-ui
// to confirm the package resolves, themes, and builds under the App Router. The
// Explore, Compare and Share surfaces replace this once the registry and the
// published Parquet artefacts exist. Nothing here is registry-driven yet, so it
// is deliberately the only screen that names no metric.
export default function Home() {
  return (
    <main
      style={{
        maxWidth: "48rem",
        margin: "0 auto",
        padding: "4rem 1.5rem",
        display: "flex",
        flexDirection: "column",
        gap: "1.5rem",
      }}
    >
      <Badge>Scaffold</Badge>
      <h1 style={{ fontSize: "2rem", lineHeight: 1.2 }}>Terrace</h1>
      <p style={{ color: "var(--ui-muted)", maxWidth: "36rem" }}>
        A personal tool for building comparisons out of Premier League data,
        1992/93 to the present. The pipeline, the metric registry and the
        comparison builder are not built yet. This page confirms the component
        library resolves and themes correctly.
      </p>
      <Card padding="lg">
        <p style={{ marginBottom: "1rem" }}>
          Rendered from <code>@hannasage/projection-ui</code>.
        </p>
        <Button variant="primary">Placeholder action</Button>
      </Card>
    </main>
  );
}
