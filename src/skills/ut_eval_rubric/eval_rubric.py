"""Evaluation rubric skill implementation."""

import logging
from datetime import datetime
from typing import Any

from ut_analysis.state_management import (
    EvalRubricManager,
    ReviewCheckpointManager,
    StateManager,
)

logger = logging.getLogger(__name__)

RUBRIC_DIMENSIONS = [
    "evidence_groundedness",
    "specificity",
    "research_usefulness",
    "actionability",
    "appropriate_confidence",
    "provenance_completeness",
    "contradiction_handling",
    "no_overclaiming",
    "output_format_validity",
]


class EvalRubricSkill:
    """Evaluates pipeline artifacts against a quality rubric."""

    def __init__(
        self,
        state_manager: StateManager,
        eval_manager: EvalRubricManager | None = None,
        review_manager: ReviewCheckpointManager | None = None,
    ) -> None:
        self.state_manager = state_manager
        self.eval_manager = eval_manager or EvalRubricManager(
            state_manager.project_dir / "data"
        )
        self.review_manager = review_manager or ReviewCheckpointManager(
            state_manager.project_dir / "data"
        )

    def evaluate_artifact(
        self,
        artifact: dict[str, Any],
        artifact_id: str,
        artifact_type: str,
    ) -> dict[str, Any]:
        """Evaluate a single artifact against the rubric."""
        scores = []
        issues = []
        recommended_fixes = []

        for dimension in RUBRIC_DIMENSIONS:
            score_result = self._check_dimension(dimension, artifact, artifact_type)
            scores.append(score_result)
            if not score_result["passed"]:
                issues.append(f"{dimension}: {score_result['rationale']}")
                recommended_fixes.append(
                    f"Improve {dimension}: {score_result['rationale']}"
                )

        failed_count = sum(1 for s in scores if not s["passed"])
        if failed_count >= 3:
            pass_fail = "fail"
        elif failed_count >= 1:
            pass_fail = "warning"
        else:
            pass_fail = "pass"

        created_checkpoint = False
        if pass_fail == "fail":
            self._create_review_checkpoint(artifact_id, artifact_type, issues)
            created_checkpoint = True

        return {
            "artifact_id": artifact_id,
            "artifact_type": artifact_type,
            "evaluator": "ut-eval-rubric",
            "scores": scores,
            "pass_fail": pass_fail,
            "issues": issues,
            "recommended_fixes": recommended_fixes,
            "created_human_review_checkpoint": created_checkpoint,
            "evaluated_at": datetime.utcnow().isoformat(),
        }

    def evaluate_batch(
        self,
        artifacts: list[dict[str, Any]],
        run_id: str,
    ) -> dict[str, Any]:
        """Evaluate a batch of artifacts."""
        try:
            results = []
            for artifact in artifacts:
                result = self.evaluate_artifact(
                    artifact=artifact.get("data", artifact),
                    artifact_id=artifact.get("artifact_id", "unknown"),
                    artifact_type=artifact.get("artifact_type", "unknown"),
                )
                results.append(result)

            passed = sum(1 for r in results if r["pass_fail"] == "pass")
            failed = sum(1 for r in results if r["pass_fail"] == "fail")
            warnings = sum(1 for r in results if r["pass_fail"] == "warning")

            summary = {
                "run_id": run_id,
                "total_artifacts_evaluated": len(results),
                "passed": passed,
                "failed": failed,
                "warnings": warnings,
                "eval_results": results,
                "created_at": datetime.utcnow().isoformat(),
            }

            self.eval_manager.save_eval_results(run_id, summary)
            return summary

        except Exception as e:
            logger.error(f"Batch evaluation failed: {e}")
            return {"status": "error", "error": str(e)}

    def _check_dimension(
        self, dimension: str, artifact: dict[str, Any], artifact_type: str
    ) -> dict[str, Any]:
        """Check a single rubric dimension."""
        checkers = {
            "evidence_groundedness": self._check_evidence_groundedness,
            "specificity": self._check_specificity,
            "research_usefulness": self._check_research_usefulness,
            "actionability": self._check_actionability,
            "appropriate_confidence": self._check_confidence,
            "provenance_completeness": self._check_provenance,
            "contradiction_handling": self._check_contradiction_handling,
            "no_overclaiming": self._check_overclaiming,
            "output_format_validity": self._check_format,
        }

        checker = checkers.get(dimension, self._default_check)
        return checker(artifact, artifact_type)

    def _check_evidence_groundedness(
        self, artifact: dict[str, Any], artifact_type: str
    ) -> dict[str, Any]:
        """Check if claims are grounded in evidence."""
        has_quotes = bool(
            artifact.get("representative_quotes")
            or artifact.get("key_quotes")
            or artifact.get("verbatim_quote")
        )
        has_finding_ids = bool(
            artifact.get("source_finding_ids")
            or artifact.get("finding_ids")
            or artifact.get("finding_id")
        )

        passed = has_quotes or has_finding_ids
        score = 1.0 if (has_quotes and has_finding_ids) else (0.5 if passed else 0.0)

        return {
            "dimension": "evidence_groundedness",
            "score": score,
            "rationale": "Evidence linked" if passed else "No evidence references found",
            "passed": passed,
        }

    def _check_specificity(
        self, artifact: dict[str, Any], artifact_type: str
    ) -> dict[str, Any]:
        """Check if the artifact is specific rather than vague."""
        text_fields = ["description", "summary", "theme_summary", "title"]
        text = ""
        for field in text_fields:
            if artifact.get(field):
                text += str(artifact[field]) + " "

        vague_markers = ["some users", "generally", "various", "many things", "stuff"]
        has_vague = any(marker in text.lower() for marker in vague_markers)
        is_specific = len(text) > 20 and not has_vague

        return {
            "dimension": "specificity",
            "score": 0.8 if is_specific else 0.3,
            "rationale": (
                "Sufficiently specific" if is_specific else "Contains vague language"
            ),
            "passed": is_specific,
        }

    def _check_research_usefulness(
        self, artifact: dict[str, Any], artifact_type: str
    ) -> dict[str, Any]:
        """Check if the artifact contributes useful research insight."""
        has_implication = bool(
            artifact.get("product_implication")
            or artifact.get("product_implications")
            or artifact.get("recommendations")
        )
        return {
            "dimension": "research_usefulness",
            "score": 0.8 if has_implication else 0.4,
            "rationale": (
                "Contains actionable implication"
                if has_implication
                else "No clear product/research implication"
            ),
            "passed": True,
        }

    def _check_actionability(
        self, artifact: dict[str, Any], artifact_type: str
    ) -> dict[str, Any]:
        """Check if findings lead to actionable next steps."""
        actionable_fields = [
            "product_implication",
            "product_implications",
            "recommended_follow_up",
            "recommendations",
            "design_implications",
        ]
        has_action = any(artifact.get(f) for f in actionable_fields)
        return {
            "dimension": "actionability",
            "score": 0.8 if has_action else 0.4,
            "rationale": "Actionable" if has_action else "No clear action suggested",
            "passed": True,
        }

    def _check_confidence(
        self, artifact: dict[str, Any], artifact_type: str
    ) -> dict[str, Any]:
        """Check if confidence is appropriate for evidence level."""
        confidence = artifact.get("confidence", None)
        participant_count = artifact.get("participant_count", 0)

        if confidence is None:
            return {
                "dimension": "appropriate_confidence",
                "score": 0.5,
                "rationale": "No confidence score provided",
                "passed": True,
            }

        if confidence > 0.8 and participant_count <= 1:
            return {
                "dimension": "appropriate_confidence",
                "score": 0.2,
                "rationale": (
                    f"Confidence {confidence} too high for {participant_count} "
                    "participant(s)"
                ),
                "passed": False,
            }

        return {
            "dimension": "appropriate_confidence",
            "score": 0.8,
            "rationale": "Confidence appropriate for evidence level",
            "passed": True,
        }

    def _check_provenance(
        self, artifact: dict[str, Any], artifact_type: str
    ) -> dict[str, Any]:
        """Check if provenance chain is complete."""
        provenance_fields = [
            "source_finding_ids",
            "finding_ids",
            "finding_id",
            "source_transcript_id",
            "participant_id",
        ]
        has_provenance = any(artifact.get(f) for f in provenance_fields)
        return {
            "dimension": "provenance_completeness",
            "score": 0.9 if has_provenance else 0.2,
            "rationale": (
                "Provenance chain present"
                if has_provenance
                else "Missing provenance — cannot trace to source"
            ),
            "passed": has_provenance,
        }

    def _check_contradiction_handling(
        self, artifact: dict[str, Any], artifact_type: str
    ) -> dict[str, Any]:
        """Check if contradictions are acknowledged."""
        has_contradictions = bool(
            artifact.get("contradictions_or_outliers")
            or artifact.get("tensions_or_contradictions")
        )
        if artifact_type in ("theme", "consolidation", "consolidated_theme"):
            return {
                "dimension": "contradiction_handling",
                "score": 0.8 if has_contradictions else 0.5,
                "rationale": (
                    "Contradictions acknowledged"
                    if has_contradictions
                    else "No contradictions noted — verify none exist"
                ),
                "passed": True,
            }
        return {
            "dimension": "contradiction_handling",
            "score": 0.8,
            "rationale": "N/A for this artifact type",
            "passed": True,
        }

    def _check_overclaiming(
        self, artifact: dict[str, Any], artifact_type: str
    ) -> dict[str, Any]:
        """Check for absolute language that overclaims."""
        text_fields = ["description", "summary", "theme_summary", "title"]
        text = ""
        for field in text_fields:
            if artifact.get(field):
                text += str(artifact[field]) + " "

        overclaim_markers = [
            "all users",
            "everyone",
            "always",
            "never",
            "definitely",
            "certainly",
            "proves that",
            "clearly shows",
        ]
        found_overclaims = [m for m in overclaim_markers if m in text.lower()]

        passed = len(found_overclaims) == 0
        return {
            "dimension": "no_overclaiming",
            "score": 0.9 if passed else 0.2,
            "rationale": (
                "No overclaiming detected"
                if passed
                else f"Overclaiming language found: {', '.join(found_overclaims)}"
            ),
            "passed": passed,
        }

    def _check_format(
        self, artifact: dict[str, Any], artifact_type: str
    ) -> dict[str, Any]:
        """Check output format validity."""
        is_valid = isinstance(artifact, dict) and len(artifact) > 0
        return {
            "dimension": "output_format_validity",
            "score": 1.0 if is_valid else 0.0,
            "rationale": "Valid format" if is_valid else "Invalid or empty artifact",
            "passed": is_valid,
        }

    def _default_check(
        self, artifact: dict[str, Any], artifact_type: str
    ) -> dict[str, Any]:
        """Default check for unknown dimensions."""
        return {
            "dimension": "unknown",
            "score": 0.5,
            "rationale": "No specific check implemented",
            "passed": True,
        }

    def _create_review_checkpoint(
        self, artifact_id: str, artifact_type: str, issues: list[str]
    ) -> None:
        """Create a human review checkpoint for failed evaluations."""
        checkpoint_data = {
            "checkpoints": [
                {
                    "checkpoint_id": f"RC_EVAL_{artifact_id}",
                    "stage": "evaluation_rubric",
                    "reason": (
                        "Artifact failed quality evaluation: "
                        f"{'; '.join(issues[:2])}"
                    ),
                    "related_artifact_id": artifact_id,
                    "artifact_type": (
                        artifact_type
                        if artifact_type
                        in (
                            "finding",
                            "theme",
                            "insight",
                            "recommendation",
                            "critique",
                            "reconciliation",
                            "contradiction",
                        )
                        else "insight"
                    ),
                    "severity": "high",
                    "suggested_reviewer_action": (
                        f"Review {artifact_id} for quality issues: "
                        f"{issues[0] if issues else 'unknown'}"
                    ),
                    "status": "pending",
                    "created_at": datetime.utcnow().isoformat(),
                }
            ]
        }
        self.review_manager.save_checkpoints(f"eval_{artifact_id}", checkpoint_data)
