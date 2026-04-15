# architecture-workbench-recorder v0.1.0

First public release of a local-first pre-plan checkpoint tool for architecture and product discussion workflows.

## Highlights

- turns a discussion transcript into a planning-facing `preplan-brief.md`
- produces a workbench-facing `proposal.md`
- preserves a structured `transcript_bundle.json` with rejected probes kept out of stable planning output
- supports conservative Markdown `apply` with explicit human review
- provides manual skill entrypoints including the daily-use alias `计划小助手`

## Current Scope

- transcript ingest from Markdown, text, and simple JSON forms
- candidate extraction for decisions, working hypotheses, open questions, glossary candidates, and thread milestones
- proposal-first workflow with local archive support
- safe local configuration via `config/local.toml`

## Notes

- this release is intentionally small
- the tool is designed as a pre-plan checkpoint, not a general meeting-notes system
- local machine paths and secrets stay outside version control
