from __future__ import annotations

import json
import sys


def main() -> None:
    _payload = json.load(sys.stdin)
    candidates = [
        {
            "type": "glossary_candidate",
            "title": "Glossary candidate: external term",
            "normalized_key": "external-term",
            "statement": "external term is a provider-agnostic candidate emitted by an external extractor.",
            "rationale": "Returned by mock external backend.",
            "evidence_turn_ids": ["turn-001"],
            "confidence": 0.88,
            "proposed_target_file": "glossary.md",
            "conflict_flags": [],
            "term": "external term",
        }
    ]
    json.dump(candidates, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
