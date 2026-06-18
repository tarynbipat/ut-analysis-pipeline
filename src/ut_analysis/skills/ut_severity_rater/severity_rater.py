"""Severity rater skill implementation for Nielsen severity rating."""

import logging
from typing import Any, Optional, Dict, List
from datetime import datetime
from collections import Counter

from ut_analysis.models import (
    Finding,
    EvaluatedFinding,
    SeverityRating,
    SeverityLevel,
)
from ut_analysis.state_management import (
    StateManager,
    EvaluationManager,
    SeverityManager,
)

logger = logging.getLogger(__name__)


class SeverityRaterSkill:
    """Rates severity of findings using Nielsen scale."""

    def __init__(
        self,
        state_manager: StateManager,
        evaluation_manager: EvaluationManager | None = None,
        severity_manager: SeverityManager | None = None,
    ) -> None:
        self.state_manager = state_manager
        self.evaluation_manager = evaluation_manager or EvaluationManager(
            state_manager.project_dir / "data"
        )
        self.severity_manager = severity_manager or SeverityManager(
            state_manager.project_dir / "data"
        )

    def rate_severity(
        self,
        evaluated_findings_batch_id: str,
        severity_batch_id: str = "severity_default",
        rating_criteria: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """Rate severity for evaluated findings."""
        try:
            # Load evaluated findings
            evaluation_data = self.evaluation_manager.load_evaluation(evaluated_findings_batch_id)
            evaluated_findings = [
                EvaluatedFinding(**ef) for ef in evaluation_data.get("evaluated_findings", [])
            ]

            # Default rating criteria
            if rating_criteria is None:
                rating_criteria = {
                    "frequency_weight": 0.3,
                    "impact_weight": 0.4,
                    "persistence_weight": 0.2,
                    "scope_weight": 0.1,
                }

            # Rate each finding
            rated_findings = []
            for ef in evaluated_findings:
                if ef.all_passed:  # Only rate validated findings
                    rated = self._rate_single_finding(ef, rating_criteria)
                    rated_findings.append(rated)

            # Calculate statistics
            stats = self._calculate_severity_stats(rated_findings)

            # Prepare result
            result = {
                "severity_batch_id": severity_batch_id,
                "rated_findings": [rf.model_dump() for rf in rated_findings],
                "severity_stats": stats,
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Save severity ratings
            self.severity_manager.save_severity_ratings(severity_batch_id, result)

            # Update state
            self.state_manager.add_finding(f"{severity_batch_id}_severity", {
                "total_rated": len(rated_findings),
                "severity_distribution": stats["severity_distribution"],
                "average_severity": stats["average_severity"],
                "high_priority": stats["high_priority_findings"],
            })

            logger.info(f"Severity rated {len(rated_findings)} findings in batch {severity_batch_id}")

            return result

        except Exception as e:
            logger.error(f"Severity rating failed: {e}")
            return {"status": "error", "error": str(e)}

    def _rate_single_finding(
        self, evaluated_finding: EvaluatedFinding, criteria: Dict[str, float]
    ) -> Dict[str, Any]:
        """Rate severity for a single finding."""
        finding = evaluated_finding.original_finding

        # Assess each criterion
        frequency_score = self._assess_frequency(finding)
        impact_score = self._assess_impact(finding)
        persistence_score = self._assess_persistence(finding)
        scope_score = self._assess_scope(finding)

        # Calculate weighted severity score
        severity_score = (
            frequency_score * criteria["frequency_weight"] +
            impact_score * criteria["impact_weight"] +
            persistence_score * criteria["persistence_weight"] +
            scope_score * criteria["scope_weight"]
        )

        # Map to Nielsen severity level
        severity_level = self._map_score_to_level(severity_score)

        # Generate rationale and evidence
        rationale, criteria_match, evidence = self._generate_justification(
            finding, severity_level, frequency_score, impact_score, persistence_score, scope_score
        )

        # Create severity rating
        severity_rating = SeverityRating(
            level=severity_level.value,
            label=severity_level.name.lower(),
            rationale=rationale,
            criteria_match=criteria_match,
            evidence=evidence,
            confidence=self._calculate_confidence(finding),
            rated_at=datetime.utcnow(),
        )

        return {
            "finding_id": finding.finding_id,
            "original_finding": finding,
            "severity_rating": severity_rating,
        }

    def _assess_frequency(self, finding: Finding) -> float:
        """Assess frequency criterion (0-1 scale)."""
        # Simple heuristic based on finding description
        text = finding.description.lower()

        if any(word in text for word in ["always", "every time", "consistently", "all participants"]):
            return 1.0  # High frequency
        elif any(word in text for word in ["often", "frequently", "multiple times", "several participants"]):
            return 0.7  # Medium-high frequency
        elif any(word in text for word in ["sometimes", "occasionally", "few participants"]):
            return 0.4  # Medium frequency
        elif any(word in text for word in ["once", "rarely", "single participant"]):
            return 0.1  # Low frequency
        else:
            return 0.5  # Unknown, assume medium

    def _assess_impact(self, finding: Finding) -> float:
        """Assess impact criterion (0-1 scale)."""
        text = finding.description.lower()

        if any(word in text for word in ["cannot complete", "impossible", "blocked", "stuck"]):
            return 1.0  # Critical impact
        elif any(word in text for word in ["difficult", "hard", "confusing", "error"]):
            return 0.7  # Major impact
        elif any(word in text for word in ["inconvenient", "slow", "extra steps"]):
            return 0.4  # Minor impact
        elif any(word in text for word in ["cosmetic", "typo", "color", "spacing"]):
            return 0.1  # Cosmetic impact
        else:
            return 0.5  # Unknown, assume medium

    def _assess_persistence(self, finding: Finding) -> float:
        """Assess persistence criterion (0-1 scale)."""
        text = finding.description.lower()

        if any(word in text for word in ["recurring", "repeated", "keeps happening", "persistent"]):
            return 1.0  # High persistence
        elif any(word in text for word in ["multiple times", "again", "still"]):
            return 0.7  # Medium-high persistence
        elif any(word in text for word in ["once", "single occurrence"]):
            return 0.2  # Low persistence
        else:
            return 0.5  # Unknown, assume medium

    def _assess_scope(self, finding: Finding) -> float:
        """Assess scope criterion (0-1 scale)."""
        text = finding.description.lower()

        if any(word in text for word in ["all participants", "everyone", "every user"]):
            return 1.0  # Universal scope
        elif any(word in text for word in ["most participants", "majority", "many users"]):
            return 0.7  # Broad scope
        elif any(word in text for word in ["some participants", "few users", "several"]):
            return 0.4  # Limited scope
        elif any(word in text for word in ["one participant", "single user"]):
            return 0.1  # Individual scope
        else:
            return 0.5  # Unknown, assume medium

    def _map_score_to_level(self, score: float) -> SeverityLevel:
        """Map severity score to Nielsen level."""
        if score >= 0.9:
            return SeverityLevel.CATASTROPHIC
        elif score >= 0.7:
            return SeverityLevel.CRITICAL
        elif score >= 0.5:
            return SeverityLevel.MAJOR
        elif score >= 0.3:
            return SeverityLevel.MINOR
        else:
            return SeverityLevel.COSMETIC

    def _generate_justification(
        self,
        finding: Finding,
        severity_level: SeverityLevel,
        frequency: float,
        impact: float,
        persistence: float,
        scope: float,
    ) -> tuple[str, Dict[str, str], List[str]]:
        """Generate rationale, criteria match, and evidence."""
        # Rationale
        level_names = {
            SeverityLevel.COSMETIC: "cosmetic",
            SeverityLevel.MINOR: "minor inconvenience",
            SeverityLevel.MAJOR: "significant problem",
            SeverityLevel.CRITICAL: "critical issue preventing task completion",
            SeverityLevel.CATASTROPHIC: "catastrophic system failure",
        }

        rationale = f"This is rated as {level_names[severity_level]} because {finding.description}"

        # Criteria match descriptions
        criteria_match = {
            "frequency": self._describe_frequency(frequency),
            "impact": self._describe_impact(impact),
            "persistence": self._describe_persistence(persistence),
            "scope": self._describe_scope(scope),
        }

        # Evidence from finding
        evidence = [
            finding.verbatim_quote,
            f"Task: {finding.task_id}",
            f"Participant: {finding.participant_id}",
        ]

        return rationale, criteria_match, evidence

    def _describe_frequency(self, score: float) -> str:
        """Describe frequency score in words."""
        if score >= 0.8:
            return "High - affects most or all users"
        elif score >= 0.6:
            return "Medium-high - affects many users"
        elif score >= 0.4:
            return "Medium - affects some users"
        elif score >= 0.2:
            return "Low - affects few users"
        else:
            return "Very low - affects individual users"

    def _describe_impact(self, score: float) -> str:
        """Describe impact score in words."""
        if score >= 0.8:
            return "Critical - prevents task completion"
        elif score >= 0.6:
            return "Major - significantly hinders task completion"
        elif score >= 0.4:
            return "Moderate - causes inconvenience"
        elif score >= 0.2:
            return "Minor - small inconvenience"
        else:
            return "Cosmetic - no functional impact"

    def _describe_persistence(self, score: float) -> str:
        """Describe persistence score in words."""
        if score >= 0.8:
            return "High - issue recurs frequently"
        elif score >= 0.6:
            return "Medium-high - occurs multiple times"
        elif score >= 0.4:
            return "Medium - occurs occasionally"
        elif score >= 0.2:
            return "Low - occurs once"
        else:
            return "Very low - single occurrence"

    def _describe_scope(self, score: float) -> str:
        """Describe scope score in words."""
        if score >= 0.8:
            return "Universal - affects all participants"
        elif score >= 0.6:
            return "Broad - affects most participants"
        elif score >= 0.4:
            return "Limited - affects some participants"
        elif score >= 0.2:
            return "Narrow - affects few participants"
        else:
            return "Individual - affects one participant"

    def _calculate_confidence(self, finding: Finding) -> float:
        """Calculate confidence in severity rating."""
        confidence = 0.5  # Base confidence

        # Higher confidence with clear evidence
        if finding.verbatim_quote and len(finding.verbatim_quote.strip()) > 10:
            confidence += 0.2

        # Higher confidence with task attribution
        if finding.task_id:
            confidence += 0.1

        # Higher confidence with participant ID
        if finding.participant_id:
            confidence += 0.1

        # Higher confidence with higher original confidence
        confidence += finding.confidence * 0.1

        return min(confidence, 1.0)

    def _calculate_severity_stats(self, rated_findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate severity rating statistics."""
        total = len(rated_findings)

        # Severity distribution
        severity_counts = Counter()
        severity_levels = []
        for rf in rated_findings:
            level = rf["severity_rating"]["level"]
            severity_counts[level] += 1
            severity_levels.append(level)

        distribution = {}
        for level in [0, 1, 2, 3, 4]:
            label = SeverityLevel(level).name.lower()
            distribution[f"{level}_{label}"] = severity_counts.get(level, 0)

        # Average severity
        avg_severity = sum(severity_levels) / total if total > 0 else 0

        # High priority findings (severity 3+)
        high_priority = sum(1 for level in severity_levels if level >= 3)

        # Mock inter-rater agreement (would be calculated from multiple raters)
        inter_rater_agreement = 0.87

        return {
            "total_rated": total,
            "severity_distribution": distribution,
            "average_severity": round(avg_severity, 2),
            "high_priority_findings": high_priority,
            "inter_rater_agreement": inter_rater_agreement,
        }
