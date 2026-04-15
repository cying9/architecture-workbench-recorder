from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CLI_PATH = REPO_ROOT / "source_code" / "awr" / "cli.py"
FIXTURES = REPO_ROOT / "tests" / "fixtures"
TRANSCRIPT = FIXTURES / "sample-transcript.md"
STRUCTURED_TRANSCRIPT = FIXTURES / "structured-transcript.json"
WORKBENCH = FIXTURES / "sample-workbench"
EXTERNAL_BACKEND_SCRIPT = FIXTURES / "mock_external_backend.py"
WRAPPER_PATH = REPO_ROOT / "scripts" / "invoke-discussion-checkpoint.ps1"
PRIMARY_SKILL = REPO_ROOT / "skills" / "architecture-workbench-discussion" / "SKILL.md"
ALIAS_SKILL = REPO_ROOT / "skills" / "plan-helper" / "SKILL.md"
ALIAS_META = REPO_ROOT / "skills" / "plan-helper" / "agents" / "openai.yaml"


class RecorderCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp(prefix="awr-test-"))
        self.workbench_dir = self.temp_dir / "workbench"
        shutil.copytree(WORKBENCH, self.workbench_dir)
        self.output_dir = self.temp_dir / "proposal-out"

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(CLI_PATH), *args],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    def run_wrapper(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(WRAPPER_PATH),
                *args,
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    def test_propose_creates_human_and_machine_readable_bundle(self) -> None:
        result = self.run_cli(
            "propose",
            "--transcript",
            str(TRANSCRIPT),
            "--workbench",
            str(self.workbench_dir),
            "--output-dir",
            str(self.output_dir),
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)

        preplan_brief = self.output_dir / "preplan-brief.md"
        proposal_md = self.output_dir / "proposal.md"
        proposal_json = self.output_dir / ".internal" / "proposal.json"
        self.assertTrue(preplan_brief.exists())
        self.assertTrue(proposal_md.exists())
        self.assertTrue(proposal_json.exists())

        brief_text = preplan_brief.read_text(encoding="utf-8")
        proposal_text = proposal_md.read_text(encoding="utf-8")
        self.assertIn("Pre-Plan Brief", brief_text)
        self.assertIn("Stable Decisions", brief_text)
        self.assertIn("Proposed Decision Log Updates", proposal_text)
        self.assertIn("transcript bundle", proposal_text)
        self.assertIn("generic meeting notes system", proposal_text)

        proposal = json.loads(proposal_json.read_text(encoding="utf-8"))
        self.assertEqual(proposal["summary"]["candidate_counts"]["decided"], 1)
        self.assertEqual(proposal["summary"]["candidate_counts"]["working_hypothesis"], 1)
        self.assertEqual(proposal["summary"]["candidate_counts"]["open_question"], 1)
        self.assertEqual(proposal["summary"]["candidate_counts"]["glossary_candidate"], 1)
        self.assertEqual(proposal["summary"]["candidate_counts"]["thread_milestone"], 1)

    def test_apply_updates_target_files_without_full_rewrite(self) -> None:
        propose = self.run_cli(
            "propose",
            "--transcript",
            str(TRANSCRIPT),
            "--workbench",
            str(self.workbench_dir),
            "--output-dir",
            str(self.output_dir),
        )
        self.assertEqual(propose.returncode, 0, msg=propose.stderr or propose.stdout)

        proposal_json = self.output_dir / ".internal" / "proposal.json"
        apply_result = self.run_cli(
            "apply",
            "--proposal",
            str(proposal_json),
            "--workbench",
            str(self.workbench_dir),
        )
        self.assertEqual(apply_result.returncode, 0, msg=apply_result.stderr or apply_result.stdout)

        glossary_text = (self.workbench_dir / "glossary.md").read_text(encoding="utf-8")
        decision_text = (self.workbench_dir / "decision-log.md").read_text(encoding="utf-8")
        questions_text = (self.workbench_dir / "open-questions.md").read_text(encoding="utf-8")
        thread_text = (self.workbench_dir / "thread-log.md").read_text(encoding="utf-8")
        readme_text = (self.workbench_dir / "README.md").read_text(encoding="utf-8")

        self.assertIn("### `transcript bundle`", glossary_text)
        self.assertIn("## 2026-04-15", decision_text)
        self.assertIn("proposal-first", decision_text)
        self.assertIn("README updates should ever be applied automatically", questions_text)
        self.assertIn("## 2026-04-15", thread_text)
        self.assertIn("conversation-to-workbench", thread_text)
        self.assertEqual(readme_text, WORKBENCH.joinpath("README.md").read_text(encoding="utf-8"))

    def test_propose_writes_transcript_bundle_and_filters_rejected_probe(self) -> None:
        result = self.run_cli(
            "propose",
            "--transcript",
            str(STRUCTURED_TRANSCRIPT),
            "--workbench",
            str(self.workbench_dir),
            "--output-dir",
            str(self.output_dir),
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)

        bundle_json = self.output_dir / "transcript_bundle.json"
        preplan_brief = self.output_dir / "preplan-brief.md"
        proposal_md = self.output_dir / "proposal.md"
        proposal_json = self.output_dir / ".internal" / "proposal.json"
        self.assertTrue(bundle_json.exists())
        self.assertTrue(preplan_brief.exists())

        bundle = json.loads(bundle_json.read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(bundle["claims"]), 3)
        rejected = [claim for claim in bundle["claims"] if claim["disposition"] == "rejected"]
        self.assertTrue(rejected)

        proposal_text = proposal_md.read_text(encoding="utf-8")
        brief_text = preplan_brief.read_text(encoding="utf-8")
        self.assertNotIn("auto-overwrite README", proposal_text)
        self.assertIn("README changes as proposal-only", proposal_text)
        self.assertIn("Planning Readiness", brief_text)
        self.assertIn("Rejected probes kept out of planning inputs", brief_text)

        proposal = json.loads(proposal_json.read_text(encoding="utf-8"))
        self.assertEqual(proposal["summary"]["discarded_probe_count"], 1)

    def test_external_command_backend_can_supply_candidates(self) -> None:
        result = self.run_cli(
            "propose",
            "--transcript",
            str(TRANSCRIPT),
            "--workbench",
            str(self.workbench_dir),
            "--backend",
            "external-command",
            "--extractor-command",
            f"{sys.executable} {EXTERNAL_BACKEND_SCRIPT}",
            "--output-dir",
            str(self.output_dir),
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)

        proposal = json.loads((self.output_dir / ".internal" / "proposal.json").read_text(encoding="utf-8"))
        glossary_candidates = [
            item for item in proposal["candidates"] if item["type"] == "glossary_candidate"
        ]
        self.assertTrue(any(item["term"] == "external term" for item in glossary_candidates))

    def test_manual_wrapper_runs_propose_checkpoint(self) -> None:
        wrapper_output = self.temp_dir / "wrapper-out"
        result = self.run_wrapper(
            "-Mode",
            "propose",
            "-Transcript",
            str(TRANSCRIPT),
            "-Workbench",
            str(self.workbench_dir),
            "-OutputName",
            "wrapper-test",
            "-OutputDir",
            str(wrapper_output),
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertIn("proposal_id=", result.stdout)
        self.assertTrue((wrapper_output / "preplan-brief.md").exists())
        self.assertTrue((wrapper_output / ".internal" / "proposal.json").exists())

    def test_primary_skill_is_manual_only(self) -> None:
        self.assertTrue(PRIMARY_SKILL.exists())
        text = PRIMARY_SKILL.read_text(encoding="utf-8")
        self.assertIn("Manual Trigger Only", text)
        self.assertIn("Do not auto-activate", text)
        self.assertIn("preplan-brief.md", text)
        self.assertIn("proposal.md", text)
        self.assertIn("transcript_bundle.json", text)

    def test_plan_helper_alias_is_installed(self) -> None:
        self.assertTrue(ALIAS_SKILL.exists())
        self.assertTrue(ALIAS_META.exists())
        text = ALIAS_SKILL.read_text(encoding="utf-8")
        meta = ALIAS_META.read_text(encoding="utf-8")
        self.assertIn("Plan Helper", text)
        self.assertIn("manual trigger only", text.lower())
        self.assertIn('display_name: "计划小助手"', meta)


if __name__ == "__main__":
    unittest.main()
