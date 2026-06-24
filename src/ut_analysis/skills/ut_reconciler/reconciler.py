"""Reconciler skill implementation for producing nuanced contradiction reconciliations."""

import logging
from typing import Any, Optional
from datetime import datetime
from collections import defaultdict

from ut_analysis.models import (
    Reconciliation,
    ReconciliationReport,
    HumanReviewCheckpoint,
)
from ut_analysis.state_management import (
    StateManager,
    ContradictionsManager,
    SynthesisManager,
    ReconciliationManager,
    ReviewCheckpointManager,
)

logger = logging.getLogger(__name__)

DEFAULT_RECONCILIATION_CONFIG = {
    "include_participant_metadata": True,
    "generate_research_questions": True,
    "min_confidence_threshold": 0.5,
    "max_unresolved_allowed": 3,
}


class ReconcilerSkill:
    """Reconciles contradictions into nuanced, context-aware interpretations."""

    def __init__(
        self,
        state_manager: StateManager,
        contradictions_manager: ContradictionsManager | None = None,
        synthesis_manager: SynthesisManager | None = None,
        reconciliation_manager: "ReconciliationManager | None" = None,
        review_manager: "ReviewCheckpointManager | None" = None,
    ) -> None:
        self.state_manager = state_manager
        self.contradictions_manager = contradictions_manager or ContradictionsManager(
            state_manager.project_dir / "data"
        )
        self.synthesis_manager = synthesis_manager or SynthesisManager(
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
        contradictions_batch_id: str,
        synthesis_batch_id: Optional[str] = None,
        reconciliation_batch_id: str = "recon_default",
        reconciliation_config: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Reconcile contradictions into nuanced interpretations.

        Args:
            contradictions_batch_id: ID of the contradictions batch to reconcile.
            synthesis_batch_id: Optional synthesis batch for theme context.
            reconciliation_batch_id: ID for this reconciliation output.
            reconciliation_config: Optional configuration overrides.

        Returns:
            Structured reconciliation report as a dictionary.
        """
        try:
            config = {**DEFAULT_RECONCILIATION_CONFIG, **(reconciliation_config or {})}

            # Load contradictions
            contra_data = self.contradictions_manager.load_contradictions(
                contradictions_batch_id
            )
            contradictions = contra_data.get("contradictions", [])

            if not contradictions:
                return {
                    "status": "error",
                    "error": "No contradictions found to reconcile",
                }

            # Optionally load synthesis for theme context
            themes_context: dict[str, Any] = {}
            if synthesis_batch_id:
                try:
                    synthesis_data = self.synthesis_manager.load_synthesis(
                        synthesis_batch_id
                    )
                    themes_context = self._extract_themes_context(synthesis_data)
                except FileNotFoundError:
                    logger.warning(
                        f"Synthesis {synthesis_batch_id} not found; proceeding without theme context"
                    )

            # Reconcile each contradiction
            reconciliations: list[Reconciliation] = []
            unresolved: list[str] = []
            review_checkpoints: list[HumanReviewCheckpoint] = []
            recon_counter = 1

            for contradiction in contradictions:
                result = self._reconcile_single(
                    contradiction, themes_context, recon_counter, config
                )

                if result is None:
                    unresolved.append(contradiction.get("contradiction_id", f"unknown_{recon_counter}"))
                else:
                    reconciliations.append(result)

                    # Check for review checkpoint need
                    if self._needs_review(result, contradiction, config):
                        checkpoint = self._create_review_checkpoint(result, contradiction)
                        review_checkpoints.append(checkpoint)

                recon_counter += 1

            # Identify research gaps across all reconciliations
            research_gaps = self._identify_research_gaps(reconciliations, contradictions)

            # Build report
            report = ReconciliationReport(
                reconciliation_batch_id=reconciliation_batch_id,
                source_contradictions_id=contradictions_batch_id,
                reconciliations=reconciliations,
                unresolved_tensions=unresolved,
                research_gaps=research_gaps,
                summary=self._calculate_summary(reconciliations, unresolved, research_gaps),
            )

            # Persist results
            result_dict = report.model_dump()
            result_dict["review_checkpoints"] = [cp.model_dump() for cp in review_checkpoints]
            result_dict["timestamp"] = datetime.utcnow().isoformat()

            self.reconciliation_manager.save_reconciliation(
                reconciliation_batch_id, result_dict
            )

            # Save review checkpoints
            if review_checkpoints:
                self.review_manager.save_checkpoints(
                    f"{reconciliation_batch_id}_review",
                    {"checkpoints": [cp.model_dump() for cp in review_checkpoints]},
                )

            # Update pipeline state
            self.state_manager.add_finding(
                f"{reconciliation_batch_id}_reconciliation",
                {
                    "total_reconciled": len(reconciliations),
                    "unresolved_count": len(unresolved),
                    "research_gaps_found": len(research_gaps),
                    "human_review_needed": len(review_checkpoints) > 0,
                },
            )

            logger.info(
                f"Reconciled {len(reconciliations)} contradictions, "
                f"{len(unresolved)} unresolved, "
                f"{len(research_gaps)} research gaps identified"
            )

            return result_dict

        except Exception as e:
            logger.error(f"Reconciliation failed: {e}")
            return {"status": "error", "error": str(e)}

    def _reconcile_single(
        self,
        contradiction: dict[str, Any],
        themes_context: dict[str, Any],
        recon_id: int,
        config: dict[str, Any],
    ) -> Optional[Reconciliation]:
        """Reconcile a single contradiction."""
        contra_id = contradiction.get("contradiction_id", f"CONTRA_{recon_id:03d}")
        evidence = contradiction.get("evidence", {})
        analysis = contradiction.get("analysis", {})
        severity = contradiction.get("severity", "low")

        # Extract participant groups from evidence
        participant_agreement = evidence.get("participant_agreement", {})
        participant_groups = self._segment_participants(participant_agreement)

        # If we can't form meaningful groups, it may be unresolvable
        if not participant_groups or all(
            len(v) < 1 for v in participant_groups.values()
        ):
            if severity == "high":
                return None  # Mark as unresolved
            # For low-severity, create a minimal reconciliation
            participant_groups = {"group_a": list(participant_agreement.keys())}

        # Generate explanations
        possible_explanations = self._generate_explanations(
            contradiction, participant_groups, themes_context
        )

        # Generate design implication
        design_implication = self._generate_design_implication(
            contradiction, participant_groups, possible_explanations
        )

        # Determine if this changes the original finding
        changes_finding = self._assess_finding_change(
            contradiction, participant_groups
        )

        # Generate research questions if configured
        research_questions: list[str] = []
        if config.get("generate_research_questions"):
            research_questions = self._generate_research_questions(
                contradiction, participant_groups, possible_explanations
            )

        # Identify related themes
        theme_ids = self._find_related_themes(contradiction, themes_context)

        # Calculate confidence
        confidence = self._calculate_reconciliation_confidence(
            participant_groups, possible_explanations, evidence
        )

        # Generate tension description
        tension_description = self._generate_tension_description(
            contradiction, participant_groups
        )

        return Reconciliation(
            reconciliation_id=f"RECON_{recon_id:03d}",
            contradiction_id=contra_id,
            theme_ids=theme_ids,
            tension_description=tension_description,
            participant_groups=participant_groups,
            possible_explanations=possible_explanations,
            design_implication=design_implication,
            changes_original_finding=changes_finding,
            further_research_needed=len(research_questions) > 0,
            research_questions=research_questions,
            confidence=confidence,
        )

    def _segment_participants(
        self, participant_agreement: dict[str, str]
    ) -> dict[str, list[str]]:
        """Segment participants into groups based on their outcomes."""
        groups: dict[str, list[str]] = defaultdict(list)
        for participant, outcome in participant_agreement.items():
            groups[outcome].append(participant)
        return dict(groups)

    def _generate_explanations(
        self,
        contradiction: dict[str, Any],
        participant_groups: dict[str, list[str]],
        themes_context: dict[str, Any],
    ) -> list[str]:
        """Generate possible explanations for the contradiction."""
        explanations = []
        analysis = contradiction.get("analysis", {})
        possible_causes = analysis.get("possible_causes", [])

        # Include existing causes from contradiction analysis
        explanations.extend(possible_causes)

        # Add context-aware explanations based on group sizes
        group_sizes = {k: len(v) for k, v in participant_groups.items()}
        if len(group_sizes) == 2:
            sizes = list(group_sizes.values())
            if max(sizes) > 2 * min(sizes):
                explanations.append(
                    "Majority-minority split suggests a specific user segment "
                    "has different needs or context"
                )
            else:
                explanations.append(
                    "Even split suggests a fundamental design tension "
                    "requiring both approaches to be supported"
                )

        # Add explanations from contradiction type
        contra_type = contradiction.get("type", "")
        if contra_type == "participant_disagreement":
            explanations.append(
                "Individual differences in prior experience or mental models "
                "may explain divergent outcomes"
            )
        elif contra_type == "temporal_inconsistency":
            explanations.append(
                "Learning effects or fatigue during session may account "
                "for temporal changes in behavior"
            )

        return explanations[:5]  # Cap at 5 explanations

    def _generate_design_implication(
        self,
        contradiction: dict[str, Any],
        participant_groups: dict[str, list[str]],
        explanations: list[str],
    ) -> str:
        """Generate a design implication that honors the tension."""
        group_count = len(participant_groups)
        description = contradiction.get("description", "")

        if group_count == 2:
            groups = list(participant_groups.keys())
            return (
                f"Design should accommodate both '{groups[0]}' and '{groups[1]}' "
                f"perspectives. Consider progressive disclosure or user-configurable "
                f"behavior rather than a one-size-fits-all approach."
            )
        elif group_count > 2:
            return (
                "Multiple distinct user needs identified. Consider segmented "
                "experiences or adaptive interfaces that respond to user behavior patterns."
            )
        else:
            return (
                f"Contradiction in '{description}' suggests underlying "
                "complexity requiring further investigation before committing to a design direction."
            )

    def _assess_finding_change(
        self,
        contradiction: dict[str, Any],
        participant_groups: dict[str, list[str]],
    ) -> bool:
        """Assess whether the reconciliation changes the original finding."""
        # If the contradiction is high severity and groups are balanced, it changes the finding
        severity = contradiction.get("severity", "low")
        if severity == "high":
            group_sizes = [len(v) for v in participant_groups.values()]
            if group_sizes and max(group_sizes) - min(group_sizes) <= 1:
                return True

        return False

    def _generate_research_questions(
        self,
        contradiction: dict[str, Any],
        participant_groups: dict[str, list[str]],
        explanations: list[str],
    ) -> list[str]:
        """Generate follow-up research questions."""
        questions = []
        description = contradiction.get("description", "")

        # Question about group differences
        if len(participant_groups) >= 2:
            groups = list(participant_groups.keys())
            questions.append(
                f"What characteristics distinguish '{groups[0]}' users "
                f"from '{groups[1]}' users in this context?"
            )

        # Question about unexamined variables
        questions.append(
            f"What environmental or experiential factors predict "
            f"user position on: {description[:80]}?"
        )

        # Question about design interventions
        if explanations:
            questions.append(
                f"If '{explanations[0]}' is the cause, what intervention would resolve the tension?"
            )

        return questions[:3]

    def _find_related_themes(
        self,
        contradiction: dict[str, Any],
        themes_context: dict[str, Any],
    ) -> list[str]:
        """Find themes related to this contradiction."""
        affected = contradiction.get("affected_findings", [])
        related_themes = []

        # Check if any affected findings map to known themes
        for theme_id, theme_findings in themes_context.items():
            if any(f in theme_findings for f in affected):
                related_themes.append(theme_id)

        return related_themes

    def _calculate_reconciliation_confidence(
        self,
        participant_groups: dict[str, list[str]],
        explanations: list[str],
        evidence: dict[str, Any],
    ) -> float:
        """Calculate confidence in the reconciliation."""
        confidence = 0.5  # Base confidence

        # More participants = higher confidence
        total_participants = sum(len(v) for v in participant_groups.values())
        confidence += min(total_participants * 0.05, 0.2)

        # More explanations = slightly higher (we understand it better)
        confidence += min(len(explanations) * 0.05, 0.15)

        # Consistency score from evidence boosts confidence
        consistency = evidence.get("consistency_score", 0.5)
        # Lower consistency = more genuine contradiction = reconciliation is more needed
        if consistency < 0.5:
            confidence += 0.1

        return max(0.0, min(1.0, confidence))

    def _generate_tension_description(
        self,
        contradiction: dict[str, Any],
        participant_groups: dict[str, list[str]],
    ) -> str:
        """Generate a clear description of what is in tension."""
        base_desc = contradiction.get("description", "Unknown tension")
        groups = list(participant_groups.keys())

        if len(groups) == 2:
            return (
                f"{base_desc} — participants split between "
                f"'{groups[0]}' ({len(participant_groups[groups[0]])} participants) "
                f"and '{groups[1]}' ({len(participant_groups[groups[1]])} participants)"
            )

        return base_desc

    def _needs_review(
        self,
        reconciliation: Reconciliation,
        contradiction: dict[str, Any],
        config: dict[str, Any],
    ) -> bool:
        """Determine if reconciliation needs human review."""
        threshold = config.get("min_confidence_threshold", 0.5)

        # Low confidence reconciliation
        if reconciliation.confidence < threshold:
            return True

        # High-severity contradiction that changes findings
        if contradiction.get("severity") == "high" and reconciliation.changes_original_finding:
            return True

        # Very small participant groups make segmentation unreliable
        min_group_size = min(
            (len(v) for v in reconciliation.participant_groups.values()),
            default=0,
        )
        if min_group_size < 2:
            return True

        return False

    def _create_review_checkpoint(
        self,
        reconciliation: Reconciliation,
        contradiction: dict[str, Any],
    ) -> HumanReviewCheckpoint:
        """Create a human review checkpoint for a reconciliation."""
        severity = contradiction.get("severity", "medium")

        return HumanReviewCheckpoint(
            checkpoint_id=f"RC_{reconciliation.reconciliation_id}",
            stage="post_reconciliation",
            reason=(
                f"Reconciliation confidence {reconciliation.confidence:.2f} — "
                f"verify interpretation of contradiction"
            ),
            related_artifact_id=reconciliation.reconciliation_id,
            artifact_type="reconciliation",
            severity=severity if severity in ("critical", "high", "medium", "low") else "medium",
            suggested_reviewer_action=(
                f"Review reconciliation of '{reconciliation.tension_description[:80]}'. "
                f"Verify participant group segmentation and design implication."
            ),
        )

    def _extract_themes_context(
        self, synthesis_data: dict[str, Any]
    ) -> dict[str, list[str]]:
        """Extract theme-to-finding mapping from synthesis data."""
        context: dict[str, list[str]] = {}
        for insight in synthesis_data.get("insights", []):
            theme = insight.get("theme", "")
            finding_ids = insight.get("evidence", {}).get("finding_ids", [])
            if theme:
                context[theme] = finding_ids
        return context

    def _identify_research_gaps(
        self,
        reconciliations: list[Reconciliation],
        contradictions: list[dict[str, Any]],
    ) -> list[str]:
        """Identify research gaps across all reconciliations."""
        gaps: list[str] = []

        # Gaps from low-confidence reconciliations
        low_confidence = [r for r in reconciliations if r.confidence < 0.5]
        if low_confidence:
            gaps.append(
                f"{len(low_confidence)} reconciliation(s) have low confidence — "
                "additional participant data needed"
            )

        # Gaps from small participant groups
        small_groups = []
        for recon in reconciliations:
            for group, members in recon.participant_groups.items():
                if len(members) < 2:
                    small_groups.append(group)
        if small_groups:
            gaps.append(
                f"Participant segments too small for reliable analysis: "
                f"{', '.join(sorted(set(small_groups))[:3])}"
            )

        # Gaps from unresolved contradictions
        if len(contradictions) > len(reconciliations):
            unresolved = len(contradictions) - len(reconciliations)
            gaps.append(
                f"{unresolved} contradiction(s) could not be reconciled — "
                "may require different research methodology"
            )

        # Aggregate research questions as gaps
        all_questions = []
        for recon in reconciliations:
            all_questions.extend(recon.research_questions)
        if all_questions:
            gaps.append(
                f"{len(all_questions)} follow-up research question(s) generated"
            )

        return gaps

    def _calculate_summary(
        self,
        reconciliations: list[Reconciliation],
        unresolved: list[str],
        research_gaps: list[str],
    ) -> dict[str, Any]:
        """Calculate summary statistics."""
        return {
            "total_reconciled": len(reconciliations),
            "total_unresolved": len(unresolved),
            "changes_original_findings": sum(
                1 for r in reconciliations if r.changes_original_finding
            ),
            "further_research_needed": sum(
                1 for r in reconciliations if r.further_research_needed
            ),
            "research_gaps_count": len(research_gaps),
            "average_confidence": (
                sum(r.confidence for r in reconciliations) / len(reconciliations)
                if reconciliations
                else 0.0
            ),
        }
