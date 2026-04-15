# architecture-workbench-recorder

Local-first pre-plan checkpoint tooling for turning a long discussion into a small set of planning-ready artifacts.

This repository is the backend for a manual Codex skill. Its job is not to make decisions for you. Its job is to help you stabilize a messy thread before `plan-mode`, `writing-plans`, or implementation.

## What This Is

This project now follows a **skill-first + recorder-backend** shape:

- the backend lives here as a small local CLI
- the primary user entry is the manual Codex skill `architecture-workbench-discussion`
- the skill is for pre-plan checkpointing, not passive background logging
- default checkpoint bundles are archived under the local `shared_preplan_root` configured in `config/local.toml`

Status:

- implementation baseline available
- v0.1 covers `propose` and conservative `apply` for Markdown workbench maintenance

Primary design document:

- `docs/2026-04-14-v0.1-design.md`

## What Problem It Solves

Long product and architecture threads contain:

- correct conclusions
- temporary probes
- rejected ideas
- unstable terminology
- open questions that block planning

This tool turns that noisy input into a small, reviewable checkpoint bundle that can be used as the handoff into planning.

## Position In The Workflow

Recommended flow:

1. discuss and explore
2. manually trigger this skill when the thread is ready for consolidation
3. review the generated pre-plan artifacts
4. use the result as input to `plan-mode` or `writing-plans`
5. only then move into implementation

This means the tool sits **before** planning. It is not a substitute for planning.

## Is It A Skill Now

Yes.

Daily-use nickname:

- `计划小助手`

Repository-owned skill source:

- `skills/architecture-workbench-discussion/SKILL.md`
- `skills/plan-helper/SKILL.md`

Installed Codex skill:

- `$CODEX_HOME/skills/architecture-workbench-discussion/SKILL.md`
- `$CODEX_HOME/skills/plan-helper/SKILL.md`

Policy:

- manual trigger only
- no hidden auto-recording
- no implicit activation
- default to `propose`, not `apply`

## How To Wake It Up

There are two practical ways.

### 1. In conversation

Explicitly ask for it. Good trigger phrases include:

- “计划小助手，记录一下这轮讨论”
- “计划小助手，帮我把这轮讨论整理成 pre-plan brief”
- “计划小助手，先把这轮讨论沉淀一下再进入 plan-mode”
- “用 `architecture-workbench-discussion` 记录一下这轮讨论”
- “帮我把这轮讨论做成 pre-plan checkpoint”
- “在进入 plan-mode 之前，先整理这轮讨论”
- “把这段 thread 沉淀成 pre-plan brief”

The important thing is that the request is explicit. This skill is intentionally not auto-triggered.

### 2. From PowerShell

Use the wrapper directly:

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File .\scripts\invoke-discussion-checkpoint.ps1 -Mode propose -Transcript <path> -Workbench <dir> -OutputName <name>
```

By default the wrapper writes to:

- `<shared_preplan_root>\checkpoints\<date>\<timestamp>-<name>\`

Use `-OutputDir` only for a custom one-off destination.

## Local Configuration

Machine-local paths and future secrets should live in:

- `config/local.toml`

This file is intentionally gitignored.

Start from:

- `config/local.example.toml`

Recommended first step:

1. copy `config/local.example.toml` to `config/local.toml`
2. set `paths.shared_preplan_root`
3. optionally set publishing defaults under `[github]`

## Default Output Bundle

The default user-facing artifact budget is exactly three files:

- `preplan-brief.md`
- `proposal.md`
- `transcript_bundle.json`

Internal apply data is also generated at:

- `.internal/proposal.json`

That machine-readable file exists so `apply` can stay deterministic, but it is not treated as one of the default human-facing pre-plan artifacts.

## What Each Artifact Is For

### `preplan-brief.md`

Planning-facing handoff document.

It summarizes:

- stable decisions
- working hypotheses
- open questions
- thread milestones
- glossary watchlist
- planning readiness and blockers

This is the main thing to hand to `plan-mode` or `writing-plans`.

### `proposal.md`

Workbench-facing update proposal.

It shows:

- what would be added to `glossary.md`
- what would be added to `decision-log.md`
- what would be added to `open-questions.md`
- what would be added to `thread-log.md`
- conflicts, duplicates, and apply preview

### `transcript_bundle.json`

Structured audit bundle.

It preserves:

- normalized turns
- claim ledger
- rejected probes that should not be promoted into planning

### `.internal/proposal.json`

Internal machine-readable proposal used by `apply`.

## Functional Overview

Core capabilities:

- ingest a local transcript
- normalize transcript turns
- preserve explicit rejected probes
- extract candidate items
- compare against an existing five-file workbench
- emit a planning-facing brief
- emit a workbench-facing proposal
- optionally apply safe, targeted Markdown updates

Recognized candidate classes:

- `decided`
- `working_hypothesis`
- `open_question`
- `glossary_candidate`
- `thread_milestone`

## What It Does Not Do

- no automatic architecture decisions
- no default full-document rewrites
- no generic meeting-notes workflow
- no automatic activation on every architecture thread
- no hidden background capture

## Workbench Policy

Preferred update targets:

1. `thread-log.md`
2. `open-questions.md`
3. `decision-log.md`
4. `glossary.md`

`README.md` stays proposal-only in v0.1.

## Claim-State Rule

Before anything is promoted into planning or the workbench, the conversation is preserved in two layers:

1. normalized turns
2. claim ledger

The claim ledger distinguishes at least:

- `probe`
- `rejected`
- `working_hypothesis`
- `decided`
- `open_question`
- `thread_milestone`

Rejected probes remain in `transcript_bundle.json` for auditability but should not be promoted into `preplan-brief.md` as stable planning input.

## CLI

### Propose

```powershell
python source_code/awr/cli.py propose --transcript examples/transcripts/sample-thread.md --workbench examples/workbenches/sample-workbench --output-dir runtime/preplan/checkpoints/demo
```

### Apply

```powershell
python source_code/awr/cli.py apply --proposal runtime/preplan/checkpoints/demo/.internal/proposal.json --workbench examples/workbenches/sample-workbench
```

### Manual Wrapper

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\invoke-discussion-checkpoint.ps1 -Mode propose -Transcript examples\transcripts\sample-thread.md -Workbench examples\workbenches\sample-workbench -OutputName manual-demo
```

## Structured Transcript Cues

Supported today:

- inline tags in Markdown or text transcripts such as `[decision]`, `[working_hypothesis]`, `[milestone]`, `[probe]`, `[reject:key]`, and `[term:name]`
- JSON transcripts with the same tagged text pattern

## Provider-Agnostic Extraction

Available backends:

- `--backend rule-based`
- `--backend external-command --extractor-command "<your command>"`

The external command receives JSON on stdin with:

- `transcript_bundle`
- `workbench_snapshot`

and must return candidate JSON on stdout.

## Directory Overview

- `config/` defaults and file targeting
- `docs/` design and product notes
- `examples/` sample transcripts and workbenches
- `scripts/` wrapper entrypoints
- `skills/` repository-owned skill source
- `source_code/awr/` CLI and pipeline implementation
- `tests/` minimal verification coverage

## Testing

```powershell
python -m unittest discover -s tests -v
```
