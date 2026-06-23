"""Tests for the human review checkpoint mechanism."""

import pytest
import tempfile
from pathlib import Path
import json

from ut_analysis.state_management import ReviewCheckpointManager
from ut_analysis.models import HumanReviewCheckpoint, ReviewGate


@pytest.fixture
def temp_project_dir():
    """Create temporary project directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def review_manager(temp_project_dir):
    """Create a review checkpoint manager."""
    return ReviewCheckpointManager(temp_project_dir)


@pytest.fixture
def sample_checkpoints(review_manager):
    """Create sample review checkpoints."""
    data = {
        "checkpoints": [
            {
                "checkpoint_id": "RC_CRIT_001",
                "stage": "post_synthesis_critique",
                "reason": "Evidence strength is 'weak'",
                "related_artifact_id": "I_001",
                "artifact_type": "insight",
                "severity": "high",
                "suggested_reviewer_action": "Review evidence for insight I_001",
                "status": "pending",
                "created_at": "2026-06-23T10:00:00",
            },
            {
                "checkpoint_id": "RC_CRIT_002",
                "stage": "post_synthesis_critique",
                "reason": "Confidence below threshold",
                "related_artifact_id": "I_003",
                "artifact_type": "insight",
                "severity": "medium",
                "suggested_reviewer_action": "Verify participant attribution",
                "status": "pending",
                "created_at": "2026-06-23T10:01:00",
            },
        ]
    }
    review_manager.save_checkpoints("critic_001_review", data)
    return "critic_001_review"


class TestReviewCheckpointManager:
    """Tests for ReviewCheckpointManager."""

    def test_save_and_load_checkpoints(self, review_manager, sample_checkpoints):
        """Should save and load checkpoints correctly."""
        data = review_manager.load_checkpoints(sample_checkpoints)
        assert len(data["checkpoints"]) == 2
        assert data["checkpoints"][0]["checkpoint_id"] == "RC_CRIT_001"

    def test_list_checkpoints(self, review_manager, sample_checkpoints):
        """Should list available checkpoint batches."""
        batches = review_manager.list_checkpoints()
        assert "critic_001_review" in batches

    def test_update_checkpoint_status(self, review_manager, sample_checkpoints):
        """Should update checkpoint status."""
        updated = review_manager.update_checkpoint_status(
            batch_id=sample_checkpoints,
            checkpoint_id="RC_CRIT_001",
            status="approved",
            reviewer_notes="Evidence verified manually",
            reviewed_by="researcher@example.com",
        )

        assert updated["status"] == "approved"
        assert updated["reviewer_notes"] == "Evidence verified manually"
        assert updated["reviewed_by"] == "researcher@example.com"
        assert "reviewed_at" in updated

        # Verify persistence
        reloaded = review_manager.load_checkpoints(sample_checkpoints)
        cp = reloaded["checkpoints"][0]
        assert cp["status"] == "approved"

    def test_update_nonexistent_checkpoint_raises(self, review_manager, sample_checkpoints):
        """Should raise error for nonexistent checkpoint ID."""
        with pytest.raises(ValueError, match="Checkpoint not found"):
            review_manager.update_checkpoint_status(
                batch_id=sample_checkpoints,
                checkpoint_id="NONEXISTENT",
                status="approved",
            )

    def test_get_pending_checkpoints(self, review_manager, sample_checkpoints):
        """Should return all pending checkpoints."""
        pending = review_manager.get_pending_checkpoints()
        assert len(pending) == 2
        assert all(cp["status"] == "pending" for cp in pending)

    def test_get_pending_after_approval(self, review_manager, sample_checkpoints):
        """Approved checkpoints should not appear in pending list."""
        review_manager.update_checkpoint_status(
            batch_id=sample_checkpoints,
            checkpoint_id="RC_CRIT_001",
            status="approved",
        )

        pending = review_manager.get_pending_checkpoints()
        assert len(pending) == 1
        assert pending[0]["checkpoint_id"] == "RC_CRIT_002"

    def test_load_missing_raises(self, review_manager):
        """Should raise FileNotFoundError for missing batch."""
        with pytest.raises(FileNotFoundError):
            review_manager.load_checkpoints("nonexistent")


class TestHumanReviewCheckpointModel:
    """Tests for the HumanReviewCheckpoint Pydantic model."""

    def test_create_checkpoint(self):
        """Should create a valid checkpoint."""
        cp = HumanReviewCheckpoint(
            checkpoint_id="RC_TEST_001",
            stage="post_synthesis_critique",
            reason="Low confidence score",
            related_artifact_id="I_001",
            artifact_type="insight",
            severity="high",
            suggested_reviewer_action="Review evidence quality",
        )

        assert cp.status == "pending"
        assert cp.checkpoint_id == "RC_TEST_001"
        assert cp.reviewed_at is None

    def test_checkpoint_serialization(self):
        """Should serialize to dict cleanly."""
        cp = HumanReviewCheckpoint(
            checkpoint_id="RC_TEST_002",
            stage="post_reconciliation",
            reason="Contradiction unresolved",
            related_artifact_id="RECON_001",
            artifact_type="reconciliation",
            severity="medium",
            suggested_reviewer_action="Verify reconciliation logic",
        )

        data = cp.model_dump()
        assert data["status"] == "pending"
        assert data["artifact_type"] == "reconciliation"


class TestReviewGateModel:
    """Tests for the ReviewGate model."""

    def test_review_gate_all_approved(self):
        """Gate should detect when all checkpoints are approved."""
        cp1 = HumanReviewCheckpoint(
            checkpoint_id="RC_001",
            stage="critique",
            reason="test",
            related_artifact_id="I_001",
            artifact_type="insight",
            severity="low",
            suggested_reviewer_action="Review",
            status="approved",
        )
        cp2 = HumanReviewCheckpoint(
            checkpoint_id="RC_002",
            stage="critique",
            reason="test",
            related_artifact_id="I_002",
            artifact_type="insight",
            severity="low",
            suggested_reviewer_action="Review",
            status="approved",
        )

        gate = ReviewGate(
            gate_id="GATE_001",
            stage="critique",
            checkpoints=[cp1, cp2],
            all_approved=all(cp.status == "approved" for cp in [cp1, cp2]),
            blocking_count=sum(1 for cp in [cp1, cp2] if cp.status == "pending"),
        )

        assert gate.all_approved is True
        assert gate.blocking_count == 0

    def test_review_gate_with_pending(self):
        """Gate should track blocking checkpoints."""
        cp1 = HumanReviewCheckpoint(
            checkpoint_id="RC_001",
            stage="critique",
            reason="test",
            related_artifact_id="I_001",
            artifact_type="insight",
            severity="high",
            suggested_reviewer_action="Review",
            status="pending",
        )

        gate = ReviewGate(
            gate_id="GATE_002",
            stage="critique",
            checkpoints=[cp1],
            all_approved=False,
            blocking_count=1,
        )

        assert gate.all_approved is False
        assert gate.blocking_count == 1
