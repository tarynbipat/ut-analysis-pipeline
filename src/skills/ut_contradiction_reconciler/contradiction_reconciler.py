"""Enhanced contradiction reconciler skill implementation."""

import logging
from datetime import datetime
from typing import Any

from ut_analysis.state_management import (
    ContradictionsManager,
    ReconciliationManager,
    ReviewCheckpointManager,
    StateManager,
)

logger = logging.getLogger(__name__)

EXPLANATION_FACTORS = [
    "segment",
    "experience_level",
    "task_context",
    "product_expectation",
    "evidence_limits",
    "other",
]


class ContradictionReconcilerSkill:
    """Reconciles contradictions into nuanced interpretations, preserving tension as signal."""

    def __init__(
        self,
        state_manager: StateManager,
        contradictions_manager: ContradictionsManager | None = None,
        reconciliation_manager: ReconciliationManager | None = None,
        review_manager: ReviewCheckpointManager | None = None,
    ) -> None:
        self.state_manager = state_manager
        self.contradictions_manager = contradictions_manager or ContradictionsManager(
            state_manager.project_dir / "data"
        )
        self.reconciliation_manager = reconciliation_manager or ReconciliationManager(
            state_manager.project_dir / "data"
        )
        self.review_manager = review_manager or ReviewCheckpointManager(
            state_manager.project_dir / "data"
        )

    def reconcile_contradictions(
        self,
        contradictions: list[dict[str, Any]],
        findings: list[dict[str, Any]] | None = None,
        batch_id: str = "reconcile_default",
    ) -> dict[str, Any]:
        """Reconcile contradictions into nuanced, evidence-aware interpretations."""
        try:
            reconciliations = []
            unresolved = []

            for contradiction in contradictions:
                result = self._reconcile_single(contradiction, findings or [])
                if result.get("confidence", 0) < 0.4:
                    unresolved.append(contradiction.get("contradiction_id", "unknown"))
                    self._create_review_checkpoint(contradiction, result)
                reconciliations.append(result)

            output = {
                "reconciliation_batch_id": batch_id,
                "reconciliations": reconciliations,
                "unresolved_tensions": unresolved,
                "research_gaps": self._extract_research_gaps(reconciliations),
                "summary": {
                    "total_contradictions": len(contradictions),
                    "reconciled": len(reconciliations) - len(unresolved),
                    "unresolved": len(unresolved),
                    "research_questions_generated": sum(
                        len(r.get("research_questions", [])) for r in reconciliations
                    ),
                },
                "created_at": datetime.utcnow().isoformat(),
            }

            self.reconciliation_manager.save_reconciliation(batch_id, output)
            return output

        except Exception as exc:
            logger.error("Contradiction reconciliation failed: %s", exc)
            return {"status": "error", "error": str(exc)}

    def _reconcile_single(
        self, contradiction: dict[str, Any], findings: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Reconcile a single contradiction."""
        affected_finding_ids = contradiction.get("affected_findings", [])
        description = contradiction.get("description", "")

        participant_groups = self._identify_participant_groups(affected_finding_ids, findings)
        factors = self._determine_factors(contradiction, participant_groups, findings)
        interpretation = self._build_interpretation(contradiction, participant_groups, factors)
        research_questions = self._generate_research_questions(contradiction, factors)
        confidence = self._calculate_confidence(contradiction, participant_groups, factors)

        return {
            "reconciliation_id": (
                f"RECON_{contradiction.get('contradiction_id', 'unknown')}"
            ),
            "contradiction_id": contradiction.get("contradiction_id", ""),
            "tension_description": description,
            "participant_groups": participant_groups,
            "possible_explanations": [
                self._explain_factor(factor, contradiction) for factor in factors
            ],
            "explanation_factors": factors,
            "reconciled_interpretation": interpretation,
            "design_implications": self._derive_design_implications(
                contradiction, participant_groups, factors
            ),
            "further_research_needed": confidence < 0.6,
            "research_questions": research_questions,
            "confidence": round(confidence, 2),
            "created_at": datetime.utcnow().isoformat(),
        }

    def _identify_participant_groups(
        self, finding_ids: list[str], findings: list[dict[str, Any]]
    ) -> dict[str, list[str]]:
        """Segment participants into groups based on their stance."""
        groups: dict[str, list[str]] = {"group_a": [], "group_b": []}

        relevant = [finding for finding in findings if finding.get("finding_id") in finding_ids]

        for finding in relevant:
            desc = finding.get("description", "").lower()
            participant_id = finding.get("participant_id", "unknown")
            positive_markers = [
                "liked",
                "preferred",
                "easy",
                "helpful",
                "good",
                "positive",
            ]
            if any(marker in desc for marker in positive_markers):
                groups["group_a"].append(participant_id)
            else:
                groups["group_b"].append(participant_id)

        groups["group_a"] = list(set(groups["group_a"]))
        groups["group_b"] = list(set(groups["group_b"]))

        return groups

    def _determine_factors(
        self,
        contradiction: dict[str, Any],
        participant_groups: dict[str, list[str]],
        findings: list[dict[str, Any]],
    ) -> list[str]:
        """Determine likely explanation factors for the contradiction."""
        factors = []
        desc = contradiction.get("description", "").lower()

        if len(participant_groups.get("group_a", [])) > 0 and len(
            participant_groups.get("group_b", [])
        ) > 0:
            factors.append("segment")

        if any(word in desc for word in ["experience", "familiar", "novice", "expert"]):
            factors.append("experience_level")

        if any(word in desc for word in ["task", "scenario", "context", "situation"]):
            factors.append("task_context")

        if any(word in desc for word in ["expect", "thought", "assumed", "believe"]):
            factors.append("product_expectation")

        if not factors:
            factors.append("evidence_limits")

        for factor in factors:
            if factor not in EXPLANATION_FACTORS:
                return ["other"]

        return factors

    def _explain_factor(self, factor: str, contradiction: dict[str, Any]) -> str:
        """Generate explanation for a factor."""
        del contradiction
        explanations = {
            "segment": (
                "Different user segments may have different needs and expectations, "
                "leading to divergent reactions to the same feature."
            ),
            "experience_level": (
                "Experience level likely mediates this reaction — more experienced users "
                "may have different mental models or workarounds."
            ),
            "task_context": (
                "The specific task context may have triggered different behaviors "
                "depending on what participants were trying to accomplish."
            ),
            "product_expectation": (
                "Participants may have had different expectations about how the product "
                "should work, leading to different evaluations of the same behavior."
            ),
            "evidence_limits": (
                "The contradiction may reflect insufficient evidence to draw a clear "
                "conclusion — more data is needed."
            ),
            "other": "Additional factors may be at play that require further investigation.",
        }
        return explanations.get(factor, explanations["other"])

    def _build_interpretation(
        self,
        contradiction: dict[str, Any],
        participant_groups: dict[str, list[str]],
        factors: list[str],
    ) -> str:
        """Build a nuanced reconciled interpretation."""
        description = contradiction.get("description", "this behavior")
        group_a_count = len(participant_groups.get("group_a", []))
        group_b_count = len(participant_groups.get("group_b", []))
        factors_text = ", ".join(factors)

        return (
            f"Regarding {description}: participants diverged in their reactions "
            f"({group_a_count} positive, {group_b_count} negative/neutral). "
            f"This tension appears driven by {factors_text}. "
            f"Rather than averaging these views, the design should account for both "
            f"perspectives — serving users who value the current behavior while "
            f"addressing concerns of those who do not."
        )

    def _generate_research_questions(
        self, contradiction: dict[str, Any], factors: list[str]
    ) -> list[str]:
        """Generate research questions to resolve the contradiction."""
        del contradiction
        questions = []

        if "segment" in factors:
            questions.append(
                "What specific user characteristics predict which reaction a user will have?"
            )
        if "experience_level" in factors:
            questions.append(
                "How does prior experience change user expectations and behavior here?"
            )
        if "task_context" in factors:
            questions.append(
                "Under what task conditions does the positive vs negative reaction emerge?"
            )
        if "evidence_limits" in factors:
            questions.append(
                "With a larger sample, does this contradiction persist or resolve?"
            )

        questions.append(
            "What design approach could serve both groups without compromising either?"
        )

        return questions

    def _derive_design_implications(
        self,
        contradiction: dict[str, Any],
        participant_groups: dict[str, list[str]],
        factors: list[str],
    ) -> list[str]:
        """Derive design implications that honor both sides."""
        del contradiction, participant_groups
        implications = [
            "Consider progressive disclosure or customization to serve both user groups"
        ]

        if "segment" in factors:
            implications.append("Explore segment-specific defaults or onboarding paths")
        if "experience_level" in factors:
            implications.append("Provide both novice-friendly and expert modes")

        return implications

    def _calculate_confidence(
        self,
        contradiction: dict[str, Any],
        participant_groups: dict[str, list[str]],
        factors: list[str],
    ) -> float:
        """Calculate confidence in the reconciliation."""
        del contradiction
        confidence = 0.5

        total = len(participant_groups.get("group_a", [])) + len(
            participant_groups.get("group_b", [])
        )
        if total >= 4:
            confidence += 0.2
        elif total >= 2:
            confidence += 0.1

        if "evidence_limits" not in factors and factors:
            confidence += 0.15

        return min(0.9, confidence)

    def _extract_research_gaps(self, reconciliations: list[dict[str, Any]]) -> list[str]:
        """Extract research gaps from reconciliations."""
        gaps = []
        for reconciliation in reconciliations:
            if reconciliation.get("further_research_needed"):
                gaps.extend(reconciliation.get("research_questions", [])[:1])
        return gaps

    def _create_review_checkpoint(
        self, contradiction: dict[str, Any], reconciliation: dict[str, Any]
    ) -> None:
        """Create review checkpoint for low-confidence reconciliations."""
        checkpoint_data = {
            "checkpoints": [
                {
                    "checkpoint_id": (
                        "RC_RECON_"
                        f"{contradiction.get('contradiction_id', 'unknown')}"
                    ),
                    "stage": "contradiction_reconciliation",
                    "reason": (
                        f"Low confidence ({reconciliation.get('confidence', 0)}) "
                        f"reconciliation for: {contradiction.get('description', '')[:60]}"
                    ),
                    "related_artifact_id": reconciliation.get("reconciliation_id", ""),
                    "artifact_type": "reconciliation",
                    "severity": "high",
                    "suggested_reviewer_action": (
                        "Review reconciliation logic and determine if additional "
                        "data is needed before proceeding"
                    ),
                    "status": "pending",
                    "created_at": datetime.utcnow().isoformat(),
                }
            ]
        }
        batch_id = f"recon_{contradiction.get('contradiction_id', 'unknown')}"
        self.review_manager.save_checkpoints(batch_id, checkpoint_data)
