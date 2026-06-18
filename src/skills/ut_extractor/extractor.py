"""Extractor skill implementation for finding extraction from transcripts."""

import logging
from typing import Any, Optional, Dict, List
from datetime import datetime
import re

from ut_analysis.models import (
    Finding,
    FindingCategory,
    TaskOutcome,
    TaskOutcomeType,
    TranscriptTurn,
    ObservationNote,
)
from ut_analysis.state_management import (
    StateManager,
    TranscriptManager,
    NotesManager,
    FindingsManager,
)

logger = logging.getLogger(__name__)


class ExtractorSkill:
    """Extracts usability findings from transcripts and observation notes."""

    def __init__(
        self,
        state_manager: StateManager,
        transcript_manager: TranscriptManager | None = None,
        notes_manager: NotesManager | None = None,
        findings_manager: FindingsManager | None = None,
    ) -> None:
        self.state_manager = state_manager
        self.transcript_manager = transcript_manager or TranscriptManager(
            state_manager.project_dir / "data"
        )
        self.notes_manager = notes_manager or NotesManager(state_manager.project_dir / "data")
        self.findings_manager = findings_manager or FindingsManager(
            state_manager.project_dir / "data"
        )
        self.task_definitions: Dict[str, Dict[str, Any]] = {}

    def load_config_tasks(self, config_data: Dict[str, Any]) -> None:
        """Load task definitions from project config."""
        for task in config_data.get("tasks", []):
            self.task_definitions[task["id"]] = task
            if "name" in task:
                self.task_definitions[task["name"]] = task

    def extract_findings(
        self,
        transcript_ids: List[str],
        note_session_ids: Optional[List[str]] = None,
        project_config: Optional[Dict[str, Any]] = None,
        batch_id: str = "batch_default",
    ) -> Dict[str, Any]:
        """Extract findings from transcripts and notes."""
        try:
            if project_config:
                self.load_config_tasks(project_config)

            all_findings: List[Finding] = []
            task_completion_matrix: Dict[str, Dict[str, Dict[str, Any]]] = {}
            finding_counter = 1

            # Extract from transcripts
            for transcript_id in transcript_ids:
                try:
                    transcript_data = self.transcript_manager.load_transcript(transcript_id)
                    findings, task_outcomes = self._extract_from_transcript(
                        transcript_data, finding_counter
                    )
                    all_findings.extend(findings)
                    finding_counter += len(findings)

                    # Update task completion matrix
                    for outcome in task_outcomes:
                        task_id = outcome.task_id
                        participant_id = outcome.participant_id
                        if task_id not in task_completion_matrix:
                            task_completion_matrix[task_id] = {}
                        task_completion_matrix[task_id][participant_id] = {
                            "outcome": outcome.outcome.value,
                            "time_seconds": outcome.time_to_completion,
                            "help_requested": outcome.help_requested,
                        }

                except Exception as e:
                    logger.warning(f"Failed to extract from transcript {transcript_id}: {e}")

            # Extract from notes
            if note_session_ids:
                for session_id in note_session_ids:
                    try:
                        notes_data = self.notes_manager.load_notes(session_id)
                        findings = self._extract_from_notes(notes_data, finding_counter)
                        all_findings.extend(findings)
                        finding_counter += len(findings)
                    except Exception as e:
                        logger.warning(f"Failed to extract from notes {session_id}: {e}")

            # Convert to dict format for JSON serialization
            findings_data = {
                "extraction_batch_id": batch_id,
                "findings": [finding.model_dump() for finding in all_findings],
                "task_completion_matrix": task_completion_matrix,
                "extraction_stats": self._calculate_stats(all_findings, task_completion_matrix),
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Save findings
            self.findings_manager.save_findings(batch_id, findings_data)

            # Update state
            self.state_manager.add_finding(batch_id, {
                "count": len(all_findings),
                "categories": self._count_categories(all_findings),
                "participants": list(set(f.participant_id for f in all_findings)),
            })

            logger.info(f"Extracted {len(all_findings)} findings in batch {batch_id}")

            return findings_data

        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            return {"status": "error", "error": str(e)}

    def _extract_from_transcript(
        self, transcript_data: Dict[str, Any], finding_counter: int
    ) -> tuple[List[Finding], List[TaskOutcome]]:
        """Extract findings from a single transcript."""
        findings: List[Finding] = []
        task_outcomes: List[TaskOutcome] = []

        turns = transcript_data.get("turns", [])
        transcript_id = transcript_data.get("transcript_id", "")
        participant_id = transcript_data.get("participant_id", "")

        # Track task completion status
        task_status: Dict[str, Dict[str, Any]] = {}

        for i, turn_data in enumerate(turns):
            turn = TranscriptTurn(**turn_data)
            context = self._get_context(turns, i)

            # Extract findings from this turn
            turn_findings = self._analyze_turn(turn, context, transcript_id, participant_id)
            findings.extend(turn_findings)

            # Track task completion
            task_outcome = self._assess_task_completion(turn, context, participant_id)
            if task_outcome:
                task_outcomes.append(task_outcome)
                task_status[task_outcome.task_id] = {
                    "outcome": task_outcome.outcome,
                    "time_seconds": task_outcome.time_to_completion,
                }

        return findings, task_outcomes

    def _extract_from_notes(
        self, notes_data: Dict[str, Any], finding_counter: int
    ) -> List[Finding]:
        """Extract findings from observation notes."""
        findings: List[Finding] = []

        notes = notes_data.get("notes", [])
        session_id = notes_data.get("session_id", "")
        participant_id = notes_data.get("participant_id", "")

        for note_data in notes:
            note = ObservationNote(**note_data)

            # Convert observation notes to findings
            finding = Finding(
                finding_id=f"F_{finding_counter:04d}",
                category=self._categorize_observation(note.observation),
                title=self._generate_title_from_observation(note.observation),
                description=note.observation,
                verbatim_quote=note.observation,
                speaker="Researcher",  # Observations are from researcher
                timestamp=note.timestamp,
                source_transcript_id=session_id,  # Use session ID as source
                task_id=note.task_id,
                participant_id=participant_id,
                confidence=note.confidence,
                extracted_at=datetime.utcnow(),
                metadata={"source_type": "observation_note"},
            )
            findings.append(finding)
            finding_counter += 1

        return findings

    def _analyze_turn(
        self,
        turn: TranscriptTurn,
        context: Dict[str, List[str]],
        transcript_id: str,
        participant_id: str,
    ) -> List[Finding]:
        """Analyze a single turn for findings."""
        findings: List[Finding] = []

        text = turn.utterance.lower()
        speaker = turn.speaker.lower()

        # Define patterns for different categories
        patterns = {
            FindingCategory.USABILITY_ISSUE: [
                r"can't find", r"doesn't work", r"stuck", r"confused",
                r"lost", r"not sure", r"where is", r"how do i"
            ],
            FindingCategory.PAIN_POINT: [
                r"annoying", r"frustrating", r"hard", r"difficult",
                r"confusing", r"weird", r"strange"
            ],
            FindingCategory.POSITIVE_MOMENT: [
                r"easy", r"great", r"perfect", r"love", r"awesome",
                r"intuitive", r"helpful", r"clear"
            ],
        }

        for category, pattern_list in patterns.items():
            for pattern in pattern_list:
                if re.search(pattern, text):
                    confidence = self._calculate_confidence(text, speaker, context)

                    finding = Finding(
                        finding_id=f"F_{len(findings) + 1:04d}",
                        category=category,
                        title=self._generate_title(turn.utterance, category),
                        description=turn.utterance,
                        verbatim_quote=turn.utterance,
                        speaker=turn.speaker,
                        timestamp=turn.timestamp,
                        source_transcript_id=transcript_id,
                        task_id=turn.task_id,
                        participant_id=participant_id,
                        confidence=confidence,
                        extracted_at=datetime.utcnow(),
                        metadata={
                            "context_before": context.get("before", []),
                            "context_after": context.get("after", []),
                        },
                    )
                    findings.append(finding)
                    break  # Only one finding per turn per category

        return findings

    def _assess_task_completion(
        self, turn: TranscriptTurn, context: Dict[str, List[str]], participant_id: str
    ) -> Optional[TaskOutcome]:
        """Assess if this turn indicates task completion."""
        text = turn.utterance.lower()

        # Success indicators
        if any(phrase in text for phrase in ["completed", "done", "finished", "great", "perfect"]):
            return TaskOutcome(
                task_id=turn.task_id or "unknown",
                participant_id=participant_id,
                outcome=TaskOutcomeType.COMPLETED,
                time_to_completion=None,  # Would need to track from task start
                help_requested=False,
            )

        # Failure indicators
        elif any(phrase in text for phrase in ["can't", "failed", "stuck", "give up"]):
            return TaskOutcome(
                task_id=turn.task_id or "unknown",
                participant_id=participant_id,
                outcome=TaskOutcomeType.FAILED,
                help_requested=False,
            )

        # Help request indicators
        elif any(phrase in text for phrase in ["help", "can you", "show me", "how do"]):
            return TaskOutcome(
                task_id=turn.task_id or "unknown",
                participant_id=participant_id,
                outcome=TaskOutcomeType.NEEDED_HELP,
                help_requested=True,
            )

        return None

    def _get_context(self, turns: List[Dict[str, Any]], current_index: int) -> Dict[str, List[str]]:
        """Get context around current turn."""
        context = {"before": [], "after": []}

        # Get 2 turns before
        for i in range(max(0, current_index - 2), current_index):
            if i < len(turns):
                turn = turns[i]
                context["before"].append(f"{turn.get('speaker', 'Unknown')}: {turn.get('utterance', '')}")

        # Get 2 turns after
        for i in range(current_index + 1, min(len(turns), current_index + 3)):
            turn = turns[i]
            context["after"].append(f"{turn.get('speaker', 'Unknown')}: {turn.get('utterance', '')}")

        return context

    def _calculate_confidence(
        self, text: str, speaker: str, context: Dict[str, List[str]]
    ) -> float:
        """Calculate confidence score for finding."""
        confidence = 0.5  # Base confidence

        # Higher confidence for explicit statements
        explicit_words = ["can't", "doesn't", "stuck", "confused", "easy", "great"]
        if any(word in text for word in explicit_words):
            confidence += 0.3

        # Higher for participants vs researchers
        if "participant" in speaker.lower():
            confidence += 0.1

        # Higher with corroborating context
        context_text = " ".join(context.get("before", []) + context.get("after", []))
        if any(word in context_text.lower() for word in ["help", "show", "guide"]):
            confidence += 0.1

        return min(confidence, 1.0)

    def _generate_title(self, text: str, category: FindingCategory) -> str:
        """Generate a concise title for the finding."""
        # Simple title generation - in practice, this would use more sophisticated NLP
        if category == FindingCategory.USABILITY_ISSUE:
            return f"Usability Issue: {text[:50]}..."
        elif category == FindingCategory.PAIN_POINT:
            return f"Pain Point: {text[:50]}..."
        elif category == FindingCategory.POSITIVE_MOMENT:
            return f"Positive Moment: {text[:50]}..."
        else:
            return f"Finding: {text[:50]}..."

    def _generate_title_from_observation(self, observation: str) -> str:
        """Generate title from observation note."""
        return f"Observation: {observation[:50]}..."

    def _categorize_observation(self, observation: str) -> FindingCategory:
        """Categorize observation note."""
        text = observation.lower()

        if any(word in text for word in ["issue", "problem", "difficulty", "struggle"]):
            return FindingCategory.USABILITY_ISSUE
        elif any(word in text for word in ["frustrated", "annoyed", "confused"]):
            return FindingCategory.PAIN_POINT
        elif any(word in text for word in ["pleased", "satisfied", "easy"]):
            return FindingCategory.POSITIVE_MOMENT
        else:
            return FindingCategory.PARTICIPANT_QUOTE

    def _calculate_stats(
        self, findings: List[Finding], task_matrix: Dict[str, Dict[str, Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Calculate extraction statistics."""
        total_findings = len(findings)

        # Category distribution
        categories = {}
        for finding in findings:
            cat = finding.category.value
            categories[cat] = categories.get(cat, 0) + 1

        # Average confidence
        avg_confidence = (
            sum(f.confidence for f in findings) / total_findings
            if total_findings > 0 else 0
        )

        # Task completion rate
        total_tasks = sum(len(participants) for participants in task_matrix.values())
        completed_tasks = sum(
            1 for task_data in task_matrix.values()
            for participant_data in task_data.values()
            if participant_data.get("outcome") == "completed"
        )
        completion_rate = completed_tasks / total_tasks if total_tasks > 0 else 0

        return {
            "total_findings": total_findings,
            "by_category": categories,
            "average_confidence": round(avg_confidence, 2),
            "task_completion_rate": round(completion_rate, 2),
        }

    def _count_categories(self, findings: List[Finding]) -> Dict[str, int]:
        """Count findings by category."""
        counts = {}
        for finding in findings:
            cat = finding.category.value
            counts[cat] = counts.get(cat, 0) + 1
        return counts
