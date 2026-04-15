from __future__ import annotations

import shutil
from datetime import date
from pathlib import Path

from awr.models.contracts import ProposalBundle


def apply_proposal(
    proposal: ProposalBundle,
    workbench_root: str | Path,
    current_date: date | None = None,
) -> None:
    root = Path(workbench_root).expanduser().resolve()
    backup_root = root / ".awr-backups" / proposal.proposal_id
    backup_root.mkdir(parents=True, exist_ok=True)
    today = (current_date or date.today()).isoformat()

    touched_paths: set[Path] = set()
    for unit in proposal.apply_plan:
        target = root / unit.target_file
        if target not in touched_paths and target.exists():
            shutil.copy2(target, backup_root / target.name)
            touched_paths.add(target)
        _apply_unit(target, unit.target_file, unit.content, today)


def _apply_unit(path: Path, target_file: str, content: str, today: str) -> None:
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    if target_file == "decision-log.md":
        updated = _append_under_date_section(existing, today, content, heading="# Decision Log")
    elif target_file == "thread-log.md":
        updated = _append_under_date_section(existing, today, content, heading="# Thread Log")
    elif target_file == "open-questions.md":
        updated = _append_open_question(existing, content)
    else:
        updated = existing.rstrip() + "\n" + content.rstrip() + "\n"
    path.write_text(updated, encoding="utf-8")


def _append_under_date_section(existing: str, today: str, content: str, heading: str) -> str:
    working = existing.rstrip()
    date_header = f"## {today}"
    if date_header in working:
        return working + "\n\n" + content.rstrip() + "\n"
    if not working:
        return f"{heading}\n\n{date_header}\n\n{content.rstrip()}\n"
    return working + f"\n\n{date_header}\n\n" + content.rstrip() + "\n"


def _append_open_question(existing: str, content: str) -> str:
    stripped = content.strip()
    if stripped.startswith(tuple(f"{i}." for i in range(10))):
        line = stripped
    else:
        next_index = _next_question_index(existing)
        line = f"{next_index}. {stripped.lstrip('- ').strip()}"
    working = existing.rstrip()
    if not working:
        return "# Open Questions\n\n" + line + "\n"
    return working + "\n" + line + "\n"


def _next_question_index(existing: str) -> int:
    highest = 0
    for line in existing.splitlines():
        parts = line.strip().split(".", 1)
        if len(parts) == 2 and parts[0].isdigit():
            highest = max(highest, int(parts[0]))
    return highest + 1
