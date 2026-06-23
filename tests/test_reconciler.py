"""Tests for the ut-reconciler contradiction reconciliation agent."""

import pytest
import tempfile
from pathlib import Path
import json

from ut_analysis.skills.ut_reconciler.reconciler import ReconcilerSkill
from ut_analysis.state_management import (
    StateManager,
    ContradictionsManager,
    SynthesisManager,
)


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
def contradictions_data(state_manager):
    """Create sample contradictions data."""
    contra_manager = ContradictionsManager(state_manager.project_dir / "data")
    data = {
        "contradictions_batch_id": "contra_001",
        "contradictions": [
            {
                "contradiction_id": "CONTRA_001",
                "type": "participant_disagreement",
                "severity": "high",
                "description": "Conflicting outcomes for TASK-001 across participants",
                "affected_findings": ["F_001", "F_002", "F_003"],
                "evidence": {
                    "participant_agreement": {
                        "P001": "success",
                        "P002": "failure",
                        "P003": "success",
                        "P004": "failure",
                    },
                    "consistency_score": 0.5,
                    "pattern_type": "split_opinion",
                },
                "analysis": {
                    "possible_causes": [
                        "Task ambiguity in instructions",
                        "Different user approaches to same goal",
                    ],
                    "recommended_action": "Clarify task instructions",
                    "confidence_impact": "medium",
                    "validation_needed": True,
                },
                "resolution_suggestions": [],
            },
            {
                "contradiction_id": "CONTRA_002",
                "type": "temporal_inconsistency",
                "severity": "low",
                "description": "P001 changed approach to navigation mid-session",
                "affected_findings": ["F_004", "F_005"],
                "evidence": {
                    "participant_agreement": {
                        "P001": "inconsistent",
                    },
                    "consistency_score": 0.7,
                    "pattern_type": "temporal_shift",
                },
                "analysis": {
                    "possible_causes": ["Learning effect during session"],
                    "recommended_action": "Note temporal context",
                    "confidence_impact": "low",
                    "validation_needed": False,
                },
                "resolution_suggestions": [],
            },
        ],
    }
    contra_manager.save_contradictions("contra_001", data)
    return "contra_001"


@pytest.fixture
def synthesis_data(state_manager):
    """Create sample synthesis data for theme context."""
    synthesis_manager = SynthesisManager(state_manager.project_dir / "data")
    data = {
        "synthesis_batch_id": "synth_001",
        "insights": [
            {
                "insight_id": "I_001",
                "title": "Checkout Issues",
                "theme": "checkout_flow",
                "severity": "high",
                "description": "Checkout problems",
                "evidence": {
                    "finding_ids": ["F_001", "F_002"],
                    "participant_count": 3,
                    "task_count": 1,
                    "severity_distribution": {"3": 2},
                },
            },
            {
                "insight_id": "I_002",
                "title": "Navigation Issues",
                "theme": "navigation",
                "severity": "medium",
                "description": "Nav problems",
                "evidence": {
                    "finding_ids": ["F_004", "F_005"],
                    "participant_count": 2,
                    "task_count": 1,
                    "severity_distribution": {"2": 1},
                },
            },
        ],
    }
    synthesis_manager.save_synthesis("synth_001", data)
    return "synth_001"


class TestReconcilerSkill:
    """Tests for ReconcilerSkill."""

    def test_reconcile_basic(self, state_manager, contradictions_data):
        """Reconciler should produce reconciliations from contradictions."""
        reconciler = ReconcilerSkill(state_manager)
        result = reconciler.reconcile_contradictions(
            contradictions_batch_id=contradictions_data,
            reconciliation_batch_id="recon_001",
        )

        assert "reconciliations" in result
        assert len(result["reconciliations"]) > 0

    def test_reconcile_produces_participant_groups(
        self, state_manager, contradictions_data
    ):
        """Reconciler should segment participants into groups."""
        reconciler = ReconcilerSkill(state_manager)
        result = reconciler.reconcile_contradictions(
            contradictions_batch_id=contradictions_data,
            reconciliation_batch_id="recon_002",
        )

        recon = result["reconciliations"][0]
        assert "participant_groups" in recon
        groups = recon["participant_groups"]
        assert len(groups) >= 1

    def test_reconcile_generates_explanations(
        self, state_manager, contradictions_data
    ):
        """Reconciler should generate possible explanations."""
        reconciler = ReconcilerSkill(state_manager)
        result = reconciler.reconcile_contradictions(
            contradictions_batch_id=contradictions_data,
            reconciliation_batch_id="recon_003",
        )

        recon = result["reconciliations"][0]
        assert "possible_explanations" in recon
        assert len(recon["possible_explanations"]) > 0

    def test_reconcile_generates_design_implications(
        self, state_manager, contradictions_data
    ):
        """Reconciler should generate design implications."""
        reconciler = ReconcilerSkill(state_manager)
        result = reconciler.reconcile_contradictions(
            contradictions_batch_id=contradictions_data,
            reconciliation_batch_id="recon_004",
        )

        recon = result["reconciliations"][0]
        assert "design_implication" in recon
        assert len(recon["design_implication"]) > 0

    def test_reconcile_with_synthesis_context(
        self, state_manager, contradictions_data, synthesis_data
    ):
        """Reconciler should use synthesis context when available."""
        reconciler = ReconcilerSkill(state_manager)
        result = reconciler.reconcile_contradictions(
            contradictions_batch_id=contradictions_data,
            synthesis_batch_id=synthesis_data,
            reconciliation_batch_id="recon_005",
        )

        assert "reconciliations" in result
        # Should still work and incorporate theme context
        assert len(result["reconciliations"]) > 0

    def test_reconcile_identifies_research_gaps(
        self, state_manager, contradictions_data
    ):
        """Reconciler should identify research gaps."""
        reconciler = ReconcilerSkill(state_manager)
        result = reconciler.reconcile_contradictions(
            contradictions_batch_id=contradictions_data,
            reconciliation_batch_id="recon_006",
        )

        assert "research_gaps" in result
        assert len(result["research_gaps"]) > 0

    def test_reconcile_generates_research_questions(
        self, state_manager, contradictions_data
    ):
        """Reconciler should generate follow-up research questions."""
        reconciler = ReconcilerSkill(state_manager)
        result = reconciler.reconcile_contradictions(
            contradictions_batch_id=contradictions_data,
            reconciliation_batch_id="recon_007",
            reconciliation_config={"generate_research_questions": True},
        )

        # At least one reconciliation should have research questions
        has_questions = any(
            len(r.get("research_questions", [])) > 0
            for r in result["reconciliations"]
        )
        assert has_questions

    def test_reconcile_flags_for_review(self, state_manager, contradictions_data):
        """Reconciler should generate review checkpoints for uncertain reconciliations."""
        reconciler = ReconcilerSkill(state_manager)
        result = reconciler.reconcile_contradictions(
            contradictions_batch_id=contradictions_data,
            reconciliation_batch_id="recon_008",
        )

        # High severity contradiction with balanced groups should trigger review
        assert "review_checkpoints" in result

    def test_reconcile_empty_contradictions_returns_error(self, state_manager):
        """Reconciler should handle empty contradiction list."""
        contra_manager = ContradictionsManager(state_manager.project_dir / "data")
        contra_manager.save_contradictions("contra_empty", {"contradictions": []})

        reconciler = ReconcilerSkill(state_manager)
        result = reconciler.reconcile_contradictions(
            contradictions_batch_id="contra_empty",
            reconciliation_batch_id="recon_009",
        )

        assert result["status"] == "error"

    def test_reconcile_missing_contradictions_returns_error(self, state_manager):
        """Reconciler should handle missing data."""
        reconciler = ReconcilerSkill(state_manager)
        result = reconciler.reconcile_contradictions(
            contradictions_batch_id="nonexistent",
            reconciliation_batch_id="recon_010",
        )

        assert result["status"] == "error"

    def test_reconcile_persists_results(self, state_manager, contradictions_data):
        """Reconciler should persist results via ReconciliationManager."""
        reconciler = ReconcilerSkill(state_manager)
        reconciler.reconcile_contradictions(
            contradictions_batch_id=contradictions_data,
            reconciliation_batch_id="recon_persist",
        )

        recon_file = (
            state_manager.project_dir
            / "data"
            / "reconciliations"
            / "recon_persist_reconciliation.json"
        )
        assert recon_file.exists()

        data = json.loads(recon_file.read_text())
        assert "reconciliations" in data

    def test_reconcile_summary_stats(self, state_manager, contradictions_data):
        """Reconciler should produce summary statistics."""
        reconciler = ReconcilerSkill(state_manager)
        result = reconciler.reconcile_contradictions(
            contradictions_batch_id=contradictions_data,
            reconciliation_batch_id="recon_011",
        )

        summary = result["summary"]
        assert "total_reconciled" in summary
        assert "total_unresolved" in summary
        assert "average_confidence" in summary
