"""Evidence Critic skill implementation for challenging synthesis evidence quality."""

import logging
from typing import Any, Optional
from datetime import datetime

from ut_analysis.models import (
    EvidenceCritique,
    CriticReport,
    HumanReviewCheckpoint,
)
from ut_analysis.state_management import (
    StateManager,
    SynthesisManager,
    CriticManager,
    ReviewCheckpointManager,
)

logger = logging.getLogger(__name__)

# Default configuration for the critic
DEFAULT_CRITIC_CONFIG = {
    "min_participants_for_pattern": 3,
    "require_verbatim_quotes": True,
    "severity_justification_required": True,
    "flag_single_participant_themes": True,
    "confidence_threshold": 0.7,
    "max_severity_for_single_participant": 1,
}


class CriticSkill:
    """Reviews synthesis outputs and challenges evidence quality."""

    def __init__(
        self,
        state_manager: StateManager,
        synthesis_manager: SynthesisManager | None = None,
        critic_manager: "CriticManager | None" = None,
        review_manager: "ReviewCheckpointManager | None" = None,
    ) -> None:
        self.state_manager = state_manager
        self.synthesis_manager = synthesis_manager or SynthesisManager(
            state_manager.project_dir / "data"
        )
        self.critic_manager = critic_manager or CriticManager(
            state_manager.project_dir / "data"
        )
        self.review_manager = review_manager or ReviewCheckpointManager(
            state_manager.project_dir / "data"
        )

    def critique_synthesis(
        self,
        synthesis_batch_id: str,
        critic_batch_id: str = "critic_default",
        critic_config: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Critique a synthesis output for evidence quality issues.

        Args:
            synthesis_batch_id: ID of the synthesis batch to critique.
            critic_batch_id: ID for this critic batch output.
            critic_config: Optional configuration overrides.

        Returns:
            Structured critique report as a dictionary.
        """
        try:
            config = {**DEFAULT_CRITIC_CONFIG, **(critic_config or {})}

            # Load synthesis data
            synthesis_data = self.synthesis_manager.load_synthesis(synthesis_batch_id)
            insights = synthesis_data.get("insights", [])

            if not insights:
                return {
                    "status": "error",
                    "error": "No insights found in synthesis output",
                }

            # Run critique analysis on each insight
            critiques: list[EvidenceCritique] = []
            review_checkpoints: list[HumanReviewCheckpoint] = []
            critique_counter = 1

            for insight in insights:
                critique = self._critique_insight(insight, critique_counter, config)
                critiques.append(critique)

                # Generate review checkpoint if needed
                if critique.requires_human_review:
                    checkpoint = self._create_review_checkpoint(critique, insight)
                    review_checkpoints.append(checkpoint)

                critique_counter += 1

            # Calculate summary statistics
            summary = self._calculate_summary(critiques)

            # Determine overall quality
            overall_quality = self._assess_overall_quality(summary)

            # Build report
            report = CriticReport(
                critic_batch_id=critic_batch_id,
                source_synthesis_id=synthesis_batch_id,
                critiques=critiques,
                summary=summary,
                overall_evidence_quality=overall_quality,
                human_review_required=any(c.requires_human_review for c in critiques),
            )

            # Persist results
            result = report.model_dump()
            result["review_checkpoints"] = [cp.model_dump() for cp in review_checkpoints]
            result["timestamp"] = datetime.utcnow().isoformat()

            self.critic_manager.save_critique(critic_batch_id, result)

            # Save review checkpoints
            if review_checkpoints:
                self.review_manager.save_checkpoints(
                    f"{critic_batch_id}_review", 
                    {"checkpoints": [cp.model_dump() for cp in review_checkpoints]}
                )

            # Update pipeline state
            self.state_manager.add_finding(f"{critic_batch_id}_critique", {
                "total_critiqued": len(critiques),
                "weak_evidence_count": summary.get("weak_evidence", 0),
                "human_review_needed": report.human_review_required,
                "overall_quality": overall_quality,
            })

            logger.info(
                f"Critiqued {len(insights)} insights: "
                f"{summary.get('strong_evidence', 0)} strong, "
                f"{summary.get('weak_evidence', 0)} weak, "
                f"{summary.get('insufficient_evidence', 0)} insufficient"
            )

            return result

        except Exception as e:
            logger.error(f"Critique failed: {e}")
            return {"status": "error", "error": str(e)}

    def _critique_insight(
        self,
        insight: dict[str, Any],
        critique_id: int,
        config: dict[str, Any],
    ) -> EvidenceCritique:
        """Critique a single synthesis insight."""
        issues: list[str] = []
        unsupported_claims: list[str] = []
        overgeneralizations: list[str] = []
        missing_segments: list[str] = []

        evidence = insight.get("evidence", {})
        participant_count = evidence.get("participant_count", 0)
        finding_ids = evidence.get("finding_ids", [])
        severity = insight.get("severity", "low")
        title = insight.get("title", "")
        description = insight.get("description", "")

        min_for_pattern = config["min_participants_for_pattern"]

        # Check 1: Participant count vs. claim scope
        if participant_count < min_for_pattern and len(finding_ids) > 1:
            issues.append("insufficient_participant_count")
            overgeneralizations.append(
                f"Pattern claimed from {participant_count} participants "
                f"(minimum {min_for_pattern} required)"
            )

        # Check 2: Single participant driving high-severity claim
        if participant_count == 1 and severity in ("critical", "high"):
            max_sev = config["max_severity_for_single_participant"]
            issues.append("single_participant_high_severity")
            unsupported_claims.append(
                f"Severity '{severity}' assigned but only 1 participant supports it "
                f"(max justified: severity {max_sev})"
            )

        # Check 3: Absolute language in title/description
        absolute_terms = ["all users", "always", "never", "everyone", "no one", "widespread"]
        for term in absolute_terms:
            if term in title.lower() or term in description.lower():
                issues.append("absolute_language")
                overgeneralizations.append(
                    f"Absolute term '{term}' used with {participant_count} participants"
                )
                break

        # Check 4: Evidence count vs claim confidence
        if len(finding_ids) < 2 and config.get("flag_single_participant_themes"):
            issues.append("single_finding_theme")
            unsupported_claims.append(
                "Theme based on single finding — insufficient for pattern claim"
            )

        # Check 5: Severity distribution consistency
        severity_dist = evidence.get("severity_distribution", {})
        if severity_dist:
            sev_values = [int(k) for k in severity_dist.keys()]
            if sev_values:
                sev_range = max(sev_values) - min(sev_values)
                if sev_range >= 3:
                    issues.append("inconsistent_severity")
                    unsupported_claims.append(
                        f"Severity range of {sev_range} within single insight "
                        "suggests conflated issues"
                    )

        # Determine evidence strength
        evidence_strength = self._assess_evidence_strength(
            participant_count, len(finding_ids), len(issues), severity, config
        )

        # Calculate confidence
        confidence = self._calculate_confidence(
            participant_count, len(finding_ids), len(issues), evidence_strength
        )

        # Determine if human review is required
        requires_review = self._should_flag_for_review(
            evidence_strength, severity, confidence, config
        )

        # Generate revision recommendation
        revision = self._generate_revision_recommendation(
            issues, evidence_strength, participant_count, severity
        )

        review_reason = None
        if requires_review:
            review_reason = self._generate_review_reason(
                evidence_strength, severity, issues, confidence
            )

        return EvidenceCritique(
            critique_id=f"CRIT_{critique_id:03d}",
            target_type="insight",
            target_id=insight.get("insight_id", f"unknown_{critique_id}"),
            critique_summary=self._generate_critique_summary(
                insight, issues, evidence_strength
            ),
            evidence_strength=evidence_strength,
            issues_found=issues,
            unsupported_claims=unsupported_claims,
            overgeneralizations=overgeneralizations,
            missing_participant_segments=missing_segments,
            recommended_revision=revision,
            confidence_rating=confidence,
            requires_human_review=requires_review,
            review_reason=review_reason,
        )

    def _assess_evidence_strength(
        self,
        participant_count: int,
        finding_count: int,
        issue_count: int,
        severity: str,
        config: dict[str, Any],
    ) -> str:
        """Assess evidence strength based on multiple factors."""
        min_for_pattern = config["min_participants_for_pattern"]

        if participant_count >= min_for_pattern and finding_count >= 3 and issue_count == 0:
            return "strong"
        elif participant_count >= 2 and finding_count >= 2 and issue_count <= 1:
            return "moderate"
        elif participant_count >= 1 and finding_count >= 1 and issue_count <= 2:
            return "weak"
        else:
            return "insufficient"

    def _calculate_confidence(
        self,
        participant_count: int,
        finding_count: int,
        issue_count: int,
        evidence_strength: str,
    ) -> float:
        """Calculate confidence rating for the critique."""
        base_scores = {
            "strong": 0.9,
            "moderate": 0.7,
            "weak": 0.4,
            "insufficient": 0.2,
        }
        score = base_scores.get(evidence_strength, 0.5)

        # Adjust for participant count
        score += min(participant_count * 0.05, 0.1)

        # Penalize for issues
        score -= issue_count * 0.1

        return max(0.0, min(1.0, score))

    def _should_flag_for_review(
        self,
        evidence_strength: str,
        severity: str,
        confidence: float,
        config: dict[str, Any],
    ) -> bool:
        """Determine whether human review is required."""
        threshold = config["confidence_threshold"]

        # Always flag insufficient evidence
        if evidence_strength == "insufficient":
            return True

        # Flag weak evidence on high-severity items
        if evidence_strength == "weak" and severity in ("critical", "high"):
            return True

        # Flag when confidence is below threshold
        if confidence < threshold:
            return True

        return False

    def _generate_critique_summary(
        self,
        insight: dict[str, Any],
        issues: list[str],
        evidence_strength: str,
    ) -> str:
        """Generate a concise critique summary."""
        title = insight.get("title", "Unknown insight")
        if not issues:
            return f"'{title}' has {evidence_strength} evidence support — no issues found"

        issue_descriptions = {
            "insufficient_participant_count": "insufficient participant count",
            "single_participant_high_severity": "high severity from single participant",
            "absolute_language": "absolute language not supported by data",
            "single_finding_theme": "theme based on single finding",
            "inconsistent_severity": "inconsistent severity within group",
        }

        primary_issue = issue_descriptions.get(issues[0], issues[0])
        return f"'{title}' — {evidence_strength} evidence: {primary_issue}"

    def _generate_revision_recommendation(
        self,
        issues: list[str],
        evidence_strength: str,
        participant_count: int,
        severity: str,
    ) -> Optional[str]:
        """Generate specific revision guidance."""
        if not issues:
            return None

        recommendations = []

        if "insufficient_participant_count" in issues:
            recommendations.append(
                f"Downgrade from 'pattern' to 'observed in {participant_count} participant(s)'"
            )

        if "single_participant_high_severity" in issues:
            recommendations.append(
                f"Reduce severity from '{severity}' or add qualifying language"
            )

        if "absolute_language" in issues:
            recommendations.append(
                "Replace absolute language with qualified statements "
                "(e.g., 'some participants' instead of 'all users')"
            )

        if "inconsistent_severity" in issues:
            recommendations.append(
                "Consider splitting into separate insights with distinct severity levels"
            )

        return "; ".join(recommendations) if recommendations else None

    def _generate_review_reason(
        self,
        evidence_strength: str,
        severity: str,
        issues: list[str],
        confidence: float,
    ) -> str:
        """Generate explanation for why human review is needed."""
        reasons = []

        if evidence_strength in ("weak", "insufficient"):
            reasons.append(f"Evidence strength is '{evidence_strength}'")

        if severity in ("critical", "high"):
            reasons.append(f"Severity is '{severity}' — high-impact claim needs validation")

        if confidence < 0.5:
            reasons.append(f"Confidence rating is {confidence:.2f}")

        return "; ".join(reasons) if reasons else "Automated checks indicate review needed"

    def _create_review_checkpoint(
        self,
        critique: EvidenceCritique,
        insight: dict[str, Any],
    ) -> HumanReviewCheckpoint:
        """Create a human review checkpoint from a critique."""
        severity_map = {
            "insufficient": "critical",
            "weak": "high",
            "moderate": "medium",
            "strong": "low",
        }

        return HumanReviewCheckpoint(
            checkpoint_id=f"RC_{critique.critique_id}",
            stage="post_synthesis_critique",
            reason=critique.review_reason or "Evidence quality concern",
            related_artifact_id=critique.target_id,
            artifact_type="insight",
            severity=severity_map.get(critique.evidence_strength, "medium"),
            suggested_reviewer_action=(
                f"Review insight '{insight.get('title', '')}': "
                f"{critique.recommended_revision or 'Verify evidence manually'}"
            ),
        )

    def _calculate_summary(self, critiques: list[EvidenceCritique]) -> dict[str, Any]:
        """Calculate summary statistics for the critic report."""
        strength_counts = {"strong": 0, "moderate": 0, "weak": 0, "insufficient": 0}
        for critique in critiques:
            strength_counts[critique.evidence_strength] = (
                strength_counts.get(critique.evidence_strength, 0) + 1
            )

        return {
            "total_critiqued": len(critiques),
            "strong_evidence": strength_counts["strong"],
            "moderate_evidence": strength_counts["moderate"],
            "weak_evidence": strength_counts["weak"],
            "insufficient_evidence": strength_counts["insufficient"],
            "requires_human_review": sum(
                1 for c in critiques if c.requires_human_review
            ),
            "average_confidence": (
                sum(c.confidence_rating for c in critiques) / len(critiques)
                if critiques else 0.0
            ),
        }

    def _assess_overall_quality(self, summary: dict[str, Any]) -> str:
        """Assess overall evidence quality across all critiques."""
        total = summary.get("total_critiqued", 0)
        if total == 0:
            return "inadequate"

        strong_pct = summary.get("strong_evidence", 0) / total
        weak_pct = summary.get("weak_evidence", 0) / total
        insufficient_pct = summary.get("insufficient_evidence", 0) / total

        if strong_pct >= 0.7:
            return "high"
        elif strong_pct + summary.get("moderate_evidence", 0) / total >= 0.6:
            return "acceptable"
        elif insufficient_pct >= 0.3:
            return "inadequate"
        else:
            return "concerning"
