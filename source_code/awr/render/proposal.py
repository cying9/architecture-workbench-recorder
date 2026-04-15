from __future__ import annotations

import json
from pathlib import Path

from awr.models.contracts import (
    CandidateItem,
    ProposalArtifacts,
    ProposalBundle,
    TranscriptBundle,
)


def write_proposal_bundle(
    proposal: ProposalBundle,
    output_dir: str | Path,
    transcript_bundle: TranscriptBundle | None = None,
) -> ProposalArtifacts:
    root = Path(output_dir).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    internal_root = root / ".internal"
    internal_root.mkdir(parents=True, exist_ok=True)

    proposal_json_path = internal_root / "proposal.json"
    preplan_brief_path = root / "preplan-brief.md"
    proposal_md_path = root / "proposal.md"
    transcript_bundle_path = root / "transcript_bundle.json"

    proposal_json_path.write_text(
        json.dumps(proposal.model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    preplan_brief_path.write_text(render_preplan_brief_markdown(proposal), encoding="utf-8")
    proposal_md_path.write_text(render_proposal_markdown(proposal), encoding="utf-8")
    if transcript_bundle is not None:
        transcript_bundle_path.write_text(
            json.dumps(
                transcript_bundle.model_dump(mode="json"),
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    return ProposalArtifacts(
        output_dir=str(root),
        preplan_brief_path=str(preplan_brief_path),
        proposal_markdown_path=str(proposal_md_path),
        proposal_json_path=str(proposal_json_path),
        transcript_bundle_path=str(transcript_bundle_path) if transcript_bundle is not None else None,
        proposal=proposal,
    )


def render_preplan_brief_markdown(proposal: ProposalBundle) -> str:
    sections: list[str] = [
        "# Pre-Plan Brief",
        "",
        "## Purpose",
        "",
        "This brief is the planning-facing checkpoint distilled from the discussion thread.",
        "Use it before entering `plan-mode`, `writing-plans`, or implementation.",
        "",
        "## Source",
        "",
        f"- Transcript source: `{proposal.summary.transcript_source}`",
        f"- Workbench root: `{proposal.summary.workbench_root}`",
        f"- Proposal id: `{proposal.proposal_id}`",
        "",
        "## Stable Decisions",
        "",
        *_render_preplan_candidate_list(proposal.candidates, "decided"),
        "",
        "## Working Hypotheses",
        "",
        *_render_preplan_candidate_list(proposal.candidates, "working_hypothesis"),
        "",
        "## Open Questions",
        "",
        *_render_preplan_candidate_list(proposal.candidates, "open_question"),
        "",
        "## Thread Milestones",
        "",
        *_render_preplan_candidate_list(proposal.candidates, "thread_milestone"),
        "",
        "## Glossary Watchlist",
        "",
        *_render_preplan_candidate_list(proposal.candidates, "glossary_candidate"),
        "",
        "## Planning Readiness",
        "",
        f"- Rejected probes kept out of planning inputs: {proposal.summary.discarded_probe_count}",
        f"- Conflicts detected: {len(proposal.conflicts)}",
        f"- Duplicates detected: {len(proposal.duplicates)}",
    ]

    open_questions = [item for item in proposal.candidates if item.type == "open_question"]
    if open_questions:
        sections.extend(
            [
                "- Planning blockers remain open.",
                "- Recommended next step: resolve or explicitly defer the open questions before detailed implementation planning.",
            ]
        )
    else:
        sections.extend(
            [
                "- No explicit planning blockers detected from this checkpoint.",
                "- Recommended next step: use this brief as the handoff input for `writing-plans` or manual plan drafting.",
            ]
        )

    return "\n".join(sections).strip() + "\n"


def render_proposal_markdown(proposal: ProposalBundle) -> str:
    sections: list[str] = [
        "# Workbench Update Proposal",
        "",
        "## Summary",
        "",
        f"- Transcript source: `{proposal.summary.transcript_source}`",
        f"- Workbench root: `{proposal.summary.workbench_root}`",
        f"- Proposal id: `{proposal.proposal_id}`",
        "",
        "## Candidate Counts",
        "",
    ]
    for key, value in proposal.summary.candidate_counts.items():
        sections.append(f"- `{key}`: {value}")

    sections.extend(
        [
            "",
            "## Proposed Glossary Updates",
            "",
            *_render_candidate_group(proposal.candidates, "glossary_candidate"),
            "",
            "## Proposed Decision Log Updates",
            "",
            *_render_candidate_group(proposal.candidates, "decided", "working_hypothesis"),
            "",
            "## Proposed Open Question Updates",
            "",
            *_render_candidate_group(proposal.candidates, "open_question"),
            "",
            "## Proposed Thread Log Updates",
            "",
            *_render_candidate_group(proposal.candidates, "thread_milestone"),
            "",
            "## README Suggestions",
            "",
            *_render_readme_suggestions(proposal.candidates),
            "",
            "## Conflicts",
            "",
        ]
    )

    if proposal.conflicts:
        sections.extend(f"- {item}" for item in proposal.conflicts)
    else:
        sections.append("- None")

    sections.extend(["", "## Duplicates", ""])
    if proposal.duplicates:
        sections.extend(f"- {item}" for item in proposal.duplicates)
    else:
        sections.append("- None")

    sections.extend(["", "## Apply Preview", ""])
    if proposal.apply_plan:
        for unit in proposal.apply_plan:
            sections.append(f"- `{unit.target_file}` <- {unit.rationale}")
    else:
        sections.append("- No pending apply actions")

    return "\n".join(sections).strip() + "\n"


def _render_preplan_candidate_list(
    candidates: list[CandidateItem],
    candidate_type: str,
) -> list[str]:
    filtered = [item for item in candidates if item.type == candidate_type]
    if not filtered:
        return ["- None"]

    rows: list[str] = []
    for item in filtered:
        rows.append(f"- {item.title}: {item.statement}")
        if item.rationale:
            rows.append(f"  Why: {item.rationale}")
    return rows


def _render_candidate_group(
    candidates: list[CandidateItem],
    *candidate_types: str,
) -> list[str]:
    rows: list[str] = []
    filtered = [item for item in candidates if item.type in candidate_types]
    if not filtered:
        return ["- None"]
    for item in filtered:
        rows.append(f"### {item.title}")
        rows.append("")
        rows.append(f"- Type: `{item.type}`")
        rows.append(f"- Statement: {item.statement}")
        if item.term:
            rows.append(f"- Term: `{item.term}`")
        rows.append(f"- Evidence turns: {', '.join(item.evidence_turn_ids)}")
        if item.rationale:
            rows.append(f"- Why: {item.rationale}")
        rows.append("")
    return rows


def _render_readme_suggestions(candidates: list[CandidateItem]) -> list[str]:
    rows: list[str] = []
    filtered = [
        item
        for item in candidates
        if item.proposed_target_file == "README.md"
    ]
    if not filtered:
        return ["- None"]
    for item in filtered:
        rows.append(f"### {item.title}")
        rows.append("")
        rows.append(f"- Suggestion: {item.statement}")
        rows.append(f"- Why: {item.rationale}")
        rows.append("- Apply policy: proposal-only in v0.1")
        rows.append("")
    return rows
