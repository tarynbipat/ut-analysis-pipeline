"""Ingestor skill implementation for data ingestion and parsing."""

import logging
from pathlib import Path
from datetime import datetime
from typing import Any, Optional
import re
from docx import Document
import markdown as md_lib

from ut_analysis.models import Transcript, TranscriptTurn, ObservationNote
from ut_analysis.state_management import StateManager, TranscriptManager, NotesManager

logger = logging.getLogger(__name__)


class IngestorSkill:
    """Ingests and parses transcripts and notes from multiple sources."""

    # Timestamp regex patterns
    ISO_TIMESTAMP_PATTERN = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"
    MM_SS_PATTERN = r"(\d{1,2}):(\d{2})"

    def __init__(
        self,
        state_manager: StateManager,
        transcript_manager: TranscriptManager | None = None,
        notes_manager: NotesManager | None = None,
    ) -> None:
        self.state_manager = state_manager
        self.transcript_manager = transcript_manager or TranscriptManager(
            state_manager.project_dir / "data"
        )
        self.notes_manager = notes_manager or NotesManager(state_manager.project_dir / "data")
        self.task_definitions: dict[str, dict[str, Any]] = {}

    def load_config_tasks(self, config_data: dict[str, Any]) -> None:
        """Load task definitions from project config."""
        for task in config_data.get("tasks", []):
            self.task_definitions[task["id"]] = task
            if "name" in task:
                self.task_definitions[task["name"]] = task

    def load_transcript(
        self,
        transcript_id: str,
        file_path: str,
        participant_id: str,
        session_date: Optional[str] = None,
    ) -> dict[str, Any]:
        """Load and parse transcript from file."""
        try:
            file_path_obj = Path(file_path)

            if not file_path_obj.exists():
                raise FileNotFoundError(f"Transcript file not found: {file_path}")

            # Determine format and parse
            if file_path_obj.suffix.lower() == ".docx":
                turns = self._parse_docx(file_path)
            elif file_path_obj.suffix.lower() == ".md":
                turns = self._parse_markdown(file_path)
            else:
                raise ValueError(f"Unsupported format: {file_path_obj.suffix}")

            # Create transcript object
            session_dt = datetime.fromisoformat(session_date) if session_date else datetime.utcnow()

            transcript_data = {
                "transcript_id": transcript_id,
                "participant_id": participant_id,
                "session_date": session_dt.isoformat(),
                "turns": [turn.model_dump() for turn in turns],
                "source_file": str(file_path),
                "duration_seconds": self._calculate_duration(turns),
                "metadata": {"format": file_path_obj.suffix.lower()},
            }

            # Save transcript
            self.transcript_manager.save_transcript(transcript_id, transcript_data)

            # Update state
            self.state_manager.add_transcript(
                transcript_id,
                {
                    "participant_id": participant_id,
                    "turns_count": len(turns),
                    "file": file_path,
                },
            )

            logger.info(f"Loaded transcript {transcript_id}: {len(turns)} turns")

            return {
                "status": "success",
                "transcript_id": transcript_id,
                "turns_count": len(turns),
                "participant_id": participant_id,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to load transcript: {e}")
            return {"status": "error", "error": str(e)}

    def _parse_docx(self, file_path: str) -> list[TranscriptTurn]:
        """Parse DOCX transcript file."""
        doc = Document(file_path)
        turns: list[TranscriptTurn] = []
        turn_counter = 1

        # Pattern: "Speaker: [timestamp] [task-id?]"
        speaker_pattern = r"^(.+?):\s*\[?([0-9:]+|[\d-]+T[\d:]+Z)\]?\s*(?:\[(.+?)\])?"

        current_turn_lines: list[str] = []
        current_speaker = None
        current_timestamp = None
        current_task_id = None

        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue

            match = re.match(speaker_pattern, text)
            if match:
                # Save previous turn if any
                if current_speaker and current_turn_lines:
                    utterance = " ".join(current_turn_lines).strip('"').strip()
                    turns.append(
                        TranscriptTurn(
                            turn_id=f"turn_{turn_counter:03d}",
                            speaker=current_speaker,
                            timestamp=current_timestamp or "unknown",
                            utterance=utterance,
                            task_id=current_task_id,
                        )
                    )
                    turn_counter += 1
                    current_turn_lines = []

                # Parse new turn header
                current_speaker = match.group(1).strip()
                current_timestamp = match.group(2).strip()
                current_task_id = match.group(3).strip() if match.group(3) else None

                # Remaining text on same line is start of utterance
                remainder = text[match.end() :].strip('"').strip()
                if remainder:
                    current_turn_lines.append(remainder)
            else:
                # Continuation of current turn
                if current_speaker:
                    current_turn_lines.append(text.strip('"').strip())

        # Save last turn
        if current_speaker and current_turn_lines:
            utterance = " ".join(current_turn_lines).strip('"').strip()
            turns.append(
                TranscriptTurn(
                    turn_id=f"turn_{turn_counter:03d}",
                    speaker=current_speaker,
                    timestamp=current_timestamp or "unknown",
                    utterance=utterance,
                    task_id=current_task_id,
                )
            )

        return turns

    def _parse_markdown(self, file_path: str) -> list[TranscriptTurn]:
        """Parse markdown transcript file."""
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        turns: list[TranscriptTurn] = []
        turn_counter = 1

        # Pattern: "## [Timestamp] - [Speaker] - [Task ID?]"
        turn_pattern = r"^##\s*\[(.+?)\]\s*-\s*(.+?)\s*(?:-\s*(.+?))?\s*$"

        lines = content.split("\n")
        current_turn_lines: list[str] = []
        current_speaker = None
        current_timestamp = None
        current_task_id = None

        for line in lines:
            match = re.match(turn_pattern, line)
            if match:
                # Save previous turn
                if current_speaker and current_turn_lines:
                    utterance = "\n".join(current_turn_lines).strip()
                    turns.append(
                        TranscriptTurn(
                            turn_id=f"turn_{turn_counter:03d}",
                            speaker=current_speaker,
                            timestamp=current_timestamp or "unknown",
                            utterance=utterance,
                            task_id=current_task_id,
                        )
                    )
                    turn_counter += 1
                    current_turn_lines = []

                # Parse new turn header
                current_timestamp = match.group(1).strip()
                current_speaker = match.group(2).strip()
                current_task_id = match.group(3).strip() if match.group(3) else None
            elif line.strip() and current_speaker:
                current_turn_lines.append(line.strip())

        # Save last turn
        if current_speaker and current_turn_lines:
            utterance = "\n".join(current_turn_lines).strip()
            turns.append(
                TranscriptTurn(
                    turn_id=f"turn_{turn_counter:03d}",
                    speaker=current_speaker,
                    timestamp=current_timestamp or "unknown",
                    utterance=utterance,
                    task_id=current_task_id,
                )
            )

        return turns

    def load_notes(
        self, session_id: str, file_path: str, participant_id: str
    ) -> dict[str, Any]:
        """Load and parse researcher observation notes."""
        try:
            file_path_obj = Path(file_path)

            if not file_path_obj.exists():
                raise FileNotFoundError(f"Notes file not found: {file_path}")

            # Parse notes
            notes = self._parse_notes(file_path, participant_id)

            # Create notes object
            notes_data = {
                "session_id": session_id,
                "participant_id": participant_id,
                "notes": [note.model_dump() for note in notes],
                "source_file": str(file_path),
                "metadata": {"format": "markdown"},
            }

            # Save notes
            self.notes_manager.save_notes(session_id, notes_data)

            logger.info(f"Loaded notes {session_id}: {len(notes)} observations")

            return {
                "status": "success",
                "session_id": session_id,
                "notes_count": len(notes),
                "participant_id": participant_id,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to load notes: {e}")
            return {"status": "error", "error": str(e)}

    def _parse_notes(self, file_path: str, participant_id: str) -> list[ObservationNote]:
        """Parse observation notes from markdown file."""
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        notes: list[ObservationNote] = []
        note_counter = 1

        # Split by --- (note separator)
        note_blocks = content.split("---")

        for block in note_blocks:
            block = block.strip()
            if not block:
                continue

            lines = block.split("\n")
            timestamp = None
            observer = None
            task_id = None
            confidence = 0.5
            observation_lines: list[str] = []

            for line in lines:
                line_stripped = line.strip()

                if line_stripped.startswith("##"):
                    # Header line with timestamp
                    match = re.search(r"\[(.+?)\]", line_stripped)
                    if match:
                        timestamp = match.group(1)
                elif line_stripped.startswith("Observer:") or line_stripped.startswith("Researcher:"):
                    observer = line_stripped.split(":", 1)[1].strip()
                elif line_stripped.startswith("Task:"):
                    task_id = line_stripped.split(":", 1)[1].strip()
                elif line_stripped.startswith("Confidence:"):
                    try:
                        confidence = float(line_stripped.split(":", 1)[1].strip())
                    except ValueError:
                        confidence = 0.5
                elif line_stripped and not line_stripped.startswith("#"):
                    observation_lines.append(line_stripped)

            if timestamp and observation_lines:
                observation_text = " ".join(observation_lines)
                notes.append(
                    ObservationNote(
                        note_id=f"note_{note_counter:03d}",
                        participant_id=participant_id,
                        timestamp=timestamp,
                        observation=observation_text,
                        task_id=task_id,
                        confidence=confidence,
                        metadata={"observer": observer or "Unknown"},
                    )
                )
                note_counter += 1

        return notes

    def _calculate_duration(self, turns: list[TranscriptTurn]) -> Optional[int]:
        """Calculate session duration from first and last turn timestamps."""
        if not turns:
            return None

        try:
            # Try to extract MM:SS or similar
            first_ts = turns[0].timestamp
            last_ts = turns[-1].timestamp

            # Very basic calculation - in real implementation, parse timestamps properly
            if self.MM_SS_PATTERN.search(str(last_ts)):
                return None  # Would need proper parsing

            return None
        except Exception:
            return None

    def validate_ingestion(self) -> dict[str, Any]:
        """Validate all loaded transcripts and notes."""
        errors: list[str] = []
        warnings: list[str] = []

        try:
            transcripts = self.transcript_manager.list_transcripts()
            notes_list = self.notes_manager.list_notes()

            # Check minimum data
            if not transcripts:
                errors.append("No transcripts loaded")
            if not notes_list:
                warnings.append("No observation notes loaded")

            # Validate each transcript
            for tid in transcripts:
                try:
                    transcript = self.transcript_manager.load_transcript(tid)
                    turns_count = len(transcript.get("turns", []))
                    if turns_count == 0:
                        errors.append(f"Transcript {tid} has no turns")
                except Exception as e:
                    errors.append(f"Failed to validate transcript {tid}: {e}")

            return {
                "valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings,
                "transcripts_count": len(transcripts),
                "notes_count": len(notes_list),
            }

        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return {"valid": False, "error": str(e)}
