from __future__ import annotations

from collections import Counter

from awr.models.contracts import (
    ApplyUnit,
    CandidateItem,
    ProposalBundle,
    ProposalSummary,
    TranscriptBundle,
    WorkbenchSnapshot,
)


def build_proposal(
    transcript_source: str,
    snapshot: WorkbenchSnapshot,
    bundle: TranscriptBundle,
    candidates: list[CandidateItem],
) -> ProposalBundle:
    duplicates: list[str] = []
    conflicts: list[str] = []
    apply_plan: list[ApplyUnit] = []

    glossary_terms = {entry.term.lower(): entry for entry in snapshot.glossary_entries}
    decision_bodies = {entry.decision.lower() for entry in snapshot.decisions if entry.decision}
    open_questions = {question.lower() for question in snapshot.open_questions}
    thread_bodies = {entry.body.lower() for entry in snapshot.thread_entries}

    for candidate in candidates:
        if candidate.type == "glossary_candidate" and candidate.term:
            existing = glossary_terms.get(candidate.term.lower())
            if existing and existing.definition.lower() == candidate.statement.lower():
                duplicates.append(f"Glossary term already exists: {candidate.term}")
                continue
            if existing and existing.definition.lower() != candidate.statement.lower():
                conflicts.append(f"Glossary definition conflict for term: {candidate.term}")
                candidate.conflict_flags.append("term_definition_conflict")

            apply_plan.append(
                ApplyUnit(
                    target_file="glossary.md",
                    operation="append",
                    content=_format_glossary_candidate(candidate),
                    rationale=candidate.rationale or "New glossary candidate from transcript.",
                    evidence_turn_ids=candidate.evidence_turn_ids,
                )
            )

        elif candidate.type in {"decided", "working_hypothesis"}:
            if candidate.statement.lower() in decision_bodies:
                duplicates.append(f"Decision already logged: {candidate.title}")
                continue
            apply_plan.append(
                ApplyUnit(
                    target_file="decision-log.md",
                    operation="append",
                    content=_format_decision_candidate(candidate, snapshot),
                    rationale=candidate.rationale or "Decision candidate from transcript.",
                    evidence_turn_ids=candidate.evidence_turn_ids,
                )
            )

        elif candidate.type == "open_question":
            if candidate.statement.lower() in open_questions:
                duplicates.append(f"Open question already tracked: {candidate.statement}")
                continue
            apply_plan.append(
                ApplyUnit(
                    target_file="open-questions.md",
                    operation="append",
                    content=_format_open_question(candidate, snapshot),
                    rationale=candidate.rationale or "Open question from transcript.",
                    evidence_turn_ids=candidate.evidence_turn_ids,
                )
            )

        elif candidate.type == "thread_milestone":
            if candidate.statement.lower() in thread_bodies:
                duplicates.append(f"Thread milestone already logged: {candidate.statement}")
                continue
            apply_plan.append(
                ApplyUnit(
                    target_file="thread-log.md",
                    operation="append",
                    content=_format_thread_milestone(candidate, snapshot),
                    rationale=candidate.rationale or "Thread milestone from transcript.",
                    evidence_turn_ids=candidate.evidence_turn_ids,
                )
            )

    if _needs_readme_suggestion(snapshot, candidates):
        milestone = next(
            (item for item in candidates if item.type == "thread_milestone"),
            None,
        )
        if milestone:
            candidates.append(
                CandidateItem(
                    type="thread_milestone",
                    title="README suggestion",
                    normalized_key="readme-suggestion-conversation-to-workbench",
                    statement="README could add a top-level note that the recorder is conversation-to-workbench rather than a generic meeting notes system.",
                    rationale="The transcript introduced a top-level framing shift that may deserve README visibility, but v0.1 should keep it proposal-only.",
                    evidence_turn_ids=milestone.evidence_turn_ids,
                    proposed_target_file="README.md",
                    confidence=0.68,
                    conflict_flags=["proposal_only"],
                )
            )

    counted_candidates = [
        candidate
        for candidate in candidates
        if candidate.proposed_target_file != "README.md"
    ]
    counter = Counter(candidate.type for candidate in counted_candidates)
    summary = ProposalSummary(
        transcript_source=transcript_source,
        workbench_root=snapshot.root_path,
        candidate_counts={
            "decided": counter.get("decided", 0),
            "working_hypothesis": counter.get("working_hypothesis", 0),
            "open_question": counter.get("open_question", 0),
            "glossary_candidate": counter.get("glossary_candidate", 0),
            "thread_milestone": counter.get("thread_milestone", 0),
        },
        discarded_probe_count=sum(
            1
            for claim in bundle.claims
            if claim.kind == "probe" and claim.disposition == "rejected"
        ),
    )
    return ProposalBundle(
        summary=summary,
        candidates=candidates,
        duplicates=duplicates,
        conflicts=conflicts,
        apply_plan=apply_plan,
    )


def _needs_readme_suggestion(
    snapshot: WorkbenchSnapshot,
    candidates: list[CandidateItem],
) -> bool:
    readme_text = snapshot.readme_text.lower()
    for candidate in candidates:
        if candidate.type != "thread_milestone":
            continue
        if "generic meeting notes system" in candidate.statement.lower():
            return "generic meeting notes system" not in readme_text
    return False


def _format_glossary_candidate(candidate: CandidateItem) -> str:
    return f"\n### `{candidate.term}`\n\n{candidate.statement}\n"


def _format_decision_candidate(candidate: CandidateItem, snapshot: WorkbenchSnapshot) -> str:
    _ = snapshot
    status = candidate.status_hint or "decided"
    return (
        "\n### D-NEW: "
        f"{candidate.title}\n\n"
        f"- Status: {status}\n"
        "- Decision:\n"
        f"  {candidate.statement}\n"
        "- Why:\n"
        f"  {candidate.rationale or 'Derived from the confirmed discussion thread.'}\n"
    )


def _format_open_question(candidate: CandidateItem, snapshot: WorkbenchSnapshot) -> str:
    next_index = len(snapshot.open_questions) + 1
    return f"\n{next_index}. {candidate.statement}\n"


def _format_thread_milestone(candidate: CandidateItem, snapshot: WorkbenchSnapshot) -> str:
    next_index = len(snapshot.thread_entries) + 1
    return (
        f"\n### Entry {next_index:02d}: Thread milestone\n\n"
        f"- {candidate.statement}\n"
    )
