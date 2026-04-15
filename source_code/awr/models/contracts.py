from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field


CandidateType = Literal[
    "decided",
    "working_hypothesis",
    "open_question",
    "glossary_candidate",
    "thread_milestone",
]


class TranscriptTurn(BaseModel):
    turn_id: str
    speaker: str
    role: str
    timestamp: str | None = None
    raw_text: str
    normalized_text: str
    source_span: str
    labels: list[str] = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)


class ClaimRecord(BaseModel):
    claim_id: str = Field(default_factory=lambda: uuid4().hex)
    kind: str
    normalized_key: str
    content: str
    disposition: Literal["active", "rejected"] = "active"
    confidence: float = 0.7
    evidence_turn_ids: list[str] = Field(default_factory=list)
    term: str | None = None


class TranscriptBundle(BaseModel):
    transcript_source: str
    turns: list[TranscriptTurn] = Field(default_factory=list)
    claims: list[ClaimRecord] = Field(default_factory=list)


class GlossaryEntry(BaseModel):
    term: str
    definition: str


class DecisionEntry(BaseModel):
    title: str
    status: str
    decision: str


class ThreadEntry(BaseModel):
    title: str
    body: str


class WorkbenchSnapshot(BaseModel):
    root_path: str
    readme_text: str
    glossary_entries: list[GlossaryEntry] = Field(default_factory=list)
    decisions: list[DecisionEntry] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    thread_entries: list[ThreadEntry] = Field(default_factory=list)


class CandidateItem(BaseModel):
    candidate_id: str = Field(default_factory=lambda: uuid4().hex)
    type: CandidateType
    title: str
    normalized_key: str
    statement: str
    rationale: str | None = None
    evidence_turn_ids: list[str] = Field(default_factory=list)
    confidence: float = 0.7
    status_hint: str | None = None
    proposed_target_file: str
    conflict_flags: list[str] = Field(default_factory=list)
    term: str | None = None


class ApplyUnit(BaseModel):
    unit_id: str = Field(default_factory=lambda: uuid4().hex)
    target_file: str
    operation: Literal["append"]
    anchor: str | None = None
    content: str
    rationale: str
    evidence_turn_ids: list[str] = Field(default_factory=list)


class ProposalSummary(BaseModel):
    transcript_source: str
    workbench_root: str
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    candidate_counts: dict[str, int]
    discarded_probe_count: int = 0


class ProposalBundle(BaseModel):
    proposal_id: str = Field(default_factory=lambda: uuid4().hex[:12])
    summary: ProposalSummary
    candidates: list[CandidateItem] = Field(default_factory=list)
    duplicates: list[str] = Field(default_factory=list)
    conflicts: list[str] = Field(default_factory=list)
    apply_plan: list[ApplyUnit] = Field(default_factory=list)


class ProposalArtifacts(BaseModel):
    output_dir: str
    preplan_brief_path: str
    proposal_markdown_path: str
    proposal_json_path: str
    transcript_bundle_path: str | None = None
    proposal: ProposalBundle


def ensure_path(value: str | Path) -> Path:
    return Path(value).expanduser().resolve()
