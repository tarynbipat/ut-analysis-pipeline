"""Tests for thematic specialist analyst skills."""

import tempfile
from pathlib import Path
from typing import Any

import pytest

from ut_analysis.skills.ut_behavior_analyst.behavior_analyst import BehaviorAnalystSkill
from ut_analysis.skills.ut_mental_model_analyst.mental_model_analyst import (
    MentalModelAnalystSkill,
)
from ut_analysis.skills.ut_needs_analyst.needs_analyst import NeedsAnalystSkill
from ut_analysis.skills.ut_pain_point_analyst.pain_point_analyst import (
    PainPointAnalystSkill,
)
from ut_analysis.skills.ut_trust_analyst.trust_analyst import TrustAnalystSkill
from ut_analysis.skills.ut_workflow_analyst.workflow_analyst import WorkflowAnalystSkill
from ut_analysis.state_management import StateManager, ThematicAnalysisManager


@pytest.fixture
def temp_project_dir() -> Path:
    """Create temporary project directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.mark.parametrize(
    ("skill_class", "lane_id", "lane_name", "agent_name"),
    [
        (
            PainPointAnalystSkill,
            "pain_points",
            "Pain Points",
            "pain-point-analyst",
        ),
        (NeedsAnalystSkill, "needs", "User Needs", "needs-analyst"),
        (
            BehaviorAnalystSkill,
            "behaviors",
            "Behavioral Patterns",
            "behavior-analyst",
        ),
        (
            MentalModelAnalystSkill,
            "mental_models",
            "Mental Models",
            "mental-model-analyst",
        ),
        (
            TrustAnalystSkill,
            "trust",
            "Trust and Confidence",
            "trust-analyst",
        ),
        (
            WorkflowAnalystSkill,
            "workflow",
            "Workflow Breakdowns",
            "workflow-analyst",
        ),
    ],
)
def test_lane_analysis_skills(
    temp_project_dir: Path,
    skill_class: type[Any],
    lane_id: str,
    lane_name: str,
    agent_name: str,
) -> None:
    """Each thematic analyst groups findings, persists output, and returns themes."""
    state_manager = StateManager(temp_project_dir)
    thematic_manager = ThematicAnalysisManager(temp_project_dir / "data")
    skill = skill_class(state_manager, thematic_manager)

    lane_data = {
        "lane_id": lane_id,
        "lane_name": lane_name,
        "finding_ids": ["F1", "F2", "F3"],
        "findings": [
            {
                "finding_id": "F1",
                "title": "Users hit friction in checkout",
                "description": "Users feel confused by the checkout flow and need help",
                "participant_id": "P1",
                "task_id": "T1",
                "severity": 3,
                "verbatim_quote": "I got confused during checkout.",
            },
            {
                "finding_id": "F2",
                "title": "Checkout remains confusing",
                "description": "The checkout flow feels confusing and users want clearer help",
                "participant_id": "P2",
                "task_id": "T1",
                "severity": 2,
                "verbatim_quote": "I want clearer guidance here.",
            },
            {
                "finding_id": "F3",
                "title": "Separate issue",
                "description": "Users verify the result before they continue to the next step",
                "participant_id": "P3",
                "task_id": "T2",
                "severity": 1,
                "verbatim_quote": "I double-check before moving on.",
            },
        ],
    }

    result = skill.analyze_lane(lane_data, run_id="run_001")

    assert result["lane_id"] == lane_id
    assert result["lane_name"] == lane_name
    assert result["agent_name"] == agent_name
    assert len(result["themes"]) == 2
    assert result["themes"][0]["evidence_count"] == 2
    assert result["themes"][1]["evidence_count"] == 1
    assert result["themes"][1]["confidence"] < result["themes"][0]["confidence"]

    persisted = thematic_manager.load_lane_analysis(lane_id)
    assert persisted == result
