"""Tests for the enhanced contradiction reconciler skill."""

import json

from ut_analysis.skills.ut_contradiction_reconciler.contradiction_reconciler import (
    ContradictionReconcilerSkill,
)
from ut_analysis.state_management import StateManager


def test_contradiction_reconciler_preserves_tension_and_persists(tmp_path):
    """The reconciler should preserve contradictions as signal and save output."""
    state_manager = StateManager(tmp_path)
    skill = ContradictionReconcilerSkill(state_manager)

    contradictions = [
        {
            "contradiction_id": "CONTRA_001",
            "description": "Novice users expected a guided flow while experts preferred speed",
            "affected_findings": ["F_001", "F_002"],
        }
    ]
    findings = [
        {
            "finding_id": "F_001",
            "participant_id": "P001",
            "description": "Participant liked the guided setup and found it helpful",
        },
        {
            "finding_id": "F_002",
            "participant_id": "P002",
            "description": "Participant found the setup slow and confusing",
        },
    ]

    result = skill.reconcile_contradictions(
        contradictions=contradictions,
        findings=findings,
        batch_id="recon_batch",
    )

    assert result["summary"]["total_contradictions"] == 1
    assert result["reconciliations"][0]["explanation_factors"] == [
        "segment",
        "experience_level",
        "product_expectation",
    ]
    assert "Rather than averaging these views" in result["reconciliations"][0][
        "reconciled_interpretation"
    ]

    persisted_path = (
        tmp_path / "data" / "reconciliations" / "recon_batch_reconciliation.json"
    )
    assert persisted_path.exists()
    assert json.loads(persisted_path.read_text())["reconciliation_batch_id"] == "recon_batch"


def test_contradiction_reconciler_defaults_to_evidence_limits(tmp_path):
    """The reconciler should flag evidence limits when explanation factors are unclear."""
    state_manager = StateManager(tmp_path)
    skill = ContradictionReconcilerSkill(state_manager)

    result = skill.reconcile_contradictions(
        contradictions=[
            {
                "contradiction_id": "CONTRA_002",
                "description": "Participants reacted differently",
                "affected_findings": ["F_003"],
            }
        ],
        findings=[
            {
                "finding_id": "F_003",
                "participant_id": "P003",
                "description": "Participant reacted differently",
            }
        ],
        batch_id="recon_unclear",
    )

    reconciliation = result["reconciliations"][0]
    assert reconciliation["explanation_factors"] == ["evidence_limits"]
    assert reconciliation["further_research_needed"] is True
