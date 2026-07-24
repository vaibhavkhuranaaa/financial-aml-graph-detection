---
name: Signal Ledger
description: Bounded synthetic research workbench
colors:
  ink: "#10171c"
  surface: "#172126"
  grid: "#405059"
  text: "#edf2df"
  evidence: "#c6ee48"
  focus: "#f38b4b"
typography:
  display: {fontFamily: "ui-sans-serif, system-ui, sans-serif", fontSize: "clamp(1.9rem, 4vw, 3.4rem)", fontWeight: 700, lineHeight: 1, letterSpacing: "-0.04em"}
  body: {fontFamily: "ui-sans-serif, system-ui, sans-serif", fontSize: "0.88rem", fontWeight: 400, lineHeight: 1.5}
rounded: {none: "0"}
spacing: {compact: "16px", desk: "30px", section: "62px"}
components:
  queue-row: {backgroundColor: "{colors.surface}", textColor: "{colors.text}", padding: "15px"}
---

## Overview

Signal Ledger is an operate-mode casefile console. It makes a bounded synthetic graph investigation feel inspectable while keeping research limitations in the same visual field as the queue.

## Colors

Midnight ink and blue-black surfaces evoke a review desk under low ambient light. Acid evidence green marks public-fixture status, selected score values, and focus states. Archive orange identifies a graph convergence node and cautionary evidence; it is never a success state.

## Typography

Use the system sans for reading and controls. Reserve the system monospace stack for identifiers, scores, small evidence stamps, and measurements. Large headings are tight but never tighter than -0.04em.

## Layout

Desktop centers a three-part evidence desk: research queue, canvas graph, investigation brief. Below 960px, the desk becomes a clear linear reading order. The graph is a real SVG canvas, not a decorative background.

## Elevation & Depth

Use ruled separators and tonal surface changes; avoid floating cards and decorative blur.

## Shapes

The interface is square-edged and archival. Pills are limited to compact, factual signal tags.

## Components

Queue rows are full-width buttons with visible keyboard focus. Graph nodes use green for exits, orange for the current focal point, and muted green-gray for supporting topology. Every load failure has a plain recovery action.

## Do's and Don'ts

Do keep synthetic status, bounded behavior, and limitations visible. Do not use compliance, alert, finding, or production language for fixture content. Do not turn scores into decisions or threshold recommendations.
