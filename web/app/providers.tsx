"use client";

import { ThemeProvider, type UITheme } from "@hannasage/projection-ui";

// Placeholder theme. The real design tokens land with the Explore surface. These
// values are chosen to clear the contrast floors in .claude/rules/web.md: text
// on background well above 7.0:1, muted above 4.5:1. Do not treat them as final.
const terraceTheme: UITheme = {
  bg: "#ffffff",
  surface: "#f5f6f8",
  border: "#d6dae0",
  text: "#14181f",
  muted: "#586173",
  primary: "#1d4ed8",
  primaryFg: "#ffffff",
  danger: "#b91c1c",
  font: 'system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif',
  radius: "soft",
};

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider theme={terraceTheme} style={{ minHeight: "100%" }}>
      {children}
    </ThemeProvider>
  );
}
