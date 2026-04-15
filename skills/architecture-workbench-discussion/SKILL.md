---
name: architecture-workbench-discussion
description: Use when the user explicitly asks to checkpoint a long architecture or product discussion into a local workbench before planning, spec writing, or implementation. Do not use automatically for ordinary chat or every thread.
---

# Architecture Workbench Discussion

## Overview

This is a manual checkpointing skill for pre-plan discussion work.

Use it to turn a noisy design conversation into a small, reviewable workbench proposal.
Do not treat it as an always-on recorder.

## Manual Trigger Only

- Only use this skill when the user explicitly asks to record, checkpoint, consolidate, or prepare a discussion for planning.
- Do not auto-activate it just because a conversation looks architectural.
- Default to `propose`, not `apply`.

## Product Position

This skill is for:

- discussion-to-workbench consolidation
- pre-plan stabilization
- product and architecture threads with evolving terminology

This skill is not for:

- generic meeting notes
- passive automatic logging
- autonomous architecture decisions

## Artifact Budget

The default output budget is exactly three artifacts:

- `preplan-brief.md`
- `proposal.md`
- `transcript_bundle.json`

The machine-readable proposal for `apply` lives at `.internal/proposal.json`.

If more output seems useful, keep it out of the default path unless the user explicitly asks for debug artifacts.

## Planning Handoff

Treat this skill as a pre-plan checkpoint.

Its primary human-facing output is `preplan-brief.md`, which should be the handoff input to `plan-mode` or `writing-plans`.
The workbench proposal is secondary.

## Workbench Policy

Prefer updates in this order:

1. `thread-log.md`
2. `open-questions.md`
3. `decision-log.md`
4. `glossary.md`

Treat `README.md` as proposal-only in v0.1.

## Claim-State Rule

Before proposing any workbench update, preserve the conversation in two layers:

1. normalized turns
2. claim ledger

The claim ledger must distinguish at least:

- `probe`
- `rejected`
- `working_hypothesis`
- `decided`
- `open_question`
- `thread_milestone`

Rejected probes stay in `transcript_bundle.json` for auditability but should not be promoted into the workbench proposal.

## Backend

Canonical backend repository:

- current repository root

Canonical pre-plan archive root:

- `paths.shared_preplan_root` from `config/local.toml`

Use that shared folder as the default home for discussion checkpoints that may later feed planning, specs, or implementation work.

Canonical manual wrapper:

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File .\scripts\invoke-discussion-checkpoint.ps1 -Mode propose -Transcript <path> -Workbench <dir> -OutputName <name>
```

Optional external extractor backend:

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File .\scripts\invoke-discussion-checkpoint.ps1 -Mode propose -Transcript <path> -Workbench <dir> -Backend external-command -ExtractorCommand "<your command>" -OutputName <name>
```

Apply only after explicit user confirmation:

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File .\scripts\invoke-discussion-checkpoint.ps1 -Mode apply -Proposal <proposal.json> -Workbench <dir>
```
