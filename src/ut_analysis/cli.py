"""CLI interface for UT Analysis Pipeline."""

import click
import logging
from pathlib import Path

from ut_analysis.skills.ut_controller.controller import ControllerSkill
from ut_analysis.skills.ut_ingestor.ingestor import IngestorSkill
from ut_analysis.skills.ut_extractor.extractor import ExtractorSkill
from ut_analysis.skills.ut_evaluator.evaluator import EvaluatorSkill
from ut_analysis.state_management import (
    StateManager,
    TranscriptManager,
    NotesManager,
    FindingsManager,
    EvaluationManager,
    ThemeOrchestrationManager,
    ThematicAnalysisManager,
    EvalRubricManager,
    ResearchGapManager,
    NextStudyManager,
    PipelineRunManager,
    ReviewCheckpointManager,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@click.group()
def main() -> None:
    """Usability test analysis pipeline CLI."""
    pass


@main.command()
@click.option("--config", required=True, help="Path to research_config.yaml")
@click.option("--project-dir", required=True, help="Project directory")
def init_project(config: str, project_dir: str) -> None:
    """Initialize analysis project."""
    controller = ControllerSkill()
    result = controller.init_pipeline(config, project_dir)

    if result["status"] == "success":
        click.echo(f"✓ Project initialized: {result['project_id']}")
        click.echo(f"  Participants: {result['participants_count']}")
        click.echo(f"  Tasks: {result['tasks_count']}")
        click.echo("\nNext steps:")
        for step in result["next_steps"]:
            click.echo(f"  • {step}")
    else:
        click.echo(f"✗ Error: {result.get('error')}")


@main.command()
@click.option("--file", required=True, help="Transcript file (.docx or .md)")
@click.option("--transcript-id", required=True, help="Transcript ID")
@click.option("--participant-id", required=True, help="Participant ID")
@click.option("--project-dir", required=True, help="Project directory")
def ingest_transcript(
    file: str, transcript_id: str, participant_id: str, project_dir: str
) -> None:
    """Ingest a transcript file."""
    state_mgr = StateManager(project_dir)
    transcript_mgr = TranscriptManager(Path(project_dir) / "data")
    ingestor = IngestorSkill(state_mgr, transcript_mgr)

    result = ingestor.load_transcript(transcript_id, file, participant_id)

    if result["status"] == "success":
        click.echo(f"✓ Transcript ingested: {result['transcript_id']}")
        click.echo(f"  Turns: {result['turns_count']}")
    else:
        click.echo(f"✗ Error: {result.get('error')}")


@main.command()
@click.option("--file", required=True, help="Notes file (.md)")
@click.option("--session-id", required=True, help="Session ID")
@click.option("--participant-id", required=True, help="Participant ID")
@click.option("--project-dir", required=True, help="Project directory")
def ingest_notes(
    file: str, session_id: str, participant_id: str, project_dir: str
) -> None:
    """Ingest observation notes."""
    state_mgr = StateManager(project_dir)
    notes_mgr = NotesManager(Path(project_dir) / "data")
    ingestor = IngestorSkill(state_mgr, notes_manager=notes_mgr)

    result = ingestor.load_notes(session_id, file, participant_id)

    if result["status"] == "success":
        click.echo(f"✓ Notes ingested: {result['session_id']}")
        click.echo(f"  Observations: {result['notes_count']}")
    else:
        click.echo(f"✗ Error: {result.get('error')}")


@main.command()
@click.option("--project-dir", required=True, help="Project directory")
def status(project_dir: str) -> None:
    """Show pipeline status."""
    controller = ControllerSkill(StateManager(project_dir))
    status = controller.get_status()
    metrics = controller.get_metrics()

    click.echo(f"Project: {status.get('project_id')}")
    click.echo(f"Phase: {status.get('phase')}")
    click.echo("\nMetrics:")
    for key, value in metrics.items():
        click.echo(f"  {key}: {value}")


@main.command()
@click.option("--project-dir", required=True, help="Project directory")
@click.option("--batch-id", default="batch_001", help="Extraction batch ID")
def extract(project_dir: str, batch_id: str) -> None:
    """Extract findings from all ingested transcripts."""
    import yaml

    state_mgr = StateManager(project_dir)
    transcript_mgr = TranscriptManager(Path(project_dir) / "data")
    findings_mgr = FindingsManager(Path(project_dir) / "data")
    extractor = ExtractorSkill(state_mgr, transcript_mgr, findings_manager=findings_mgr)

    # Load project config for task definitions
    config_path = Path("research_config.yaml")
    project_config = None
    if config_path.exists():
        with open(config_path, "r") as f:
            project_config = yaml.safe_load(f)

    # Get all transcript IDs
    transcript_ids = transcript_mgr.list_transcripts()
    if not transcript_ids:
        click.echo("No transcripts found. Ingest transcripts first.")
        return

    click.echo(f"Extracting findings from {len(transcript_ids)} transcripts...")

    result = extractor.extract_findings(
        transcript_ids=transcript_ids,
        project_config=project_config,
        batch_id=batch_id,
    )

    if "error" in result:
        click.echo(f"Error: {result['error']}")
    else:
        stats = result.get("extraction_stats", {})
        click.echo(f"Extracted {stats.get('total_findings', 0)} findings")
        click.echo(f"  Categories: {stats.get('by_category', {})}")
        click.echo(f"  Avg confidence: {stats.get('average_confidence', 0)}")
        click.echo(f"  Task completion rate: {stats.get('task_completion_rate', 0)}")


@main.command()
@click.option("--project-dir", required=True, help="Project directory")
@click.option("--findings-batch", default="batch_ai_001", help="Findings batch ID to evaluate")
@click.option("--eval-batch-id", default="eval_001", help="Evaluation batch ID")
def evaluate(project_dir: str, findings_batch: str, eval_batch_id: str) -> None:
    """Evaluate findings using 5-check verification."""
    state_mgr = StateManager(project_dir)
    transcript_mgr = TranscriptManager(Path(project_dir) / "data")
    findings_mgr = FindingsManager(Path(project_dir) / "data")
    eval_mgr = EvaluationManager(Path(project_dir) / "data")
    evaluator = EvaluatorSkill(state_mgr, transcript_mgr, findings_mgr, eval_mgr)

    # Get all transcript IDs
    transcript_ids = transcript_mgr.list_transcripts()

    click.echo(f"Evaluating findings batch '{findings_batch}'...")

    result = evaluator.evaluate_findings(
        findings_batch_id=findings_batch,
        transcript_ids=transcript_ids,
        evaluation_batch_id=eval_batch_id,
    )

    if "error" in result:
        click.echo(f"Error: {result['error']}")
    else:
        stats = result.get("evaluation_stats", {})
        click.echo(f"Evaluated {stats.get('total_findings', 0)} findings")
        click.echo(f"  Passed all checks: {stats.get('passed_all_checks', 0)}")
        click.echo(f"  Failed: {stats.get('failed_checks', 0)}")
        click.echo(f"  Needs revision: {stats.get('needs_revision', 0)}")
        click.echo(f"  Avg checks passed: {stats.get('average_checks_passed', 0)}/5")
        if stats.get("by_failure_reason"):
            click.echo(f"  Failure reasons: {stats['by_failure_reason']}")


@main.command()
@click.option("--project-dir", required=True, help="Project directory")
@click.option("--findings-batch", default="batch_001", help="Findings batch ID")
@click.option("--run-id", default="run_001", help="Run ID")
def orchestrate_themes(project_dir: str, findings_batch: str, run_id: str) -> None:
    """Run thematic orchestration to route findings to specialist lanes."""
    from ut_analysis.skills.ut_theme_orchestrator.theme_orchestrator import (
        ThemeOrchestratorSkill,
    )

    state_mgr = StateManager(project_dir)
    orchestrator = ThemeOrchestratorSkill(state_mgr)

    state = state_mgr.get_state()
    project_id = state.get("project_id", "unknown")

    result = orchestrator.create_orchestration_plan(findings_batch, run_id, project_id)

    if "error" in result:
        click.echo(f"✗ Error: {result['error']}")
    else:
        lanes = result.get("thematic_lanes", [])
        click.echo(f"✓ Theme orchestration complete: {len(lanes)} lanes created")
        for lane in lanes:
            finding_ids = lane.get("input_finding_ids", lane.get("finding_ids", []))
            click.echo(
                f"  • {lane['lane_name']} → {lane['assigned_agent']} "
                f"({len(finding_ids)} findings)"
            )


@main.command()
@click.option("--project-dir", required=True, help="Project directory")
@click.option("--run-id", default="run_001", help="Run ID")
def run_theme_agents(project_dir: str, run_id: str) -> None:
    """Run parallel thematic specialist agents on orchestrated lanes."""
    from ut_analysis.skills.ut_pain_point_analyst.pain_point_analyst import (
        PainPointAnalystSkill,
    )
    from ut_analysis.skills.ut_needs_analyst.needs_analyst import NeedsAnalystSkill
    from ut_analysis.skills.ut_behavior_analyst.behavior_analyst import (
        BehaviorAnalystSkill,
    )
    from ut_analysis.skills.ut_mental_model_analyst.mental_model_analyst import (
        MentalModelAnalystSkill,
    )
    from ut_analysis.skills.ut_trust_analyst.trust_analyst import TrustAnalystSkill
    from ut_analysis.skills.ut_workflow_analyst.workflow_analyst import (
        WorkflowAnalystSkill,
    )

    state_mgr = StateManager(project_dir)
    orch_mgr = ThemeOrchestrationManager(Path(project_dir) / "data")

    try:
        try:
            plan = orch_mgr.load_plan(run_id)
        except FileNotFoundError:
            plan = orch_mgr.load_plan(f"{run_id}_theme_orchestration")
    except FileNotFoundError:
        click.echo("✗ No orchestration plan found. Run orchestrate-themes first.")
        return

    agent_map = {
        "ut-pain-point-analyst": PainPointAnalystSkill(state_mgr),
        "ut-needs-analyst": NeedsAnalystSkill(state_mgr),
        "ut-behavior-analyst": BehaviorAnalystSkill(state_mgr),
        "ut-mental-model-analyst": MentalModelAnalystSkill(state_mgr),
        "ut-trust-analyst": TrustAnalystSkill(state_mgr),
        "ut-workflow-analyst": WorkflowAnalystSkill(state_mgr),
    }

    findings_mgr = FindingsManager(Path(project_dir) / "data")
    lanes = plan.get("thematic_lanes", [])

    click.echo(f"Running {len(lanes)} thematic specialist agents...")
    for lane in lanes:
        agent_name = lane.get("assigned_agent", "")
        agent = agent_map.get(agent_name)
        if agent is None:
            click.echo(f"  ⚠ No agent found for: {agent_name}")
            continue

        input_finding_ids = lane.get("input_finding_ids", lane.get("finding_ids", []))
        lane_data = {
            "lane_id": lane["lane_id"],
            "lane_name": lane["lane_name"],
            "input_finding_ids": input_finding_ids,
            "findings": _load_findings_for_lane(findings_mgr, input_finding_ids),
        }

        result = agent.analyze_lane(lane_data, run_id)
        themes_count = len(result.get("themes", []))
        click.echo(f"  ✓ {lane['lane_name']}: {themes_count} themes identified")


def _load_findings_for_lane(
    findings_mgr: FindingsManager, finding_ids: list[str]
) -> list[dict]:
    """Load findings matching the given IDs from all available batches."""
    all_findings = []
    for batch_id in findings_mgr.list_findings():
        try:
            batch = findings_mgr.load_findings(batch_id)
            for finding in batch.get("findings", []):
                if finding.get("finding_id") in finding_ids:
                    all_findings.append(finding)
        except Exception:
            pass
    return all_findings


@main.command()
@click.option("--project-dir", required=True, help="Project directory")
@click.option("--run-id", default="run_001", help="Run ID")
def consolidate_themes(project_dir: str, run_id: str) -> None:
    """Consolidate themes from parallel specialist agents."""
    from ut_analysis.skills.ut_theme_consolidator.theme_consolidator import (
        ThemeConsolidatorSkill,
    )

    state_mgr = StateManager(project_dir)
    thematic_mgr = ThematicAnalysisManager(Path(project_dir) / "data")
    consolidator = ThemeConsolidatorSkill(state_mgr, thematic_mgr)

    lane_ids = thematic_mgr.list_lane_analyses()
    if not lane_ids:
        click.echo("✗ No lane analyses found. Run run-theme-agents first.")
        return

    lane_analyses = [thematic_mgr.load_lane_analysis(lid) for lid in lane_ids]
    state = state_mgr.get_state()
    project_id = state.get("project_id", "unknown")

    result = consolidator.consolidate_themes(
        lane_analyses, project_id, f"{run_id}_consolidation"
    )

    themes = result.get("consolidated_themes", [])
    click.echo(f"✓ Consolidated {len(themes)} themes from {len(lane_analyses)} lanes")
    for theme in themes[:5]:
        click.echo(f"  • [{theme['evidence_strength']}] {theme['title']}")


@main.command()
@click.option("--project-dir", required=True, help="Project directory")
@click.option("--run-id", default="run_001", help="Run ID")
def find_research_gaps(project_dir: str, run_id: str) -> None:
    """Identify research gaps from consolidated themes."""
    from ut_analysis.skills.ut_research_gap_finder.research_gap_finder import (
        ResearchGapFinderSkill,
    )

    state_mgr = StateManager(project_dir)
    thematic_mgr = ThematicAnalysisManager(Path(project_dir) / "data")
    gap_finder = ResearchGapFinderSkill(state_mgr)

    consolidation_id = f"{run_id}_consolidation"
    try:
        consolidation = thematic_mgr.load_consolidation(consolidation_id)
    except FileNotFoundError:
        click.echo("✗ No consolidation found. Run consolidate-themes first.")
        return

    themes = consolidation.get("consolidated_themes", [])
    state = state_mgr.get_state()
    project_id = state.get("project_id", "unknown")
    study_config = state.get("config", {})

    result = gap_finder.find_gaps(
        consolidated_themes=themes,
        study_config=study_config,
        project_id=project_id,
        run_id=run_id,
    )

    gaps = result.get("gaps", [])
    click.echo(f"✓ Identified {len(gaps)} research gaps")
    for gap in gaps[:5]:
        click.echo(f"  • [{gap['priority']}] {gap['gap_title'][:60]}")


@main.command()
@click.option("--project-dir", required=True, help="Project directory")
@click.option("--run-id", default="run_001", help="Run ID")
def plan_next_study(project_dir: str, run_id: str) -> None:
    """Generate next-study recommendations from research gaps."""
    from ut_analysis.skills.ut_next_study_planner.next_study_planner import (
        NextStudyPlannerSkill,
    )

    state_mgr = StateManager(project_dir)
    gap_mgr = ResearchGapManager(Path(project_dir) / "data")
    planner = NextStudyPlannerSkill(state_mgr)

    try:
        gap_data = gap_mgr.load_gaps(run_id)
    except FileNotFoundError:
        click.echo("✗ No research gaps found. Run find-research-gaps first.")
        return

    gaps = gap_data.get("gaps", [])
    state = state_mgr.get_state()
    project_id = state.get("project_id", "unknown")

    result = planner.generate_plans(
        research_gaps=gaps,
        study_config=state.get("config", {}),
        project_id=project_id,
        run_id=run_id,
    )

    plans = result.get("plans", [])
    click.echo(f"✓ Generated {len(plans)} next-study recommendations")
    for plan in plans:
        click.echo(f"  • [{plan['priority']}] {plan['study_objective'][:60]}")


@main.command()
@click.option("--project-dir", required=True, help="Project directory")
@click.option("--run-id", default="run_001", help="Run ID")
def run_evals(project_dir: str, run_id: str) -> None:
    """Run evaluation rubric checks on pipeline artifacts."""
    from ut_analysis.skills.ut_eval_rubric.eval_rubric import EvalRubricSkill

    state_mgr = StateManager(project_dir)
    thematic_mgr = ThematicAnalysisManager(Path(project_dir) / "data")
    eval_skill = EvalRubricSkill(state_mgr)

    artifacts = []

    consolidation_id = f"{run_id}_consolidation"
    try:
        consolidation = thematic_mgr.load_consolidation(consolidation_id)
        for theme in consolidation.get("consolidated_themes", []):
            artifacts.append(
                {
                    "artifact_id": theme.get("consolidated_theme_id", "unknown"),
                    "artifact_type": "consolidated_theme",
                    "data": theme,
                }
            )
    except FileNotFoundError:
        pass

    for lane_id in thematic_mgr.list_lane_analyses():
        try:
            lane = thematic_mgr.load_lane_analysis(lane_id)
            for theme in lane.get("themes", []):
                artifacts.append(
                    {
                        "artifact_id": theme.get("theme_id", lane_id),
                        "artifact_type": "theme",
                        "data": theme,
                    }
                )
        except FileNotFoundError:
            pass

    if not artifacts:
        click.echo("✗ No artifacts found to evaluate.")
        return

    result = eval_skill.evaluate_batch(artifacts, run_id)

    click.echo(f"✓ Evaluated {result.get('total_artifacts_evaluated', 0)} artifacts")
    click.echo(f"  Passed: {result.get('passed', 0)}")
    click.echo(f"  Warnings: {result.get('warnings', 0)}")
    click.echo(f"  Failed: {result.get('failed', 0)}")


@main.command()
@click.option("--project-dir", required=True, help="Project directory")
def list_review_checkpoints(project_dir: str) -> None:
    """List pending human review checkpoints."""
    review_mgr = ReviewCheckpointManager(Path(project_dir) / "data")
    pending = review_mgr.get_pending_checkpoints()

    if not pending:
        click.echo("✓ No pending review checkpoints.")
        return

    click.echo(f"⚠ {len(pending)} pending review checkpoint(s):")
    for cp in pending:
        click.echo(
            f"  • [{cp.get('severity', '?')}] {cp.get('checkpoint_id', '?')}: "
            f"{cp.get('reason', '')[:60]}"
        )


@main.command()
@click.option("--project-dir", required=True, help="Project directory")
@click.option("--run-id", default="run_001", help="Run ID")
def run_summary(project_dir: str, run_id: str) -> None:
    """Generate pipeline run summary for observability."""
    from ut_analysis.skills.ut_run_summary.run_summary import RunSummarySkill

    state_mgr = StateManager(project_dir)
    state = state_mgr.get_state()
    project_id = state.get("project_id", "unknown")

    review_mgr = ReviewCheckpointManager(Path(project_dir) / "data")
    pending = review_mgr.get_pending_checkpoints()

    eval_mgr = EvalRubricManager(Path(project_dir) / "data")
    evals_passed = 0
    evals_failed = 0
    try:
        eval_data = eval_mgr.load_eval_results(run_id)
        evals_passed = eval_data.get("passed", 0)
        evals_failed = eval_data.get("failed", 0)
    except FileNotFoundError:
        pass

    orch_mgr = ThemeOrchestrationManager(Path(project_dir) / "data")
    thematic_mgr = ThematicAnalysisManager(Path(project_dir) / "data")

    stages = []
    artifacts = []
    agents = []

    if orch_mgr.list_plans():
        stages.append("theme_orchestration")
        artifacts.append("theme_orchestration_plan.json")
        agents.append("ut-theme-orchestrator")

    lane_ids = thematic_mgr.list_lane_analyses()
    if lane_ids:
        stages.append("thematic_analysis")
        for lid in lane_ids:
            artifacts.append(f"{lid}_theme_analysis.json")
        agents.extend(
            [
                "ut-pain-point-analyst",
                "ut-needs-analyst",
                "ut-behavior-analyst",
                "ut-mental-model-analyst",
                "ut-trust-analyst",
                "ut-workflow-analyst",
            ]
        )

    try:
        thematic_mgr.load_consolidation(f"{run_id}_consolidation")
        stages.append("theme_consolidation")
        artifacts.append("theme_consolidation.json")
        agents.append("ut-theme-consolidator")
    except FileNotFoundError:
        pass

    gap_mgr = ResearchGapManager(Path(project_dir) / "data")
    if gap_mgr.list_gaps():
        stages.append("research_gap_analysis")
        artifacts.append("research_gaps.json")
        agents.append("ut-research-gap-finder")

    next_mgr = NextStudyManager(Path(project_dir) / "data")
    if next_mgr.list_plans():
        stages.append("next_study_planning")
        artifacts.append("next_study_plan.json")
        agents.append("ut-next-study-planner")

    run_mgr = PipelineRunManager(Path(project_dir) / "data")
    summary_skill = RunSummarySkill(state_mgr, run_mgr)
    result = summary_skill.generate_run_summary(
        run_id=run_id,
        project_id=project_id,
        stages_completed=stages,
        artifacts_created=artifacts,
        agents_invoked=list(set(agents)),
        evals_passed=evals_passed,
        evals_failed=evals_failed,
        review_checkpoints_created=len(pending),
        unresolved_issues=[cp.get("reason", "") for cp in pending[:3]],
    )

    click.echo(f"✓ Run summary generated: {run_id}")
    click.echo(f"  Stages: {len(stages)}")
    click.echo(f"  Artifacts: {len(artifacts)}")
    click.echo(f"  Next: {result.get('next_suggested_action', 'N/A')[:60]}")


if __name__ == "__main__":
    main()
