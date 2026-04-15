from __future__ import annotations

import re

from awr.models.contracts import CandidateItem, TranscriptBundle, WorkbenchSnapshot


def extract_candidates(
    bundle: TranscriptBundle, snapshot: WorkbenchSnapshot
) -> list[CandidateItem]:
    del snapshot
    candidates: list[CandidateItem] = []
    for claim in bundle.claims:
        if claim.disposition == "rejected":
            continue

        text = claim.content

        if claim.kind == "decided":
            statement = text
            candidates.append(
                CandidateItem(
                    type="decided",
                    title="Proposal-first default with conservative apply",
                    normalized_key=claim.normalized_key,
                    statement=statement,
                    rationale="Explicitly framed as a decision in the discussion.",
                    evidence_turn_ids=claim.evidence_turn_ids,
                    proposed_target_file="decision-log.md",
                    confidence=claim.confidence,
                    status_hint="decided",
                )
            )

        if claim.kind == "working_hypothesis":
            term = claim.term or _extract_term(text) or "working term"
            candidates.append(
                CandidateItem(
                    type="working_hypothesis",
                    title=f"Working hypothesis: {term}",
                    normalized_key=claim.normalized_key,
                    statement=text,
                    rationale="Marked as a working hypothesis in the transcript.",
                    evidence_turn_ids=claim.evidence_turn_ids,
                    proposed_target_file="decision-log.md",
                    confidence=claim.confidence,
                    status_hint="working decision",
                    term=term,
                )
            )

        if claim.kind == "glossary_candidate":
            term = claim.term or _extract_term(text) or "working term"
            definition = _derive_definition(text, term)
            candidates.append(
                CandidateItem(
                    type="glossary_candidate",
                    title=f"Glossary candidate: {term}",
                    normalized_key=claim.normalized_key,
                    statement=definition,
                    rationale="The transcript gave the term a stable-enough working definition.",
                    evidence_turn_ids=claim.evidence_turn_ids,
                    proposed_target_file="glossary.md",
                    confidence=claim.confidence,
                    term=term,
                )
            )

        if claim.kind == "open_question":
            question = text
            candidates.append(
                CandidateItem(
                    type="open_question",
                    title="Open question from transcript",
                    normalized_key=claim.normalized_key,
                    statement=question,
                    rationale="Explicitly framed as an open question.",
                    evidence_turn_ids=claim.evidence_turn_ids,
                    proposed_target_file="open-questions.md",
                    confidence=claim.confidence,
                )
            )

        if claim.kind == "thread_milestone":
            milestone = text
            candidates.append(
                CandidateItem(
                    type="thread_milestone",
                    title="Thread milestone",
                    normalized_key=claim.normalized_key,
                    statement=milestone,
                    rationale="Explicitly framed as a major discussion milestone.",
                    evidence_turn_ids=claim.evidence_turn_ids,
                    proposed_target_file="thread-log.md",
                    confidence=claim.confidence,
                )
            )

    return _dedupe_candidates(candidates)


def _normalize_key(text: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", text.lower())
    return normalized.strip("-")


def _extract_term(text: str) -> str | None:
    match = re.search(r"`([^`]+)`", text)
    return match.group(1).strip() if match else None


def _derive_definition(text: str, term: str) -> str:
    lowered = text.lower()
    if " is " in lowered:
        return text.split(" is ", 1)[1].strip().rstrip(".") + "."
    if ":" in text:
        return text.split(":", 1)[1].strip()
    return f"{term} is a working term from the transcript."


def _dedupe_candidates(candidates: list[CandidateItem]) -> list[CandidateItem]:
    seen: set[tuple[str, str]] = set()
    unique: list[CandidateItem] = []
    for candidate in candidates:
        key = (candidate.type, candidate.normalized_key)
        if key in seen:
            continue
        seen.add(key)
        unique.append(candidate)
    return unique
