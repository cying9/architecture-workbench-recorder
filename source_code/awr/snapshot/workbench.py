from __future__ import annotations

import re
from pathlib import Path

from awr.models.contracts import DecisionEntry, GlossaryEntry, ThreadEntry, WorkbenchSnapshot


def load_workbench_snapshot(root: str | Path) -> WorkbenchSnapshot:
    workbench_root = Path(root).expanduser().resolve()
    readme = _read(workbench_root / "README.md")
    glossary = _parse_glossary(_read(workbench_root / "glossary.md"))
    decisions = _parse_decision_log(_read(workbench_root / "decision-log.md"))
    open_questions = _parse_open_questions(_read(workbench_root / "open-questions.md"))
    thread_entries = _parse_thread_log(_read(workbench_root / "thread-log.md"))
    return WorkbenchSnapshot(
        root_path=str(workbench_root),
        readme_text=readme,
        glossary_entries=glossary,
        decisions=decisions,
        open_questions=open_questions,
        thread_entries=thread_entries,
    )


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _parse_glossary(text: str) -> list[GlossaryEntry]:
    entries: list[GlossaryEntry] = []
    pattern = re.compile(r"^### `(?P<term>[^`]+)`\n\n(?P<body>.*?)(?=\n### |\Z)", re.M | re.S)
    for match in pattern.finditer(text.strip()):
        definition = " ".join(line.strip() for line in match.group("body").strip().splitlines() if line.strip())
        entries.append(GlossaryEntry(term=match.group("term").strip(), definition=definition))
    return entries


def _parse_decision_log(text: str) -> list[DecisionEntry]:
    entries: list[DecisionEntry] = []
    pattern = re.compile(r"^### (?P<title>[^\n]+)\n\n(?P<body>.*?)(?=\n### |\Z)", re.M | re.S)
    for match in pattern.finditer(text.strip()):
        block = match.group("body")
        status = _capture_line(block, "- Status:")
        decision = _capture_paragraph(block, "- Decision:")
        entries.append(DecisionEntry(title=match.group("title").strip(), status=status, decision=decision))
    return entries


def _parse_open_questions(text: str) -> list[str]:
    questions: list[str] = []
    for line in text.splitlines():
        match = re.match(r"^\d+\.\s+(?P<question>.+)$", line.strip())
        if match:
            questions.append(match.group("question").strip())
    return questions


def _parse_thread_log(text: str) -> list[ThreadEntry]:
    entries: list[ThreadEntry] = []
    pattern = re.compile(r"^### (?P<title>[^\n]+)\n\n(?P<body>.*?)(?=\n### |\Z)", re.M | re.S)
    for match in pattern.finditer(text.strip()):
        body = "\n".join(line.rstrip() for line in match.group("body").strip().splitlines())
        entries.append(ThreadEntry(title=match.group("title").strip(), body=body))
    return entries


def _capture_line(block: str, prefix: str) -> str:
    for line in block.splitlines():
        if line.strip().startswith(prefix):
            return line.split(":", 1)[1].strip()
    return ""


def _capture_paragraph(block: str, prefix: str) -> str:
    lines = block.splitlines()
    for index, line in enumerate(lines):
        if line.strip().startswith(prefix):
            remainder = line.split(":", 1)[1].strip()
            if remainder:
                return remainder
            collected: list[str] = []
            pointer = index + 1
            while pointer < len(lines):
                raw = lines[pointer]
                if raw.startswith("- ") and raw.strip():
                    break
                if raw.strip():
                    collected.append(raw.strip())
                pointer += 1
            return " ".join(collected)
    return ""
