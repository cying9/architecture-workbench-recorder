from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import typer

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from awr.apply_ops.markdown import apply_proposal
from awr.compare.diffing import build_proposal
from awr.extract.backends import get_backend
from awr.extract.claims import build_transcript_bundle
from awr.ingest.transcript import load_transcript
from awr.models.contracts import ProposalBundle
from awr.render.proposal import write_proposal_bundle
from awr.snapshot.workbench import load_workbench_snapshot


app = typer.Typer(help="Turn a transcript into a workbench proposal and optionally apply it.")


@app.command()
def propose(
    transcript: Path = typer.Option(..., exists=True, dir_okay=False, readable=True),
    workbench: Path = typer.Option(..., exists=True, file_okay=False, readable=True),
    backend: str = typer.Option("rule-based", help="Candidate extraction backend"),
    extractor_command: str | None = typer.Option(
        None,
        help="External command for the external-command backend. It receives JSON on stdin and must emit candidate JSON on stdout.",
    ),
    output_dir: Path = typer.Option(
        Path("runtime/proposals/latest"),
        help="Directory for preplan-brief.md, proposal.md, transcript_bundle.json, and internal apply data",
    ),
) -> None:
    turns = load_transcript(transcript)
    transcript_bundle = build_transcript_bundle(str(transcript.resolve()), turns)
    snapshot = load_workbench_snapshot(workbench)
    candidates = get_backend(backend, extractor_command=extractor_command).extract(
        transcript_bundle, snapshot
    )
    proposal = build_proposal(str(transcript.resolve()), snapshot, transcript_bundle, candidates)
    artifacts = write_proposal_bundle(proposal, output_dir, transcript_bundle=transcript_bundle)
    typer.echo(f"proposal_id={proposal.proposal_id}")
    typer.echo(f"preplan_brief={artifacts.preplan_brief_path}")
    typer.echo(f"proposal_markdown={artifacts.proposal_markdown_path}")
    typer.echo(f"proposal_json={artifacts.proposal_json_path}")
    if artifacts.transcript_bundle_path:
        typer.echo(f"transcript_bundle={artifacts.transcript_bundle_path}")


@app.command()
def apply(
    proposal: Path = typer.Option(..., exists=True, dir_okay=False, readable=True),
    workbench: Path = typer.Option(..., exists=True, file_okay=False, readable=True),
) -> None:
    bundle = ProposalBundle.model_validate(
        json.loads(proposal.read_text(encoding="utf-8"))
    )
    apply_proposal(bundle, workbench, current_date=date.today())
    typer.echo(f"applied_proposal={bundle.proposal_id}")


if __name__ == "__main__":
    app()
