"""Evaluator skill implementation for 5-check verification of findings."""

import logging
from typing import Any, Optional, Dict, List
from datetime import datetime
import re

from ut_analysis.models import (
    Finding,
    EvaluatedFinding,
    EvaluationResult,
    EvaluationCheckType,
)
from ut_analysis.state_management import (
    StateManager,
    TranscriptManager,
    FindingsManager,
    EvaluationManager,
)

logger = logging.getLogger(__name__)


class EvaluatorSkill:
    """Evaluates findings using 5-check verification process."""

    def __init__(
        self,
        state_manager: StateManager,
        transcript_manager: TranscriptManager | None = None,
        findings_manager: FindingsManager | None = None,
        evaluation_manager: EvaluationManager | None = None,
    ) -> None:
        self.state_manager = state_manager
        self.transcript_manager = transcript_manager or TranscriptManager(
            state_manager.project_dir / "data"
        )
        self.findings_manager = findings_manager or FindingsManager(
            state_manager.project_dir / "data"
        )
        self.evaluation_manager = evaluation_manager or EvaluationManager(
            state_manager.project_dir / "data"
        )

    def evaluate_findings(
        self,
        findings_batch_id: str,
        transcript_ids: List[str],
        evaluation_batch_id: str = "eval_default",
        max_iterations: int = 3,
    ) -> Dict[str, Any]:
        """Evaluate findings using 5-check process."""
        try:
            # Load findings
            findings_data = self.findings_manager.load_findings(findings_batch_id)
            findings = [Finding(**f) for f in findings_data.get("findings", [])]

            # Load transcripts for validation
            transcripts = {}
            for tid in transcript_ids:
                try:
                    transcripts[tid] = self.transcript_manager.load_transcript(tid)
                except Exception as e:
                    logger.warning(f"Could not load transcript {tid}: {e}")

            # Evaluate each finding
            evaluated_findings: List[EvaluatedFinding] = []
            for finding in findings:
                evaluated = self._evaluate_single_finding(
                    finding, transcripts, max_iterations
                )
                evaluated_findings.append(evaluated)

            # Calculate statistics
            stats = self._calculate_evaluation_stats(evaluated_findings)

            # Prepare result
            result = {
                "evaluation_batch_id": evaluation_batch_id,
                "evaluated_findings": [ef.model_dump() for ef in evaluated_findings],
                "evaluation_stats": stats,
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Save evaluation results
            self.evaluation_manager.save_evaluation(evaluation_batch_id, result)

            # Update state
            self.state_manager.add_finding(f"{evaluation_batch_id}_eval", {
                "total_evaluated": len(evaluated_findings),
                "passed": stats["passed_all_checks"],
                "failed": stats["failed_checks"],
                "needs_revision": stats["needs_revision"],
            })

            logger.info(f"Evaluated {len(evaluated_findings)} findings in batch {evaluation_batch_id}")

            return result

        except Exception as e:
            logger.error(f"Evaluation failed: {e}")
            return {"status": "error", "error": str(e)}

    def _evaluate_single_finding(
        self,
        finding: Finding,
        transcripts: Dict[str, Dict[str, Any]],
        max_iterations: int,
    ) -> EvaluatedFinding:
        """Evaluate a single finding through 5-check process."""
        evaluation_results: List[EvaluationResult] = []

        # Check 1: Verbatim Match
        check1 = self._check_verbatim_match(finding, transcripts)
        evaluation_results.append(check1)

        # Check 2: Meaning Accuracy
        check2 = self._check_meaning_accuracy(finding, transcripts)
        evaluation_results.append(check2)

        # Check 3: Task Attribution
        check3 = self._check_task_attribution(finding)
        evaluation_results.append(check3)

        # Check 4: No Interpretation
        check4 = self._check_no_interpretation(finding)
        evaluation_results.append(check4)

        # Check 5: Justified Severity
        check5 = self._check_justified_severity(finding)
        evaluation_results.append(check5)

        # Determine overall result
        all_passed = all(result.passed for result in evaluation_results)
        failed_checks = [
            result.check_type.value
            for result in evaluation_results
            if not result.passed
        ]

        # Generate correction instructions if needed
        correction_instructions = None
        if not all_passed:
            correction_instructions = self._generate_correction_instructions(
                evaluation_results
            )

        return EvaluatedFinding(
            finding_id=finding.finding_id,
            original_finding=finding,
            evaluation_results=evaluation_results,
            all_passed=all_passed,
            failed_checks=failed_checks,
            correction_instructions=correction_instructions,
            revision_count=0,  # Would be incremented in revelation loop
            evaluated_at=datetime.utcnow(),
        )

    def _check_verbatim_match(
        self, finding: Finding, transcripts: Dict[str, Dict[str, Any]]
    ) -> EvaluationResult:
        """Check 1: Verbatim quote exists in transcript."""
        try:
            transcript_id = finding.source_transcript_id
            if transcript_id not in transcripts:
                return EvaluationResult(
                    check_type=EvaluationCheckType.VERBATIM_MATCH,
                    passed=False,
                    feedback=f"Transcript {transcript_id} not found",
                    severity=2,
                )

            transcript = transcripts[transcript_id]
            turns = transcript.get("turns", [])

            # Look for exact quote match
            quote_found = False
            for turn in turns:
                if finding.verbatim_quote.strip() in turn.get("utterance", ""):
                    quote_found = True
                    break

            if quote_found:
                return EvaluationResult(
                    check_type=EvaluationCheckType.VERBATIM_MATCH,
                    passed=True,
                    feedback="Quote found exactly in transcript",
                )
            else:
                return EvaluationResult(
                    check_type=EvaluationCheckType.VERBATIM_MATCH,
                    passed=False,
                    feedback="Quote not found verbatim in transcript",
                    severity=2,
                )

        except Exception as e:
            return EvaluationResult(
                check_type=EvaluationCheckType.VERBATIM_MATCH,
                passed=False,
                feedback=f"Error checking verbatim match: {str(e)}",
                severity=1,
            )

    def _check_meaning_accuracy(
        self, finding: Finding, transcripts: Dict[str, Dict[str, Any]]
    ) -> EvaluationResult:
        """Check 2: Finding accurately reflects quote meaning."""
        try:
            # Simple heuristic: check if finding description contains key elements from quote
            quote_words = set(finding.verbatim_quote.lower().split())
            description_words = set(finding.description.lower().split())

            # Calculate overlap
            overlap = len(quote_words.intersection(description_words))
            overlap_ratio = overlap / len(quote_words) if quote_words else 0

            if overlap_ratio > 0.5:
                return EvaluationResult(
                    check_type=EvaluationCheckType.MEANING_ACCURACY,
                    passed=True,
                    feedback="Finding accurately reflects quote meaning",
                )
            else:
                return EvaluationResult(
                    check_type=EvaluationCheckType.MEANING_ACCURACY,
                    passed=False,
                    feedback="Finding may not accurately reflect quote meaning",
                    severity=1,
                )

        except Exception as e:
            return EvaluationResult(
                check_type=EvaluationCheckType.MEANING_ACCURACY,
                passed=False,
                feedback=f"Error checking meaning accuracy: {str(e)}",
                severity=1,
            )

    def _check_task_attribution(self, finding: Finding) -> EvaluationResult:
        """Check 3: Task attribution is correct."""
        try:
            # Basic validation: task_id should be present and reasonable
            if not finding.task_id:
                return EvaluationResult(
                    check_type=EvaluationCheckType.TASK_ATTRIBUTION,
                    passed=False,
                    feedback="No task ID assigned to finding",
                    severity=1,
                )

            # Check if task_id looks like a valid task ID
            if not re.match(r"^TASK-\d+$", finding.task_id):
                return EvaluationResult(
                    check_type=EvaluationCheckType.TASK_ATTRIBUTION,
                    passed=False,
                    feedback=f"Task ID format invalid: {finding.task_id}",
                    severity=1,
                )

            return EvaluationResult(
                check_type=EvaluationCheckType.TASK_ATTRIBUTION,
                passed=True,
                feedback="Task attribution appears correct",
            )

        except Exception as e:
            return EvaluationResult(
                check_type=EvaluationCheckType.TASK_ATTRIBUTION,
                passed=False,
                feedback=f"Error checking task attribution: {str(e)}",
                severity=1,
            )

    def _check_no_interpretation(self, finding: Finding) -> EvaluationResult:
        """Check 4: No researcher interpretation presented as participant statement."""
        try:
            text = finding.description.lower()

            # Look for interpretation phrases
            interpretation_phrases = [
                "seemed", "appeared", "looked", "probably", "likely",
                "participant was", "user felt", "they might", "could be"
            ]

            for phrase in interpretation_phrases:
                if phrase in text:
                    return EvaluationResult(
                        check_type=EvaluationCheckType.NO_INTERPRETATION,
                        passed=False,
                        feedback=f"Contains interpretation: '{phrase}'",
                        severity=1,
                    )

            return EvaluationResult(
                check_type=EvaluationCheckType.NO_INTERPRETATION,
                passed=True,
                feedback="No researcher interpretation detected",
            )

        except Exception as e:
            return EvaluationResult(
                check_type=EvaluationCheckType.NO_INTERPRETATION,
                passed=False,
                feedback=f"Error checking interpretation: {str(e)}",
                severity=1,
            )

    def _check_justified_severity(self, finding: Finding) -> EvaluationResult:
        """Check 5: Severity rating is justified by evidence."""
        try:
            # If no severity assigned yet, this check doesn't apply
            if finding.severity is None:
                return EvaluationResult(
                    check_type=EvaluationCheckType.JUSTIFIED_SEVERITY,
                    passed=True,
                    feedback="No severity rating assigned yet",
                )

            # Basic heuristic: check if description supports severity level
            severity = finding.severity
            text = finding.description.lower()

            # Words indicating different severity levels
            catastrophic_words = ["impossible", "cannot complete", "completely stuck", "system crash"]
            critical_words = ["major problem", "significant issue", "blocks task"]
            major_words = ["difficult", "confusing", "error"]
            minor_words = ["minor inconvenience", "small issue", "slightly confusing"]

            if severity == 4:  # Catastrophic
                if not any(word in text for word in catastrophic_words):
                    return EvaluationResult(
                        check_type=EvaluationCheckType.JUSTIFIED_SEVERITY,
                        passed=False,
                        feedback="Severity 4 (catastrophic) not supported by evidence",
                        severity=1,
                    )
            elif severity == 3:  # Critical
                if not any(word in text for word in critical_words + catastrophic_words):
                    return EvaluationResult(
                        check_type=EvaluationCheckType.JUSTIFIED_SEVERITY,
                        passed=False,
                        feedback="Severity 3 (critical) not supported by evidence",
                        severity=1,
                    )
            elif severity == 2:  # Major
                if not any(word in text for word in major_words + critical_words + catastrophic_words):
                    return EvaluationResult(
                        check_type=EvaluationCheckType.JUSTIFIED_SEVERITY,
                        passed=False,
                        feedback="Severity 2 (major) not supported by evidence",
                        severity=1,
                    )

            return EvaluationResult(
                check_type=EvaluationCheckType.JUSTIFIED_SEVERITY,
                passed=True,
                feedback="Severity rating appears justified",
            )

        except Exception as e:
            return EvaluationResult(
                check_type=EvaluationCheckType.JUSTIFIED_SEVERITY,
                passed=False,
                feedback=f"Error checking severity justification: {str(e)}",
                severity=1,
            )

    def _generate_correction_instructions(
        self, evaluation_results: List[EvaluationResult]
    ) -> str:
        """Generate correction instructions for failed checks."""
        instructions = []

        for result in evaluation_results:
            if not result.passed:
                if result.check_type == EvaluationCheckType.VERBATIM_MATCH:
                    instructions.append(
                        "Quote not found in transcript. Please use exact text from transcript."
                    )
                elif result.check_type == EvaluationCheckType.MEANING_ACCURACY:
                    instructions.append(
                        "Finding does not accurately reflect quote meaning. Re-read in context."
                    )
                elif result.check_type == EvaluationCheckType.TASK_ATTRIBUTION:
                    instructions.append(
                        "Task attribution incorrect. Verify which task was being performed."
                    )
                elif result.check_type == EvaluationCheckType.NO_INTERPRETATION:
                    instructions.append(
                        "Contains researcher interpretation. Use direct participant quotes only."
                    )
                elif result.check_type == EvaluationCheckType.JUSTIFIED_SEVERITY:
                    instructions.append(
                        "Severity rating not justified by evidence. Review Nielsen scale criteria."
                    )

        return " ".join(instructions)

    def _calculate_evaluation_stats(
        self, evaluated_findings: List[EvaluatedFinding]
    ) -> Dict[str, Any]:
        """Calculate evaluation statistics."""
        total = len(evaluated_findings)
        passed_all = sum(1 for ef in evaluated_findings if ef.all_passed)
        failed = total - passed_all

        # Count failures by check type
        failure_counts = {}
        for ef in evaluated_findings:
            for failed_check in ef.failed_checks:
                failure_counts[failed_check] = failure_counts.get(failed_check, 0) + 1

        # Average checks passed
        total_checks = total * 5  # 5 checks per finding
        passed_checks = sum(
            len([r for r in ef.evaluation_results if r.passed])
            for ef in evaluated_findings
        )
        avg_checks_passed = passed_checks / total if total > 0 else 0

        # Findings needing revision
        needs_revision = sum(1 for ef in evaluated_findings if not ef.all_passed)

        return {
            "total_findings": total,
            "passed_all_checks": passed_all,
            "failed_checks": failed,
            "by_failure_reason": failure_counts,
            "average_checks_passed": round(avg_checks_passed, 1),
            "needs_revision": needs_revision,
        }
