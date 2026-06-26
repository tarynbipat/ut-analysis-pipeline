"""Tests for the pipeline run summary skill."""

import json

from ut_analysis.skills.ut_run_summary.run_summary import RunSummarySkill
from ut_analysis.state_management import StateManager


def test_run_summary_persists_json_and_markdown(tmp_path):
    """The run summary skill should write both machine and human readable artifacts."""
    state_manager = StateManager(tmp_path)
    skill = RunSummarySkill(state_manager)

    summary = skill.generate_run_summary(
        run_id="run_001",
        project_id="proj_123",
        stages_completed=["ingestion", "analysis"],
        artifacts_created=["findings.json", "summary.md"],
        agents_invoked=["ut-extractor", "ut-critic"],
        evals_passed=3,
        evals_failed=1,
        review_checkpoints_created=0,
        unresolved_issues=[],
    )

    assert summary["next_suggested_action"].startswith("Address 1 failed evaluation")

    json_path = tmp_path / "data" / "runs" / "run_001_run_summary.json"
    md_path = tmp_path / "data" / "runs" / "run_001_run_summary.md"

    assert json_path.exists()
    assert md_path.exists()
    assert json.loads(json_path.read_text())["project_id"] == "proj_123"
    assert "# Pipeline Run Summary: run_001" in md_path.read_text(encoding="utf-8")


def test_run_summary_suggests_completion_when_reporting_done(tmp_path):
    """The next action should indicate completion when reporting is complete."""
    state_manager = StateManager(tmp_path)
    skill = RunSummarySkill(state_manager)

    summary = skill.generate_run_summary(
        run_id="run_002",
        project_id="proj_456",
        stages_completed=["analysis", "reporting"],
    )

    assert summary["next_suggested_action"] == "Pipeline complete. Share report with stakeholders."
