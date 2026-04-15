from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from typing import Protocol

from awr.models.contracts import CandidateItem, TranscriptBundle, WorkbenchSnapshot


class ExtractorBackend(Protocol):
    name: str

    def extract(
        self,
        bundle: TranscriptBundle,
        snapshot: WorkbenchSnapshot,
    ) -> list[CandidateItem]: ...


class RuleBasedBackend:
    name = "rule-based"

    def extract(
        self,
        bundle: TranscriptBundle,
        snapshot: WorkbenchSnapshot,
    ) -> list[CandidateItem]:
        from awr.extract.rule_based import extract_candidates

        return extract_candidates(bundle, snapshot)


@dataclass
class ExternalCommandBackend:
    command: str
    name: str = "external-command"

    def extract(
        self,
        bundle: TranscriptBundle,
        snapshot: WorkbenchSnapshot,
    ) -> list[CandidateItem]:
        payload = {
            "transcript_bundle": bundle.model_dump(mode="json"),
            "workbench_snapshot": snapshot.model_dump(mode="json"),
        }
        completed = subprocess.run(
            self.command,
            input=json.dumps(payload, ensure_ascii=False),
            capture_output=True,
            text=True,
            encoding="utf-8",
            shell=True,
            check=False,
        )
        if completed.returncode != 0:
            raise ValueError(
                f"External extractor failed: {completed.stderr.strip() or completed.stdout.strip()}"
            )
        raw = json.loads(completed.stdout)
        return [CandidateItem.model_validate(item) for item in raw]


def get_backend(name: str, extractor_command: str | None = None) -> ExtractorBackend:
    normalized = name.strip().lower()
    if normalized == "rule-based":
        return RuleBasedBackend()
    if normalized == "external-command":
        if not extractor_command:
            raise ValueError(
                "The external-command backend requires --extractor-command."
            )
        return ExternalCommandBackend(command=extractor_command)
    raise ValueError(f"Unsupported backend: {name}")
