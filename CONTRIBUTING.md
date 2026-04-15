# Contributing

Thanks for your interest in improving `architecture-workbench-recorder`.

## Project Style

This repository is intentionally small and local-first.

Please prefer changes that keep the tool:

- proposal-first
- markdown-first
- human-in-the-loop
- easy to inspect and easy to remove

Avoid turning it into:

- a general meeting notes product
- a background auto-recorder
- an over-agentized workflow platform

## Development Flow

1. Create or switch to a feature branch.
2. Keep the change set focused.
3. Run the test suite:

```powershell
python -m unittest discover -s tests -v
```

4. Update docs when behavior or user-facing workflow changes.
5. Keep local-only paths and secrets out of the repository.

## Local Configuration

Machine-local settings belong in:

- `config/local.toml`

Start from:

- `config/local.example.toml`

This local file is gitignored and should not be committed.

## Pull Request Guidance

Good PRs for this project usually include:

- one clear user-facing improvement
- a short explanation of why the change belongs in this tool
- notes on how the change preserves the pre-plan checkpoint model

## Scope Guardrails

Before adding something new, ask:

- Does this help discussion become planning-ready?
- Does it preserve explicit review before apply?
- Can the same goal be achieved with a simpler artifact or contract?

If the answer is no, it probably does not belong in v0.x.
