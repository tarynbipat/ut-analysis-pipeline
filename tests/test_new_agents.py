"""Tests for new multi-agent research intelligence features."""

import json
import tempfile
from pathlib import Path

import pytest

from ut_analysis.models import (
    ConsolidatedTheme,
    EvalResult,
    HumanReviewCheckpoint,
    NextStudyPlan,
    PipelineRunSummary,
    ResearchGap,
    ResearchGapReport,
    RubricScore,
    ThematicLane,
    ThematicLaneAnalysis,
    ThemeConsolidation,
    ThemeOrchestrationPlan,
    ThemeResult,
)
from ut_analysis.state_management import (
    EvalRubricManager,
    FindingsManager,
    NextStudyManager,
    PipelineRunManager,
    ResearchGapManager,
    ReviewCheckpointManager,
    StateManager,
    ThematicAnalysisManager,
    ThemeOrchestrationManager,
)


@pytest.fixture
def temp_project_dir() -> Path:
    """Create temporary project directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def state_manager(temp_project_dir: Path) -> StateManager:
    """Create state manager."""
    return StateManager(temp_project_dir)


@pytest.fixture
def sample_findings(state_manager: StateManager) -> FindingsManager:
    """Create sample findings for testing."""
    findings_mgr = FindingsManager(state_manager.project_dir / "data")
    findings_data = {
        "findings": [
            {
                "finding_id": "F_001",
                "title": "Users frustrated by confusing checkout flow",
                "description": (
                    "Participant struggled with the checkout process, expressing "
                    "frustration at unclear error messages."
                ),
                "participant_id": "P001",
                "task_id": "T1",
                "category": "pain_point",
                "verbatim_quote": "I don't understand what went wrong here",
                "speaker": "Participant",
                "timestamp": "00:10",
                "source_transcript_id": "T001",
                "severity": 3,
                "confidence": 0.8,
                "metadata": {},
            },
            {
                "finding_id": "F_002",
                "title": "Users need better navigation feedback",
                "description": (
                    "Participant wanted clearer indication of their position in the workflow."
                ),
                "participant_id": "P002",
                "task_id": "T1",
                "category": "usability_issue",
                "verbatim_quote": "Where am I in this process?",
                "speaker": "Participant",
                "timestamp": "00:20",
                "source_transcript_id": "T002",
                "severity": 2,
                "confidence": 0.7,
                "metadata": {},
            },
            {
                "finding_id": "F_003",
                "title": "Trust concerns about auto-deploy",
                "description": (
                    "Participant hesitated to use auto-deploy because they doubted "
                    "the rollback safety."
                ),
                "participant_id": "P001",
                "task_id": "T2",
                "category": "usability_issue",
                "verbatim_quote": (
                    "I'm not confident I can undo this if something goes wrong"
                ),
                "speaker": "Participant",
                "timestamp": "00:30",
                "source_transcript_id": "T001",
                "severity": 3,
                "confidence": 0.85,
                "metadata": {},
            },
            {
                "finding_id": "F_004",
                "title": "Workflow abandoned at step 3",
                "description": (
                    "Participant abandoned the workflow after getting stuck on the "
                    "configuration step."
                ),
                "participant_id": "P003",
                "task_id": "T1",
                "category": "pain_point",
                "verbatim_quote": "I give up, this is too complicated",
                "speaker": "Participant",
                "timestamp": "00:40",
                "source_transcript_id": "T003",
                "severity": 4,
                "confidence": 0.9,
                "metadata": {},
            },
            {
                "finding_id": "F_005",
                "title": "Users assume deploy means production",
                "description": (
                    "Participant believed deploy would immediately push to production "
                    "environment."
                ),
                "participant_id": "P002",
                "task_id": "T2",
                "category": "usability_issue",
                "verbatim_quote": "So this goes live right away?",
                "speaker": "Participant",
                "timestamp": "00:50",
                "source_transcript_id": "T002",
                "severity": 2,
                "confidence": 0.75,
                "metadata": {},
            },
        ]
    }
    findings_mgr.save_findings("batch_001", findings_data)
    return findings_mgr


class TestThemeOrchestration:
    """Tests for theme orchestration."""

    def test_orchestration_creates_lanes(
        self, state_manager: StateManager, sample_findings: FindingsManager
    ) -> None:
        """Theme orchestration should create thematic lanes from findings."""
        from ut_analysis.skills.ut_theme_orchestrator.theme_orchestrator import (
            ThemeOrchestratorSkill,
        )

        orchestrator = ThemeOrchestratorSkill(state_manager)
        result = orchestrator.create_orchestration_plan("batch_001", "run_test", "proj_test")

        assert "thematic_lanes" in result
        lanes = result["thematic_lanes"]
        assert lanes

        for lane in lanes:
            assert "lane_id" in lane
            assert "lane_name" in lane
            assert "assigned_agent" in lane
            assert "finding_ids" in lane
            assert lane["finding_ids"]

    def test_orchestration_assigns_findings_to_relevant_lanes(
        self, state_manager: StateManager, sample_findings: FindingsManager
    ) -> None:
        """Findings should be routed to appropriate thematic lanes."""
        from ut_analysis.skills.ut_theme_orchestrator.theme_orchestrator import (
            ThemeOrchestratorSkill,
        )

        orchestrator = ThemeOrchestratorSkill(state_manager)
        result = orchestrator.create_orchestration_plan("batch_001", "run_test", "proj_test")

        lane_names = [lane["lane_name"] for lane in result["thematic_lanes"]]
        assert any("trust" in name.lower() for name in lane_names)


class TestThematicSpecialists:
    """Tests for thematic specialist agent outputs."""

    def test_specialist_output_has_required_fields(
        self, state_manager: StateManager
    ) -> None:
        """Specialist output should include all required theme fields."""
        from ut_analysis.skills.ut_pain_point_analyst.pain_point_analyst import (
            PainPointAnalystSkill,
        )

        analyst = PainPointAnalystSkill(state_manager)
        lane_data = {
            "lane_id": "pain_points",
            "lane_name": "Pain Points",
            "input_finding_ids": ["F_001", "F_004"],
            "findings": [
                {
                    "finding_id": "F_001",
                    "title": "Checkout frustration",
                    "description": "User frustrated by confusing checkout error messages",
                    "participant_id": "P001",
                    "task_id": "T1",
                    "verbatim_quote": "I don't understand this error",
                    "severity": 3,
                },
                {
                    "finding_id": "F_004",
                    "title": "Workflow abandoned",
                    "description": "User abandoned workflow stuck on configuration step",
                    "participant_id": "P003",
                    "task_id": "T1",
                    "verbatim_quote": "This is too complicated",
                    "severity": 4,
                },
            ],
        }

        result = analyst.analyze_lane(lane_data, "run_test")

        assert "themes" in result
        assert result["lane_id"] == "pain_points"
        assert result["agent_name"] == "pain-point-analyst"

        for theme in result["themes"]:
            assert "theme_id" in theme
            assert "theme_title" in theme
            assert "theme_summary" in theme
            assert "evidence_count" in theme
            assert "participant_count" in theme
            assert "confidence" in theme
            assert 0.0 <= theme["confidence"] <= 1.0


class TestEvalRubric:
    """Tests for evaluation rubric."""

    def test_eval_catches_missing_evidence(self, state_manager: StateManager) -> None:
        """Eval should flag artifacts with no evidence references."""
        from ut_analysis.skills.ut_eval_rubric.eval_rubric import EvalRubricSkill

        eval_skill = EvalRubricSkill(state_manager)
        bad_artifact = {
            "title": "All users hate this feature",
            "description": "Everyone always struggles with this",
            "confidence": 0.95,
            "participant_count": 1,
        }

        result = eval_skill.evaluate_artifact(bad_artifact, "TEST_001", "theme")

        assert result["pass_fail"] in ("fail", "warning")
        assert result["issues"]

    def test_eval_passes_well_formed_artifact(
        self, state_manager: StateManager
    ) -> None:
        """Eval should pass well-formed artifacts."""
        from ut_analysis.skills.ut_eval_rubric.eval_rubric import EvalRubricSkill

        eval_skill = EvalRubricSkill(state_manager)
        good_artifact = {
            "theme_id": "T_001",
            "theme_title": "Checkout confusion in step 3",
            "theme_summary": "3 participants encountered difficulty at checkout step 3",
            "evidence_count": 3,
            "participant_count": 3,
            "source_finding_ids": ["F_001", "F_002", "F_003"],
            "representative_quotes": ["Quote 1", "Quote 2"],
            "confidence": 0.7,
            "product_implication": "Redesign checkout step 3 flow",
            "contradictions_or_outliers": [],
        }

        result = eval_skill.evaluate_artifact(good_artifact, "TEST_002", "theme")
        assert result["pass_fail"] == "pass"

    def test_eval_catches_overclaiming(self, state_manager: StateManager) -> None:
        """Eval should flag overclaiming language."""
        from ut_analysis.skills.ut_eval_rubric.eval_rubric import EvalRubricSkill

        eval_skill = EvalRubricSkill(state_manager)
        overclaiming_artifact = {
            "title": "All users always fail here",
            "description": (
                "Everyone definitely struggles and it proves that the design is broken"
            ),
            "source_finding_ids": ["F_001"],
            "confidence": 0.5,
            "participant_count": 5,
        }

        result = eval_skill.evaluate_artifact(overclaiming_artifact, "TEST_003", "theme")
        assert any("overclaim" in issue.lower() for issue in result["issues"])

    def test_eval_creates_checkpoint_on_failure(
        self, state_manager: StateManager
    ) -> None:
        """Failed eval should create a human review checkpoint."""
        from ut_analysis.skills.ut_eval_rubric.eval_rubric import EvalRubricSkill

        eval_skill = EvalRubricSkill(state_manager)
        bad_artifact = {
            "title": "All users always definitely fail",
            "description": "Everyone certainly proves that this never works",
            "confidence": 0.99,
            "participant_count": 1,
        }

        result = eval_skill.evaluate_artifact(bad_artifact, "FAIL_001", "theme")
        assert result["created_human_review_checkpoint"] is True


class TestResearchGaps:
    """Tests for research gap finding."""

    def test_gaps_from_weak_themes(self, state_manager: StateManager) -> None:
        """Should identify gaps from weakly supported themes."""
        from ut_analysis.skills.ut_research_gap_finder.research_gap_finder import (
            ResearchGapFinderSkill,
        )

        gap_finder = ResearchGapFinderSkill(state_manager)
        themes = [
            {
                "consolidated_theme_id": "CT_001",
                "title": "Navigation confusion",
                "evidence_strength": "weak",
                "participant_count": 1,
                "product_implications": ["Improve navigation"],
                "open_questions": [],
            },
            {
                "consolidated_theme_id": "CT_002",
                "title": "Positive onboarding experience",
                "evidence_strength": "strong",
                "participant_count": 4,
                "product_implications": ["Keep current onboarding"],
                "open_questions": [],
            },
        ]

        result = gap_finder.find_gaps(
            consolidated_themes=themes,
            project_id="test",
            run_id="run_test",
        )

        gaps = result.get("gaps", [])
        assert gaps
        assert any("Navigation" in gap.get("gap_title", "") for gap in gaps)


class TestNextStudyPlanner:
    """Tests for next study planning."""

    def test_plans_generated_from_gaps(self, state_manager: StateManager) -> None:
        """Should generate study plans from research gaps."""
        from ut_analysis.skills.ut_next_study_planner.next_study_planner import (
            NextStudyPlannerSkill,
        )

        planner = NextStudyPlannerSkill(state_manager)
        gaps = [
            {
                "gap_id": "GAP_001",
                "gap_title": "Insufficient evidence for navigation confusion",
                "priority": "high",
                "suggested_method": "Follow-up usability sessions",
                "suggested_participant_segment": "New users",
                "decision_it_would_inform": "Whether to redesign navigation",
                "recommended_follow_up": "Test with more users",
            }
        ]

        result = planner.generate_plans(
            research_gaps=gaps,
            project_id="test",
            run_id="run_test",
        )

        plans = result.get("plans", [])
        assert plans
        assert "study_objective" in plans[0]
        assert "method_recommendation" in plans[0]
        assert "key_research_questions" in plans[0]


class TestPipelineRunSummary:
    """Tests for pipeline run summary."""

    def test_run_summary_generation(self, state_manager: StateManager) -> None:
        """Should generate a complete run summary."""
        from ut_analysis.skills.ut_run_summary.run_summary import RunSummarySkill

        summary_skill = RunSummarySkill(state_manager)
        result = summary_skill.generate_run_summary(
            run_id="test_run",
            project_id="test_project",
            stages_completed=["orchestration", "thematic_analysis"],
            artifacts_created=["plan.json", "analysis.json"],
            agents_invoked=["ut-theme-orchestrator", "ut-pain-point-analyst"],
            evals_passed=5,
            evals_failed=1,
            review_checkpoints_created=2,
            unresolved_issues=["Low confidence theme"],
        )

        assert result["run_id"] == "test_run"
        assert result["project_id"] == "test_project"
        assert len(result["stages_completed"]) == 2
        assert result["evals_failed"] == 1
        assert "next_suggested_action" in result
        assert (
            "failed" in result["next_suggested_action"].lower()
            or "eval" in result["next_suggested_action"].lower()
        )


class TestModelsValidation:
    """Tests that new models validate correctly."""

    def test_thematic_lane_model(self) -> None:
        """ThematicLane should validate."""
        lane = ThematicLane(
            lane_id="pain_points",
            lane_name="Pain Points",
            assigned_agent="ut-pain-point-analyst",
            finding_ids=["F_001", "F_002"],
            participant_ids=["P001", "P002"],
            task_ids=["T1"],
            rationale="Multiple findings indicate user frustration",
            expected_output_path="output/themes/pain_points_theme_analysis.md",
        )
        assert lane.lane_id == "pain_points"
        assert len(lane.finding_ids) == 2

    def test_theme_orchestration_plan_model(self) -> None:
        """ThemeOrchestrationPlan should validate."""
        plan = ThemeOrchestrationPlan(
            plan_id="run_001_theme_orchestration",
            findings_batch_id="batch_001",
            project_id="PROJ_001",
            run_id="run_001",
            total_findings=5,
        )
        assert plan.total_findings == 5

    def test_theme_result_and_lane_analysis_models(self) -> None:
        """ThemeResult and ThematicLaneAnalysis should validate."""
        theme = ThemeResult(
            theme_id="T_001",
            theme_title="Checkout Confusion",
            theme_summary="Users confused at checkout step 3",
            evidence_count=3,
            participant_count=3,
            confidence=0.7,
        )
        analysis = ThematicLaneAnalysis(
            lane_id="pain_points",
            lane_name="Pain Points",
            agent_name="pain-point-analyst",
            source_finding_ids=["F_001", "F_002"],
            themes=[theme],
        )
        assert analysis.themes[0].theme_title == "Checkout Confusion"

    def test_consolidated_theme_model(self) -> None:
        """ConsolidatedTheme should validate with bounds."""
        theme = ConsolidatedTheme(
            consolidated_theme_id="CT_001",
            title="Checkout Confusion",
            summary="Users confused at checkout step 3",
            contributing_lanes=["pain_points", "workflow_breakdowns"],
            evidence_strength="moderate",
            participant_count=3,
            confidence=0.7,
        )
        consolidation = ThemeConsolidation(
            consolidation_id="run_001_consolidation",
            project_id="PROJ_001",
            consolidated_themes=[theme],
        )
        assert consolidation.consolidated_themes[0].evidence_strength == "moderate"
        assert consolidation.consolidated_themes[0].confidence == 0.7

    def test_research_gap_model(self) -> None:
        """ResearchGap should validate."""
        gap = ResearchGap(
            gap_id="GAP_001",
            gap_title="Missing expert users",
            why_it_matters="Current sample excludes power users",
            priority="high",
            suggested_method="Expert interviews",
        )
        report = ResearchGapReport(project_id="PROJ_001", run_id="run_001", gaps=[gap])
        assert report.gaps[0].priority == "high"

    def test_eval_result_model(self) -> None:
        """EvalResult should validate."""
        result = EvalResult(
            artifact_id="A_001",
            artifact_type="theme",
            evaluator="ut-eval-rubric",
            scores=[RubricScore(dimension="specificity", score=1.0, passed=True)],
            pass_fail="pass",
        )
        assert result.pass_fail == "pass"

    def test_next_study_and_run_summary_models(self) -> None:
        """NextStudyPlan, PipelineRunSummary, and HumanReviewCheckpoint should validate."""
        plan = NextStudyPlan(
            plan_id="PLAN_001",
            study_objective="Investigate navigation confusion",
            method_recommendation="Follow-up usability study",
        )
        summary = PipelineRunSummary(
            run_id="RUN_001",
            project_id="PROJ_001",
            stages_completed=["extraction", "orchestration"],
            evals_passed=5,
            evals_failed=0,
        )
        checkpoint = HumanReviewCheckpoint(
            checkpoint_id="CP_001",
            stage="evaluation_rubric",
            reason="Evidence needs review",
            related_artifact_id="A_001",
            artifact_type="theme",
            severity="high",
            suggested_reviewer_action="Review evidence strength",
        )
        assert plan.plan_id == "PLAN_001"
        assert summary.run_id == "RUN_001"
        assert checkpoint.status == "pending"


class TestManagerPersistence:
    """Tests manager persistence for newly added artifact types."""

    def test_new_managers_round_trip(self, temp_project_dir: Path) -> None:
        """Persistence managers should save and load JSON payloads."""
        data_dir = temp_project_dir / "data"
        orchestration_mgr = ThemeOrchestrationManager(data_dir)
        thematic_mgr = ThematicAnalysisManager(data_dir)
        eval_mgr = EvalRubricManager(data_dir)
        gap_mgr = ResearchGapManager(data_dir)
        next_mgr = NextStudyManager(data_dir)
        run_mgr = PipelineRunManager(data_dir)
        review_mgr = ReviewCheckpointManager(data_dir)

        plan_data = {
            "plan_id": "run_001_theme_orchestration",
            "thematic_lanes": [{"lane_id": "pain_points", "finding_ids": ["F_001"]}],
        }
        orchestration_mgr.save_plan("run_001_theme_orchestration", plan_data)
        assert orchestration_mgr.load_plan("run_001_theme_orchestration") == plan_data

        lane_analysis = {
            "lane_id": "pain_points",
            "themes": [{"theme_id": "T_001", "theme_title": "Checkout confusion"}],
        }
        thematic_mgr.save_lane_analysis("pain_points", lane_analysis)
        assert thematic_mgr.load_lane_analysis("pain_points") == lane_analysis

        eval_data = {"run_id": "run_001", "passed": 1, "failed": 0, "warnings": 0}
        eval_mgr.save_eval_results("run_001", eval_data)
        assert eval_mgr.load_eval_results("run_001") == eval_data

        gap_data = {"run_id": "run_001", "gaps": [{"gap_id": "GAP_001"}]}
        gap_mgr.save_gaps("run_001", gap_data)
        assert gap_mgr.load_gaps("run_001") == gap_data

        next_study_data = {"run_id": "run_001", "plans": [{"plan_id": "PLAN_001"}]}
        next_mgr.save_plan("run_001", next_study_data)
        assert next_mgr.load_plan("run_001") == next_study_data

        run_data = {"run_id": "run_001", "next_suggested_action": "Share results."}
        run_mgr.save_run_summary("run_001", run_data)
        assert run_mgr.load_run_summary("run_001") == run_data

        checkpoint_data = {
            "checkpoints": [
                {
                    "checkpoint_id": "CP_001",
                    "stage": "evaluation_rubric",
                    "reason": "Needs human review.",
                    "related_artifact_id": "A_001",
                    "artifact_type": "theme",
                    "severity": "high",
                    "suggested_reviewer_action": "Review it.",
                    "status": "pending",
                }
            ]
        }
        review_mgr.save_checkpoints("eval_A_001", checkpoint_data)
        pending = review_mgr.get_pending_checkpoints()
        assert len(pending) == 1
        assert pending[0]["checkpoint_id"] == "CP_001"

        saved_file = (
            data_dir / "theme_orchestration" / "run_001_theme_orchestration_plan.json"
        )
        assert json.loads(saved_file.read_text())["plan_id"] == "run_001_theme_orchestration"


class TestHumanReviewCheckpointTriggers:
    """Tests that review checkpoints are created appropriately."""

    def test_checkpoint_created_for_low_confidence(
        self, state_manager: StateManager
    ) -> None:
        """Should create checkpoint when confidence is high but evidence is low."""
        from ut_analysis.skills.ut_eval_rubric.eval_rubric import EvalRubricSkill

        eval_skill = EvalRubricSkill(state_manager)
        artifact = {
            "title": "Definite pattern",
            "description": "Clear pattern observed in user behavior",
            "confidence": 0.95,
            "participant_count": 1,
            "source_finding_ids": ["F_001"],
            "verbatim_quote": "quote",
        }

        result = eval_skill.evaluate_artifact(artifact, "CONF_001", "theme")
        confidence_issues = [
            issue for issue in result["issues"] if "confidence" in issue.lower()
        ]
        assert confidence_issues
