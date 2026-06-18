"""MCP Server tools for state management and I/O operations."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)


class StateManager:
    """Manages project state and persistence."""

    def __init__(self, project_dir: Path) -> None:
        self.project_dir = Path(project_dir)
        self.project_dir.mkdir(exist_ok=True, parents=True)
        self.state_file = self.project_dir / "project_state.json"
        self.data_dir = self.project_dir / "data"
        self.data_dir.mkdir(exist_ok=True, parents=True)
        self.state: dict[str, Any] = self._load_state()

    def _load_state(self) -> dict[str, Any]:
        """Load project state from file."""
        if self.state_file.exists():
            try:
                with open(self.state_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load state: {e}")
        return {
            "project_id": None,
            "phase": "initialized",
            "transcripts": {},
            "findings": {},
            "evaluations": {},
            "severity_ratings": {},
            "heuristic_mappings": {},
            "synthesis": None,
            "reports": {},
            "created_at": datetime.utcnow().isoformat(),
        }

    def save_state(self) -> None:
        """Save project state to file."""
        with open(self.state_file, "w") as f:
            json.dump(self.state, f, indent=2, default=str)

    def get_state(self) -> dict[str, Any]:
        """Get current state."""
        return self.state

    def update_phase(self, phase: str) -> None:
        """Update pipeline phase."""
        self.state["phase"] = phase
        self.save_state()

    def add_transcript(self, transcript_id: str, metadata: dict[str, Any]) -> None:
        """Record transcript metadata."""
        self.state["transcripts"][transcript_id] = {
            **metadata,
            "added_at": datetime.utcnow().isoformat(),
        }
        self.save_state()

    def add_finding(self, finding_id: str, metadata: dict[str, Any]) -> None:
        """Record finding metadata."""
        self.state["findings"][finding_id] = {
            **metadata,
            "added_at": datetime.utcnow().isoformat(),
        }
        self.save_state()

    def save_json_file(self, filename: str, data: dict[str, Any]) -> Path:
        """Save JSON data to file."""
        filepath = self.data_dir / filename
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2, default=str)
        return filepath

    def load_json_file(self, filename: str) -> dict[str, Any]:
        """Load JSON data from file."""
        filepath = self.data_dir / filename
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        with open(filepath, "r") as f:
            return json.load(f)

    def get_pipeline_status(self) -> dict[str, Any]:
        """Get current pipeline status."""
        return {
            "phase": self.state["phase"],
            "transcripts_count": len(self.state["transcripts"]),
            "findings_count": len(self.state["findings"]),
            "evaluations_count": len(self.state["evaluations"]),
            "synthesis_complete": self.state["synthesis"] is not None,
            "reports_count": len(self.state["reports"]),
        }


class TranscriptManager:
    """Manages transcript parsing and storage."""

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True, parents=True)
        self.transcripts_dir = self.data_dir / "transcripts"
        self.transcripts_dir.mkdir(exist_ok=True, parents=True)

    def save_transcript(self, transcript_id: str, transcript_data: dict[str, Any]) -> Path:
        """Save parsed transcript to JSON file."""
        filepath = self.transcripts_dir / f"{transcript_id}.json"
        with open(filepath, "w") as f:
            json.dump(transcript_data, f, indent=2, default=str)
        logger.info(f"Saved transcript: {filepath}")
        return filepath

    def load_transcript(self, transcript_id: str) -> dict[str, Any]:
        """Load transcript from file."""
        filepath = self.transcripts_dir / f"{transcript_id}.json"
        if not filepath.exists():
            raise FileNotFoundError(f"Transcript not found: {transcript_id}")
        with open(filepath, "r") as f:
            return json.load(f)

    def list_transcripts(self) -> list[str]:
        """List all transcript IDs."""
        return [f.stem for f in self.transcripts_dir.glob("*.json")]


class NotesManager:
    """Manages observation notes storage."""

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True, parents=True)
        self.notes_dir = self.data_dir / "notes"
        self.notes_dir.mkdir(exist_ok=True, parents=True)

    def save_notes(self, session_id: str, notes_data: dict[str, Any]) -> Path:
        """Save parsed notes to JSON file."""
        filepath = self.notes_dir / f"{session_id}_notes.json"
        with open(filepath, "w") as f:
            json.dump(notes_data, f, indent=2, default=str)
        logger.info(f"Saved notes: {filepath}")
        return filepath

    def load_notes(self, session_id: str) -> dict[str, Any]:
        """Load notes from file."""
        filepath = self.notes_dir / f"{session_id}_notes.json"
        if not filepath.exists():
            raise FileNotFoundError(f"Notes not found: {session_id}")
        with open(filepath, "r") as f:
            return json.load(f)

    def list_notes(self) -> list[str]:
        """List all session note IDs."""
        return [f.stem.replace("_notes", "") for f in self.notes_dir.glob("*_notes.json")]


class FindingsManager:
    """Manages findings storage and retrieval."""

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True, parents=True)
        self.findings_dir = self.data_dir / "findings"
        self.findings_dir.mkdir(exist_ok=True, parents=True)

    def save_findings(self, findings_id: str, findings_data: dict[str, Any]) -> Path:
        """Save findings to JSON file."""
        filepath = self.findings_dir / f"{findings_id}_findings.json"
        with open(filepath, "w") as f:
            json.dump(findings_data, f, indent=2, default=str)
        logger.info(f"Saved findings: {filepath}")
        return filepath

    def load_findings(self, findings_id: str) -> dict[str, Any]:
        """Load findings from file."""
        filepath = self.findings_dir / f"{findings_id}_findings.json"
        if not filepath.exists():
            raise FileNotFoundError(f"Findings not found: {findings_id}")
        with open(filepath, "r") as f:
            return json.load(f)

    def list_findings(self) -> list[str]:
        """List all findings IDs."""
        return [f.stem.replace("_findings", "") for f in self.findings_dir.glob("*_findings.json")]


class EvaluationManager:
    """Manages evaluation results storage."""

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True, parents=True)
        self.eval_dir = self.data_dir / "evaluations"
        self.eval_dir.mkdir(exist_ok=True, parents=True)

    def save_evaluation(self, eval_id: str, eval_data: dict[str, Any]) -> Path:
        """Save evaluation results."""
        filepath = self.eval_dir / f"{eval_id}_eval.json"
        with open(filepath, "w") as f:
            json.dump(eval_data, f, indent=2, default=str)
        logger.info(f"Saved evaluation: {filepath}")
        return filepath

    def load_evaluation(self, eval_id: str) -> dict[str, Any]:
        """Load evaluation results."""
        filepath = self.eval_dir / f"{eval_id}_eval.json"
        if not filepath.exists():
            raise FileNotFoundError(f"Evaluation not found: {eval_id}")
        with open(filepath, "r") as f:
            return json.load(f)


class SynthesisManager:
    """Manages synthesis and report storage."""

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True, parents=True)
        self.synthesis_dir = self.data_dir / "synthesis"
        self.synthesis_dir.mkdir(exist_ok=True, parents=True)

    def save_synthesis(self, synthesis_id: str, synthesis_data: dict[str, Any]) -> Path:
        """Save synthesis results."""
        filepath = self.synthesis_dir / f"{synthesis_id}_synthesis.json"
        with open(filepath, "w") as f:
            json.dump(synthesis_data, f, indent=2, default=str)
        logger.info(f"Saved synthesis: {filepath}")
        return filepath

    def load_synthesis(self, synthesis_id: str) -> dict[str, Any]:
        """Load synthesis results."""
        filepath = self.synthesis_dir / f"{synthesis_id}_synthesis.json"
        if not filepath.exists():
            raise FileNotFoundError(f"Synthesis not found: {synthesis_id}")
        with open(filepath, "r") as f:
            return json.load(f)

    def save_report(
        self, report_id: str, report_type: str, report_data: dict[str, Any]
    ) -> Path:
        """Save generated report."""
        filepath = self.synthesis_dir / f"{report_id}_{report_type}_report.json"
        with open(filepath, "w") as f:
            json.dump(report_data, f, indent=2, default=str)
        logger.info(f"Saved report: {filepath}")
        return filepath

    def load_report(self, report_id: str, report_type: str) -> dict[str, Any]:
        """Load generated report."""
        filepath = self.synthesis_dir / f"{report_id}_{report_type}_report.json"
        if not filepath.exists():
            raise FileNotFoundError(f"Report not found: {report_id}_{report_type}")
        with open(filepath, "r") as f:
            return json.load(f)


class ClipManager:
    """Manages media clips storage and retrieval."""

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True, parents=True)
        self.clips_dir = self.data_dir / "clips"
        self.clips_dir.mkdir(exist_ok=True, parents=True)

    def save_clips(self, clip_batch_id: str, clips_data: dict[str, Any]) -> Path:
        """Save clips metadata to JSON file."""
        filepath = self.clips_dir / f"{clip_batch_id}_clips.json"
        with open(filepath, "w") as f:
            json.dump(clips_data, f, indent=2, default=str)
        logger.info(f"Saved clips: {filepath}")
        return filepath

    def load_clips(self, clip_batch_id: str) -> dict[str, Any]:
        """Load clips metadata from file."""
        filepath = self.clips_dir / f"{clip_batch_id}_clips.json"
        if not filepath.exists():
            raise FileNotFoundError(f"Clips not found: {clip_batch_id}")
        with open(filepath, "r") as f:
            return json.load(f)

    def list_clips(self) -> list[str]:
        """List all clip batch IDs."""
        return [f.stem.replace("_clips", "") for f in self.clips_dir.glob("*_clips.json")]


class RecommendationsManager:
    """Manages recommendations storage and retrieval."""

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True, parents=True)
        self.recommendations_dir = self.data_dir / "recommendations"
        self.recommendations_dir.mkdir(exist_ok=True, parents=True)

    def save_recommendations(self, recommendations_batch_id: str, recommendations_data: dict[str, Any]) -> Path:
        """Save recommendations to JSON file."""
        filepath = self.recommendations_dir / f"{recommendations_batch_id}_recommendations.json"
        with open(filepath, "w") as f:
            json.dump(recommendations_data, f, indent=2, default=str)
        logger.info(f"Saved recommendations: {filepath}")
        return filepath

    def load_recommendations(self, recommendations_batch_id: str) -> dict[str, Any]:
        """Load recommendations from file."""
        filepath = self.recommendations_dir / f"{recommendations_batch_id}_recommendations.json"
        if not filepath.exists():
            raise FileNotFoundError(f"Recommendations not found: {recommendations_batch_id}")
        with open(filepath, "r") as f:
            return json.load(f)

    def list_recommendations(self) -> list[str]:
        """List all recommendations batch IDs."""
        return [f.stem.replace("_recommendations", "") for f in self.recommendations_dir.glob("*_recommendations.json")]


class ContradictionsManager:
    """Manages contradiction analysis storage and retrieval."""

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True, parents=True)
        self.contradictions_dir = self.data_dir / "contradictions"
        self.contradictions_dir.mkdir(exist_ok=True, parents=True)

    def save_contradictions(self, contradictions_batch_id: str, contradictions_data: dict[str, Any]) -> Path:
        """Save contradictions analysis to JSON file."""
        filepath = self.contradictions_dir / f"{contradictions_batch_id}_contradictions.json"
        with open(filepath, "w") as f:
            json.dump(contradictions_data, f, indent=2, default=str)
        logger.info(f"Saved contradictions: {filepath}")
        return filepath

    def load_contradictions(self, contradictions_batch_id: str) -> dict[str, Any]:
        """Load contradictions analysis from file."""
        filepath = self.contradictions_dir / f"{contradictions_batch_id}_contradictions.json"
        if not filepath.exists():
            raise FileNotFoundError(f"Contradictions not found: {contradictions_batch_id}")
        with open(filepath, "r") as f:
            return json.load(f)

    def list_contradictions(self) -> list[str]:
        """List all contradictions batch IDs."""
        return [f.stem.replace("_contradictions", "") for f in self.contradictions_dir.glob("*_contradictions.json")]


class ReportManager:
    """Manages final report storage and retrieval."""

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True, parents=True)
        self.reports_dir = self.data_dir / "reports"
        self.reports_dir.mkdir(exist_ok=True, parents=True)

    def save_report_metadata(self, report_batch_id: str, report_data: dict[str, Any]) -> Path:
        """Save report metadata to JSON file."""
        filepath = self.reports_dir / f"{report_batch_id}_report_metadata.json"
        with open(filepath, "w") as f:
            json.dump(report_data, f, indent=2, default=str)
        logger.info(f"Saved report metadata: {filepath}")
        return filepath

    def load_report_metadata(self, report_batch_id: str) -> dict[str, Any]:
        """Load report metadata from file."""
        filepath = self.reports_dir / f"{report_batch_id}_report_metadata.json"
        if not filepath.exists():
            raise FileNotFoundError(f"Report metadata not found: {report_batch_id}")
        with open(filepath, "r") as f:
            return json.load(f)

    def list_reports(self) -> list[str]:
        """List all report batch IDs."""
        return [f.stem.replace("_report_metadata", "") for f in self.reports_dir.glob("*_report_metadata.json")]
