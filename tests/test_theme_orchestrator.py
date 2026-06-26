"""Tests for the ut-theme-orchestrator skill."""

import json
import tempfile
from pathlib import Path

import pytest

from ut_analysis.skills.ut_theme_orchestrator.theme_orchestrator import ThemeOrchestratorSkill
from ut_analysis.state_management import StateManager, FindingsManager


@pytest.fixture
def temp_project_dir():
    """Create temporary project directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def state_manager(temp_project_dir):
    """Create a state manager with temp directory."""
    return StateManager(temp_project_dir)


@pytest.fixture
def findings_batch(state_manager):
    """Create a findings batch with multiple thematic signals."""
    findings_manager = FindingsManager(state_manager.project_dir / "data")
    findings_data = {
        "extraction_batch_id": "batch_001",
        "findings": [
            {
                "finding_id": "F_001",
                "category": "pain_point",
                "title": "Frustrating checkout step",
                "description": "Participant felt frustrated and stuck during the checkout flow",
                "verbatim_quote": "This is frustrating and I feel stuck.",
                "speaker": "Participant",
                "timestamp": "00:30",
                "source_transcript_id": "T_P001",
                "task_id": "TASK-001",
                "participant_id": "P001",
                "confidence": 0.95,
                "metadata": {},
            },
            {
                "finding_id": "F_002",
                "category": "participant_quote",
                "title": "User expects safer confirmation",
                "description": "The participant expects a safer and more secure confirmation step",
                "verbatim_quote": "I expect this to feel safer.",
                "speaker": "Participant",
                "timestamp": "01:00",
                "source_transcript_id": "T_P002",
                "task_id": "TASK-002",
                "participant_id": "P002",
                "confidence": 0.88,
                "metadata": {},
            },
            {
                "finding_id": "F_003",
                "category": "usability_issue",
                "title": "Repeated workaround in process",
                "description": "Participant always uses a workaround and repeats the same process path",
                "verbatim_quote": "I always use this workaround.",
                "speaker": "Participant",
                "timestamp": "01:30",
                "source_transcript_id": "T_P003",
                "task_id": "TASK-003",
                "participant_id": "P003",
                "confidence": 0.91,
                "metadata": {},
            },
        ],
    }
    findings_manager.save_findings("batch_001", findings_data)
    return "batch_001"


@pytest.fixture
def minimal_findings_batch(state_manager):
    """Create a minimal findings batch that should populate a single lane."""
    findings_manager = FindingsManager(state_manager.project_dir / "data")
    findings_data = {
        "extraction_batch_id": "batch_minimal",
        "findings": [
            {
                "finding_id": "F_100",
                "category": "pain_point",
                "title": "Annoying error dialog",
                "description": "The participant found the error dialog annoying and frustrating",
                "verbatim_quote": "This error is annoying.",
                "speaker": "Participant",
                "timestamp": "02:00",
                "source_transcript_id": "T_P100",
                "task_id": "TASK-100",
                "participant_id": "P100",
                "confidence": 0.9,
                "metadata": {},
            }
        ],
    }
    findings_manager.save_findings("batch_minimal", findings_data)
    return "batch_minimal"


class TestThemeOrchestratorSkill:
    """Tests for ThemeOrchestratorSkill."""

    def test_create_orchestration_plan(self, state_manager, findings_batch):
        """Skill should create a populated orchestration plan."""
        orchestrator = ThemeOrchestratorSkill(state_manager)

        result = orchestrator.create_orchestration_plan(
            findings_batch_id=findings_batch,
            run_id="run_001",
            project_id="proj_001",
        )

        assert result["plan_id"] == "run_001_theme_orchestration"
        assert result["findings_batch_id"] == findings_batch
        assert result["project_id"] == "proj_001"
        assert len(result["thematic_lanes"]) >= 3

    def test_only_populated_lanes_are_created(self, state_manager, minimal_findings_batch):
        """Skill should omit lanes with no assigned findings."""
        orchestrator = ThemeOrchestratorSkill(state_manager)

        result = orchestrator.create_orchestration_plan(
            findings_batch_id=minimal_findings_batch,
            run_id="run_002",
            project_id="proj_001",
        )

        lane_ids = {lane["lane_id"] for lane in result["thematic_lanes"]}
        assert "pain_points" in lane_ids
        assert lane_ids == {"pain_points"}

    def test_finding_can_appear_in_multiple_lanes(self, state_manager, findings_batch):
        """A single finding should be routable to multiple thematic lanes."""
        orchestrator = ThemeOrchestratorSkill(state_manager)

        result = orchestrator.create_orchestration_plan(
            findings_batch_id=findings_batch,
            run_id="run_003",
            project_id="proj_001",
        )

        pain_points = next(l for l in result["thematic_lanes"] if l["lane_id"] == "pain_points")
        workflow = next(
            l for l in result["thematic_lanes"] if l["lane_id"] == "workflow_breakdowns"
        )

        assert "F_001" in pain_points["finding_ids"]
        assert "F_001" in workflow["finding_ids"]

    def test_lane_handoff_preserves_provenance(self, state_manager, findings_batch):
        """Lane handoff artifacts should preserve finding, participant, and task provenance."""
        orchestrator = ThemeOrchestratorSkill(state_manager)

        result = orchestrator.create_orchestration_plan(
            findings_batch_id=findings_batch,
            run_id="run_004",
            project_id="proj_001",
        )

        trust_lane = next(l for l in result["thematic_lanes"] if l["lane_id"] == "trust_confidence")
        assert "P002" in trust_lane["participant_ids"]
        assert "TASK-002" in trust_lane["task_ids"]
        assert trust_lane["assigned_agent"] == "ut-trust-analyst"
        assert trust_lane["handoff_items"][0]["finding_id"] == "F_002"

    def test_persists_plan(self, state_manager, findings_batch):
        """Skill should persist the orchestration plan via ThemeOrchestrationManager."""
        orchestrator = ThemeOrchestratorSkill(state_manager)
        orchestrator.create_orchestration_plan(
            findings_batch_id=findings_batch,
            run_id="run_persist",
            project_id="proj_001",
        )

        plan_file = (
            state_manager.project_dir
            / "data"
            / "theme_orchestration"
            / "run_persist_theme_orchestration_plan.json"
        )
        assert plan_file.exists()

        data = json.loads(plan_file.read_text())
        assert "thematic_lanes" in data

    def test_missing_findings_returns_error(self, state_manager):
        """Skill should return an error when findings are missing."""
        orchestrator = ThemeOrchestratorSkill(state_manager)

        result = orchestrator.create_orchestration_plan(
            findings_batch_id="missing_batch",
            run_id="run_005",
            project_id="proj_001",
        )

        assert result["status"] == "error"
