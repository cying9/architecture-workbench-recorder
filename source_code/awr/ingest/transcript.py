from __future__ import annotations

import json
import re
from pathlib import Path

from awr.models.contracts import TranscriptTurn


ROLE_TAG_RE = re.compile(r"^\[(?P<timestamp>[^\]]+)\]\s+(?P<role>[^:]+):\s*$")
ANNOTATION_RE = re.compile(r"^\[(?P<name>[a-zA-Z_][a-zA-Z0-9_-]*)(?::(?P<value>[^\]]+))?\]")


def load_transcript(path: str | Path) -> list[TranscriptTurn]:
    source = Path(path).expanduser().resolve()
    suffix = source.suffix.lower()
    if suffix == ".json":
        return _load_json_transcript(source)
    return _load_role_tag_transcript(source)


def _load_json_transcript(source: Path) -> list[TranscriptTurn]:
    data = json.loads(source.read_text(encoding="utf-8"))
    turns: list[TranscriptTurn] = []
    for index, item in enumerate(data, start=1):
        raw_text = str(item.get("text", "")).strip()
        cleaned_text, labels, metadata = _extract_inline_annotations(raw_text)
        for annotation in item.get("annotations", []):
            if isinstance(annotation, str):
                labels.append(annotation)
            elif isinstance(annotation, dict):
                name = str(annotation.get("name", "")).strip()
                if name:
                    labels.append(name)
                    value = annotation.get("value")
                    if value is not None:
                        metadata[name] = str(value)
        role = str(item.get("role", "unknown")).strip()
        turns.append(
            TranscriptTurn(
                turn_id=f"turn-{index:03d}",
                speaker=role,
                role=role,
                timestamp=item.get("timestamp"),
                raw_text=raw_text,
                normalized_text=_normalize_text(cleaned_text),
                source_span=f"{source.name}:{index}",
                labels=labels,
                metadata=metadata,
            )
        )
    return turns


def _load_role_tag_transcript(source: Path) -> list[TranscriptTurn]:
    lines = source.read_text(encoding="utf-8").splitlines()
    turns: list[TranscriptTurn] = []
    current_role: str | None = None
    current_timestamp: str | None = None
    current_text: list[str] = []
    current_start_line = 1

    def flush(end_line: int) -> None:
        nonlocal current_role, current_timestamp, current_text, current_start_line
        if current_role is None:
            return
        text = "\n".join(current_text).strip()
        if text:
            turn_index = len(turns) + 1
            turns.append(
                TranscriptTurn(
                    turn_id=f"turn-{turn_index:03d}",
                    speaker=current_role,
                    role=current_role,
                    timestamp=current_timestamp,
                    raw_text=text,
                    normalized_text=_normalize_text(text),
                    source_span=f"{source.name}:{current_start_line}-{end_line}",
                )
            )
        current_role = None
        current_timestamp = None
        current_text = []
        current_start_line = end_line + 1

    for line_number, line in enumerate(lines, start=1):
        match = ROLE_TAG_RE.match(line)
        if match:
            flush(line_number - 1)
            current_timestamp = match.group("timestamp").strip()
            current_role = match.group("role").strip().lower()
            current_start_line = line_number
            continue
        current_text.append(line)

    flush(len(lines))
    return turns


def _normalize_text(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    return re.sub(r"[ \t]+", " ", normalized)


def _extract_inline_annotations(text: str) -> tuple[str, list[str], dict[str, str]]:
    working = text.lstrip()
    labels: list[str] = []
    metadata: dict[str, str] = {}
    while True:
        match = ANNOTATION_RE.match(working)
        if not match:
            break
        name = match.group("name").strip()
        value = match.group("value")
        labels.append(name)
        if value is not None:
            metadata[name] = value.strip()
        working = working[match.end():].lstrip()
    return working, labels, metadata
