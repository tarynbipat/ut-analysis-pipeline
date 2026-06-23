"""Tests for the ut-critic evidence challenge agent."""

import pytest
import tempfile
from pathlib import Path
import json

from ut_analysis.skills.ut_critic.critic import CriticSkill
from ut_analysis.state_management import StateManager, SynthesisManager


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
def synthesis_with_strong_evidence(state_manager):
    """Create synthesis data with strong evidence (many participants)."""
    synthesis_manager = SynthesisManager(state_manager.project_dir / "data")
    synthesis_data = {
        "synthesis_batch_id": "synth_001",
        "insights": [
            {
                "insight_id": "I_001",
                "title": "Checkout Flow Issues",
                "theme": "checkout_flow",
                "severity": "critical",
                "description": "Multiple participants struggled with checkout",
                "evidence": {
                    "finding_ids": ["F_001", "F_002", "F_003", "F_004"],
                    "participant_count": 4,
                    "task_count": 2,
                    "severity_distribution": {"3": 3, "2": 1},
                },
                "patterns": {
                    "cross_participant": "4 participants affected",
                    "cross_task": "2 tasks",
                    "workflow_impact": "Critical",
                },
                "recommendations": [],
            }
        ],
    }
    synthesis_manager.save_synthesis("synth_001", synthesis_data)
    return "synth_001"


@pytest.fixture
def synthesis_with_weak_evidence(state_manager):
    """Create synthesis data with weak evidence (single participant)."""
    synthesis_manager = SynthesisManager(state_manager.project_dir / "data")
    synthesis_data = {
        "synthesis_batch_id": "synth_weak",
        "insights": [
            {
                "insight_id": "I_001",
                "title": "All users hate the navigation",
                "theme": "navigation",
                "severity": "critical",
                "description": "All users struggled with navigation always",
                "evidence": {
                    "finding_ids": ["F_001"],
                    "participant_count": 1,
                    "task_count": 1,
                    "severity_distribution": {"3": 1},
                },
                "patterns": {
                    "cross_participant": "1 participant",
                    "cross_task": "1 task",
                    "workflow_impact": "Critical",
                },
                "recommendations": [],
            },
            {
                "insight_id": "I_002",
                "title": "Minor button color issue",
                "theme": "visual_design",
                "severity": "low",
                "description": "Button color was slightly off",
                "evidence": {
                    "finding_ids": ["F_002"],
                    "participant_count": 1,
                    "task_count": 1,
                    "severity_distribution": {"0": 1},
                },
                "patterns": {
                    "cross_participant": "1 participant",
                    "cross_task": "1 task",
                    "workflow_impact": "Minor",
                },
                "recommendations": [],
            },
        ],
    }
    synthesis_manager.save_synthesis("synth_weak", synthesis_data)
    return "synth_weak"


class TestCriticSkill:
    """Tests for CriticSkill."""

    def test_critique_strong_evidence(self, state_manager, synthesis_with_strong_evidence):
        """Critic should pass insights with strong evidence."""
        critic = CriticSkill(state_manager)
        result = critic.critique_synthesis(
            synthesis_batch_id=synthesis_with_strong_evidence,
            critic_batch_id="critic_001",
        )

        assert "critiques" in result
        assert len(result["critiques"]) == 1
        critique = result["critiques"][0]
        assert critique["evidence_strength"] == "strong"
        assert critique["requires_human_review"] is False

    def test_critique_weak_evidence_flags_review(
        self, state_manager, synthesis_with_weak_evidence
    ):
        """Critic should flag weak evidence for human review."""
        critic = CriticSkill(state_manager)
        result = critic.critique_synthesis(
            synthesis_batch_id=synthesis_with_weak_evidence,
            critic_batch_id="critic_002",
        )

        assert "critiques" in result
        critiques = result["critiques"]

        # First insight: single participant, critical severity, absolute language
        high_sev_critique = critiques[0]
        assert high_sev_critique["evidence_strength"] in ("weak", "insufficient")
        assert high_sev_critique["requires_human_review"] is True
        assert len(high_sev_critique["issues_found"]) > 0
        assert len(high_sev_critique["overgeneralizations"]) > 0

    def test_critique_detects_absolute_language(
        self, state_manager, synthesis_with_weak_evidence
    ):
        """Critic should detect absolute language like 'all users'."""
        critic = CriticSkill(state_manager)
        result = critic.critique_synthesis(
            synthesis_batch_id=synthesis_with_weak_evidence,
            critic_batch_id="critic_003",
        )

        first_critique = result["critiques"][0]
        assert "absolute_language" in first_critique["issues_found"]

    def test_critique_generates_review_checkpoints(
        self, state_manager, synthesis_with_weak_evidence
    ):
        """Critic should generate review checkpoints for flagged items."""
        critic = CriticSkill(state_manager)
        result = critic.critique_synthesis(
            synthesis_batch_id=synthesis_with_weak_evidence,
            critic_batch_id="critic_004",
        )

        assert "review_checkpoints" in result
        checkpoints = result["review_checkpoints"]
        assert len(checkpoints) > 0

        cp = checkpoints[0]
        assert cp["stage"] == "post_synthesis_critique"
        assert cp["status"] == "pending"
        assert cp["artifact_type"] == "insight"

    def test_critique_overall_quality_assessment(
        self, state_manager, synthesis_with_strong_evidence
    ):
        """Critic should produce an overall quality assessment."""
        critic = CriticSkill(state_manager)
        result = critic.critique_synthesis(
            synthesis_batch_id=synthesis_with_strong_evidence,
            critic_batch_id="critic_005",
        )

        assert result["overall_evidence_quality"] in (
            "high", "acceptable", "concerning", "inadequate"
        )

    def test_critique_empty_synthesis_returns_error(self, state_manager):
        """Critic should handle empty synthesis gracefully."""
        synthesis_manager = SynthesisManager(state_manager.project_dir / "data")
        synthesis_manager.save_synthesis("synth_empty", {"insights": []})

        critic = CriticSkill(state_manager)
        result = critic.critique_synthesis(
            synthesis_batch_id="synth_empty",
            critic_batch_id="critic_006",
        )

        assert result["status"] == "error"
        assert "No insights" in result["error"]

    def test_critique_missing_synthesis_returns_error(self, state_manager):
        """Critic should handle missing synthesis data."""
        critic = CriticSkill(state_manager)
        result = critic.critique_synthesis(
            synthesis_batch_id="nonexistent",
            critic_batch_id="critic_007",
        )

        assert result["status"] == "error"

    def test_custom_config(self, state_manager, synthesis_with_weak_evidence):
        """Critic should respect custom configuration."""
        critic = CriticSkill(state_manager)
        result = critic.critique_synthesis(
            synthesis_batch_id=synthesis_with_weak_evidence,
            critic_batch_id="critic_008",
            critic_config={"min_participants_for_pattern": 1},
        )

        # With min_participants=1, the single participant insight should be less flagged
        critiques = result["critiques"]
        # The low-severity one should have fewer issues
        low_sev = [c for c in critiques if c["target_id"] == "I_002"]
        if low_sev:
            assert "insufficient_participant_count" not in low_sev[0]["issues_found"]

    def test_critique_persists_results(self, state_manager, synthesis_with_strong_evidence):
        """Critic should persist results via CriticManager."""
        critic = CriticSkill(state_manager)
        critic.critique_synthesis(
            synthesis_batch_id=synthesis_with_strong_evidence,
            critic_batch_id="critic_persist",
        )

        # Verify file was written
        critique_file = (
            state_manager.project_dir / "data" / "critiques" / "critic_persist_critique.json"
        )
        assert critique_file.exists()

        data = json.loads(critique_file.read_text())
        assert "critiques" in data
