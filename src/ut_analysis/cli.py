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


if __name__ == "__main__":
    main()
