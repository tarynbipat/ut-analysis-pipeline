"""Controller skill implementation for pipeline orchestration."""

import yaml
import logging
from pathlib import Path
from typing import Any
from datetime import datetime

from ut_analysis.models import ProjectConfig, PipelineStatus
from ut_analysis.state_management import StateManager

logger = logging.getLogger(__name__)


class ControllerSkill:
    """Orchestrates the usability test analysis pipeline."""

    def __init__(self, state_manager: StateManager | None = None) -> None:
        self.state_manager = state_manager

    def init_pipeline(self, config_file: str, project_dir: str) -> dict[str, Any]:
        """Initialize the analysis pipeline from configuration."""
        try:
            config_path = Path(config_file)
            if not config_path.exists():
                raise FileNotFoundError(f"Config file not found: {config_file}")

            # Load configuration
            with open(config_path, "r") as f:
                config_data = yaml.safe_load(f)

            # Validate configuration
            self._validate_config(config_data)

            # Initialize state manager if not provided
            if self.state_manager is None:
                self.state_manager = StateManager(project_dir)

            # Store project metadata
            self.state_manager.state["project_id"] = config_data.get("project_id")
            self.state_manager.state["project_name"] = config_data.get("project_name")
            self.state_manager.state["config"] = config_data
            self.state_manager.state["phase"] = "initialized"
            self.state_manager.save_state()

            logger.info(f"Pipeline initialized: {config_data.get('project_id')}")

            return {
                "status": "success",
                "phase": "initialized",
                "project_id": config_data.get("project_id"),
                "participants_count": len(config_data.get("participants", [])),
                "tasks_count": len(config_data.get("tasks", [])),
                "next_steps": ["Load transcripts using ut-ingestor", "Load observation notes"],
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Pipeline initialization failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    def _validate_config(self, config: dict[str, Any]) -> None:
        """Validate configuration structure."""
        required_fields = ["project_id", "project_name", "participants", "tasks"]

        for field in required_fields:
            if field not in config:
                raise ValueError(f"Missing required config field: {field}")

        # Validate participants
        participants = config.get("participants", [])
        if not participants:
            raise ValueError("At least one participant is required")

        seen_ids = set()
        for p in participants:
            if "id" not in p:
                raise ValueError("Each participant must have an 'id'")
            if p["id"] in seen_ids:
                raise ValueError(f"Duplicate participant ID: {p['id']}")
            seen_ids.add(p["id"])

        # Validate tasks
        tasks = config.get("tasks", [])
        if not tasks:
            raise ValueError("At least one task is required")

        for task in tasks:
            if "id" not in task or "name" not in task:
                raise ValueError("Each task must have 'id' and 'name'")
            if "success_criteria" not in task:
                raise ValueError(f"Task {task['id']} must have 'success_criteria'")
            if "time_limit_seconds" not in task:
                raise ValueError(f"Task {task['id']} must have 'time_limit_seconds'")

    def get_status(self) -> dict[str, Any]:
        """Get current pipeline status."""
        if self.state_manager is None:
            return {"error": "State manager not initialized"}

        state = self.state_manager.get_state()
        status = self.state_manager.get_pipeline_status()

        return {
            "project_id": state.get("project_id"),
            "phase": state.get("phase"),
            "progress": status,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def advance_phase(self, next_phase: str) -> dict[str, Any]:
        """Advance to next pipeline phase with validation."""
        if self.state_manager is None:
            return {"error": "State manager not initialized"}

        current_state = self.state_manager.get_state()
        current_phase = current_state.get("phase")

        # Define valid transitions
        valid_transitions = {
            "initialized": ["ingestion_complete"],
            "ingestion_complete": ["extraction_complete"],
            "extraction_complete": ["evaluation_complete"],
            "evaluation_complete": ["severity_rating_complete"],
            "severity_rating_complete": ["heuristic_mapping_complete"],
            "heuristic_mapping_complete": ["synthesis_complete"],
            "synthesis_complete": ["critique_complete", "reporting_complete"],
            "critique_complete": ["reconciliation_complete", "reporting_complete"],
            "reconciliation_complete": ["reporting_complete"],
        }

        # Validate transition
        if current_phase not in valid_transitions:
            return {"error": f"Unknown phase: {current_phase}"}

        if next_phase not in valid_transitions.get(current_phase, []):
            return {"error": f"Invalid transition: {current_phase} -> {next_phase}"}

        # Check prerequisites
        prereq_errors = self._check_prerequisites(next_phase, current_state)
        if prereq_errors:
            return {
                "error": "Prerequisites not met",
                "details": prereq_errors,
                "current_phase": current_phase,
            }

        # Transition
        self.state_manager.update_phase(next_phase)

        logger.info(f"Phase advanced: {current_phase} -> {next_phase}")

        return {
            "status": "success",
            "previous_phase": current_phase,
            "current_phase": next_phase,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def _check_prerequisites(self, next_phase: str, state: dict[str, Any]) -> list[str]:
        """Check that prerequisites are met for phase transition."""
        errors = []

        if next_phase == "extraction_complete":
            transcripts_count = len(state.get("transcripts", {}))
            if transcripts_count == 0:
                errors.append("No transcripts loaded")

        elif next_phase == "evaluation_complete":
            findings_count = len(state.get("findings", {}))
            if findings_count == 0:
                errors.append("No findings extracted")

        elif next_phase == "synthesis_complete":
            config = state.get("config", {})
            participant_count = len(config.get("participants", []))
            # Require data from at least N-1 participants
            if participant_count > 1:
                min_required = participant_count - 1
                # This would need to be tracked in state
                # For now, just ensure we have some findings
                if len(state.get("findings", {})) < 3:
                    errors.append(
                        f"Need findings from at least {min_required} participants for synthesis"
                    )

        elif next_phase == "reporting_complete":
            if state.get("synthesis") is None:
                errors.append("Synthesis must be completed before reporting")

        return errors

    def get_project_config(self) -> dict[str, Any]:
        """Get loaded project configuration."""
        if self.state_manager is None:
            return {"error": "State manager not initialized"}

        state = self.state_manager.get_state()
        return state.get("config", {})

    def get_metrics(self) -> dict[str, Any]:
        """Get current pipeline metrics."""
        if self.state_manager is None:
            return {"error": "State manager not initialized"}

        state = self.state_manager.get_state()

        return {
            "transcripts_loaded": len(state.get("transcripts", {})),
            "notes_loaded": len(state.get("notes", {})),
            "findings_extracted": len(state.get("findings", {})),
            "findings_evaluated": len(state.get("evaluations", {})),
            "severity_ratings_complete": len(state.get("severity_ratings", {})),
            "heuristic_mappings_complete": len(state.get("heuristic_mappings", {})),
            "synthesis_complete": state.get("synthesis") is not None,
            "reports_generated": len(state.get("reports", {})),
        }
