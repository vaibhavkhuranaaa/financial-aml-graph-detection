# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

AML analytics leaders, ML hiring managers, and risk/compliance recruiters reviewing a portfolio case study. They need to understand how a bounded research workflow supports analyst review without mistaking it for a production decision.

## Product Purpose

Signal Ledger is a recruiter-facing research workbench that demonstrates a time-bound transaction-monitoring review: timeline, bounded graph context, precomputed research rank, human rationale, and an audit record.

## Positioning

It makes both a simulated escalation and a simulated closure inspectable using realistic synthetic banking data while exposing the data, model, and deployment limits in the same experience.

## Capabilities and Constraints

React and TypeScript front end; FastAPI public fixture API; precomputed scores and explanations only; browser-memory simulated decisions; strict response and graph limits; no live feeds or visitor-request inference. Elliptic remains local-only and must never be served. The project is building, non-production, and not compliance advice.

## Evidence on Hand

Public IBM AML-Data v8 source is used for the deterministic scenario fixture. Exact source and slice checksums are recorded in the fixture provenance. Local Elliptic research artifacts are excluded from the public surface.

## Product Principles

- Human review, not automated conclusions.
- Provenance and limitations are first-class evidence.
- Bounded public data only.
- Simulated outcomes never accuse real people or entities.

## Accessibility & Inclusion

Keyboard-operable controls, visible focus, reduced-motion support, and clear loading, empty, and error recovery states are required.
