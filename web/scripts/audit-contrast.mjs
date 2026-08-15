#!/usr/bin/env node
// WCAG contrast audit.
//
// Stub. Exits zero so the web CI job is wired end to end before the theme
// tokens are in place. Fill in when the application renders real surfaces.
//
// TODO, per .claude/rules/web.md "Accessibility":
//   - Read the resolved --ui-* token values for both themes from the built
//     output, never from eyeballing.
//   - Compute the contrast ratio for every text-on-background pairing.
//   - Fail with a non-zero exit if any pairing is below 4.5:1, or below 7.0:1
//     for body copy. Name the offending token pair and the measured ratio.
//   - The package fallback tokens are known: 15.47:1 text on background,
//     6.56:1 muted on background. Muted fails the 7.0:1 body floor, so it is
//     for labels and secondary chrome only.

console.log("audit:contrast: stub, no rendered surfaces to audit yet. Exiting 0.");
process.exit(0);
