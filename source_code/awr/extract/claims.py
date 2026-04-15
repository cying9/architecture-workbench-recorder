from __future__ import annotations

import re

from awr.models.contracts import ClaimRecord, TranscriptBundle, TranscriptTurn


def build_transcript_bundle(
    transcript_source: str,
    turns: list[TranscriptTurn],
) -> TranscriptBundle:
    claims: list[ClaimRecord] = []
    rejections: set[str] = set()

    for turn in turns:
        labels = {label.lower() for label in turn.labels}
        text = turn.normalized_text

        if "reject" in labels:
            rejection_key = (
                turn.metadata.get("reject")
                or turn.metadata.get("key")
                or _normalize_key(text)
            )
            rejections.add(rejection_key)
            claims.append(
                ClaimRecord(
                    kind="probe",
                    normalized_key=rejection_key,
                    content=text,
                    disposition="rejected",
                    confidence=0.95,
                    evidence_turn_ids=[turn.turn_id],
                )
            )
            continue

        if "probe" in labels:
            probe_key = turn.metadata.get("key") or _normalize_key(text)
            claims.append(
                ClaimRecord(
                    kind="probe",
                    normalized_key=probe_key,
                    content=text,
                    disposition="active",
                    confidence=0.55,
                    evidence_turn_ids=[turn.turn_id],
                )
            )
            continue

        if "decision" in labels:
            claims.append(
                ClaimRecord(
                    kind="decided",
                    normalized_key=_normalize_key(text),
                    content=text,
                    confidence=0.92,
                    evidence_turn_ids=[turn.turn_id],
                )
            )

        if "working_hypothesis" in labels:
            term = turn.metadata.get("term")
            claims.append(
                ClaimRecord(
                    kind="working_hypothesis",
                    normalized_key=_normalize_key(term or text),
                    content=text,
                    confidence=0.8,
                    evidence_turn_ids=[turn.turn_id],
                    term=term,
                )
            )
            if term:
                claims.append(
                    ClaimRecord(
                        kind="glossary_candidate",
                        normalized_key=_normalize_key(term),
                        content=text,
                        confidence=0.74,
                        evidence_turn_ids=[turn.turn_id],
                        term=term,
                    )
                )

        if "milestone" in labels:
            claims.append(
                ClaimRecord(
                    kind="thread_milestone",
                    normalized_key=_normalize_key(text),
                    content=text,
                    confidence=0.9,
                    evidence_turn_ids=[turn.turn_id],
                )
            )

        if "question" in labels:
            claims.append(
                ClaimRecord(
                    kind="open_question",
                    normalized_key=_normalize_key(text),
                    content=text,
                    confidence=0.9,
                    evidence_turn_ids=[turn.turn_id],
                )
            )

        if not labels:
            lowered = text.lower()
            if "treat that as a decision:" in lowered:
                claims.append(
                    ClaimRecord(
                        kind="decided",
                        normalized_key=_normalize_key(text.split(":", 1)[1]),
                        content=text.split(":", 1)[1].strip(),
                        confidence=0.92,
                        evidence_turn_ids=[turn.turn_id],
                    )
                )
            if "working hypothesis" in lowered and "`" in text:
                match = re.search(r"`([^`]+)`", text)
                term = match.group(1).strip() if match else None
                claims.append(
                    ClaimRecord(
                        kind="working_hypothesis",
                        normalized_key=_normalize_key(term or text),
                        content=text,
                        confidence=0.8,
                        evidence_turn_ids=[turn.turn_id],
                        term=term,
                    )
                )
                if term:
                    claims.append(
                        ClaimRecord(
                            kind="glossary_candidate",
                            normalized_key=_normalize_key(term),
                            content=text,
                            confidence=0.74,
                            evidence_turn_ids=[turn.turn_id],
                            term=term,
                        )
                    )
            if "one open question is" in lowered:
                claims.append(
                    ClaimRecord(
                        kind="open_question",
                        normalized_key=_normalize_key(text.split("is", 1)[1]),
                        content=text.split("is", 1)[1].strip(),
                        confidence=0.91,
                        evidence_turn_ids=[turn.turn_id],
                    )
                )
            if "important milestone:" in lowered:
                claims.append(
                    ClaimRecord(
                        kind="thread_milestone",
                        normalized_key=_normalize_key(text.split(":", 1)[1]),
                        content=text.split(":", 1)[1].strip(),
                        confidence=0.9,
                        evidence_turn_ids=[turn.turn_id],
                    )
                )

    for claim in claims:
        if claim.disposition == "active" and claim.normalized_key in rejections:
            claim.disposition = "rejected"

    return TranscriptBundle(
        transcript_source=transcript_source,
        turns=turns,
        claims=_dedupe_claims(claims),
    )


def _dedupe_claims(claims: list[ClaimRecord]) -> list[ClaimRecord]:
    unique: list[ClaimRecord] = []
    seen: set[tuple[str, str, str]] = set()
    for claim in claims:
        key = (claim.kind, claim.normalized_key, claim.disposition)
        if key in seen:
            continue
        seen.add(key)
        unique.append(claim)
    return unique


def _normalize_key(text: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", text.lower())
    return normalized.strip("-")
