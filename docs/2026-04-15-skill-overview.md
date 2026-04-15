# architecture-workbench-discussion Skill Overview

## Product Role

`architecture-workbench-discussion` is a manual pre-plan checkpoint skill.

Daily-use alias:

- `计划小助手`

It exists to help with this transition:

- from long, messy discussion
- to a small, reviewable planning handoff

It is not meant to replace planning, implementation planning, or architecture judgment.

## When To Use It

Use it when:

- a discussion thread has become long and unstable
- terminology is evolving
- some decisions are stable enough to retain
- open questions are starting to block next-step planning
- you want to preserve the useful parts before entering `plan-mode`

## When Not To Use It

Do not use it for:

- ordinary short chat
- generic meeting minutes
- background passive recording
- automatic note capture
- final implementation planning

## Main Outputs

Default human-facing outputs:

- `preplan-brief.md`
- `proposal.md`
- `transcript_bundle.json`

Internal apply payload:

- `.internal/proposal.json`

## Relationship To Later Planning

The intended handoff is:

1. use this skill to consolidate discussion
2. review the generated `preplan-brief.md`
3. enter `plan-mode` or use `writing-plans`
4. produce the actual implementation plan

This keeps planning based on stabilized discussion rather than raw thread noise.

## Invocation Model

This skill is manual-only.

It should be explicitly requested with wording like:

- 计划小助手，记录一下这轮讨论
- 计划小助手，先整理这轮讨论再进入 plan-mode
- record this discussion as a pre-plan checkpoint
- prepare this thread for planning
- consolidate this architecture discussion before plan-mode

## Local Path Policy

Repository docs should use portable paths where possible.

Machine-local values such as:

- shared archive roots
- local Codex install roots
- future API tokens or secrets

should be stored in `config/local.toml`, not hardcoded into the repository.

## Safety Model

- no implicit activation
- default to `propose`
- `apply` only after explicit confirmation
- `README.md` remains proposal-only in v0.1
