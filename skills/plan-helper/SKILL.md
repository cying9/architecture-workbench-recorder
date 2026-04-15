---
name: plan-helper
description: Use when the user explicitly asks for the plan helper alias to consolidate a long product or architecture discussion into pre-plan artifacts before planning or implementation. Do not use automatically.
---

# Plan Helper

## Overview

This skill is the human-friendly alias for the `architecture-workbench-discussion` workflow.

Use it when the user wants to checkpoint a long discussion before `plan-mode`, `writing-plans`, or implementation.

## Trigger Rule

- manual trigger only
- explicit user wording only
- do not auto-activate

Typical requests:

- "plan helper, record this discussion"
- "plan helper, prepare a pre-plan brief"
- "plan helper, consolidate this before plan-mode"

## Output Shape

Default human-facing outputs:

- `preplan-brief.md`
- `proposal.md`
- `transcript_bundle.json`

Internal apply payload:

- `.internal/proposal.json`

## Backend

Canonical backend repository:

- current repository root

Canonical archive root:

- `paths.shared_preplan_root` from `config/local.toml`

Canonical wrapper:

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File .\scripts\invoke-discussion-checkpoint.ps1 -Mode propose -Transcript <path> -Workbench <dir> -OutputName <name>
```

## Notes

- This alias exists for easier daily use.
- The user-facing display name lives in `agents/openai.yaml`.
- The underlying capability remains the same manual pre-plan checkpoint workflow.
