"""Recommender skill implementation for generating actionable recommendations."""

import logging
from typing import Any, Optional, Dict, List
from datetime import datetime
from pathlib import Path
import json

from ut_analysis.models import (
    Finding,
    Recommendation,
    RecommendationSolution,
    ImplementationDetail,
)
from ut_analysis.state_management import (
    StateManager,
    FindingsManager,
    RecommendationsManager,
)

logger = logging.getLogger(__name__)


class RecommenderSkill:
    """Generates actionable recommendations from usability findings."""

    def __init__(
        self,
        state_manager: StateManager,
        findings_manager: FindingsManager | None = None,
        recommendations_manager: RecommendationsManager | None = None,
    ) -> None:
        self.state_manager = state_manager
        self.findings_manager = findings_manager or FindingsManager(
            state_manager.project_dir / "data"
        )
        self.recommendations_manager = recommendations_manager or RecommendationsManager(
            state_manager.project_dir / "data"
        )

    def generate_recommendations(
        self,
        findings_batch_id: str,
        recommendations_batch_id: str = "recs_default",
        recommendation_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generate recommendations from findings."""
        try:
            # Load findings
            findings_data = self.findings_manager.load_findings(findings_batch_id)
            findings = [Finding(**f) for f in findings_data.get("findings", [])]

            # Default recommendation config
            if recommendation_config is None:
                recommendation_config = {
                    "prioritization_method": "impact_effort",
                    "include_alternatives": True,
                    "target_audiences": ["design", "development", "product"],
                    "implementation_focus": "near_term",
                    "business_context": {
                        "timeline": "3_months",
                        "budget": "medium",
                        "resources": ["design", "frontend", "backend"],
                    },
                }

            # Generate recommendations
            recommendations = []
            for i, finding in enumerate(findings):
                rec = self._generate_recommendation(finding, i + 1, recommendation_config)
                recommendations.append(rec)

            # Create prioritization matrix
            prioritization = self._create_prioritization_matrix(recommendations)

            # Create implementation roadmap
            roadmap = self._create_implementation_roadmap(recommendations, recommendation_config)

            # Calculate statistics
            stats = self._calculate_recommendation_stats(recommendations)

            # Prepare result
            result = {
                "recommendations_batch_id": recommendations_batch_id,
                "recommendations": [rec.model_dump() for rec in recommendations],
                "prioritization_matrix": prioritization,
                "implementation_roadmap": roadmap,
                "recommendation_stats": stats,
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Save recommendations
            self.recommendations_manager.save_recommendations(recommendations_batch_id, result)

            # Update state
            self.state_manager.add_finding(f"{recommendations_batch_id}_recommendations", {
                "total_recommendations": len(recommendations),
                "critical_recommendations": sum(1 for r in recommendations if r.priority == "critical"),
                "implementation_phases": len(roadmap),
            })

            logger.info(f"Generated {len(recommendations)} recommendations in batch {recommendations_batch_id}")

            return result

        except Exception as e:
            logger.error(f"Recommendation generation failed: {e}")
            return {"status": "error", "error": str(e)}

    def _generate_recommendation(
        self, finding: Finding, rec_number: int, config: Dict[str, Any]
    ) -> Recommendation:
        """Generate a single recommendation from a finding."""
        # Determine priority based on severity
        priority = self._calculate_priority(finding)

        # Calculate impact and effort scores
        impact_score = self._calculate_impact_score(finding)
        effort_score = self._calculate_effort_score(finding)

        # Generate title and description
        title = self._generate_recommendation_title(finding)
        description = self._generate_recommendation_description(finding)

        # Generate rationale
        rationale = self._generate_rationale(finding)

        # Generate solutions
        solutions = self._generate_solutions(finding, config)

        # Define success metrics
        success_metrics = self._generate_success_metrics(finding)

        # Determine target audience
        target_audience = self._determine_target_audience(finding, config)

        # Determine timeline
        timeline = self._determine_timeline(priority, config)

        # Identify dependencies
        dependencies = self._identify_dependencies(finding)

        # Create recommendation
        recommendation = Recommendation(
            recommendation_id=f"REC_{rec_number:03d}",
            finding_id=finding.finding_id,
            title=title,
            description=description,
            priority=priority,
            impact_score=impact_score,
            effort_score=effort_score,
            rationale=rationale,
            solutions=solutions,
            success_metrics=success_metrics,
            target_audience=target_audience,
            timeline=timeline,
            dependencies=dependencies,
            generated_at=datetime.utcnow(),
        )

        return recommendation

    def _calculate_priority(self, finding: Finding) -> str:
        """Calculate recommendation priority based on finding severity."""
        severity = finding.severity or 0

        if severity >= 3:
            return "critical"
        elif severity >= 2:
            return "high"
        elif severity >= 1:
            return "medium"
        else:
            return "low"

    def _calculate_impact_score(self, finding: Finding) -> float:
        """Calculate impact score (1-10 scale)."""
        base_score = (finding.severity or 0) * 2.5  # Severity contributes 0-7.5

        # Frequency factor
        frequency_bonus = min(1.5, (finding.frequency or 1) * 0.1)

        # User impact factor
        user_impact_bonus = 0.5 if "user" in finding.description.lower() else 0

        return min(10.0, base_score + frequency_bonus + user_impact_bonus)

    def _calculate_effort_score(self, finding: Finding) -> float:
        """Calculate effort score (1-10 scale)."""
        # Base effort by finding type
        description = finding.description.lower()

        if any(word in description for word in ["redesign", "rebuild", "architect"]):
            base_effort = 8.0
        elif any(word in description for word in ["change", "update", "modify"]):
            base_effort = 5.0
        elif any(word in description for word in ["add", "include", "implement"]):
            base_effort = 6.0
        else:
            base_effort = 3.0

        # Complexity factors
        if "backend" in description or "database" in description:
            base_effort += 2.0
        if "multiple" in description or "system" in description:
            base_effort += 1.0

        return min(10.0, base_effort)

    def _generate_recommendation_title(self, finding: Finding) -> str:
        """Generate a concise recommendation title."""
        description = finding.description.lower()

        # Extract key action
        actions = {
            "redesign": "Redesign",
            "improve": "Improve",
            "add": "Add",
            "fix": "Fix",
            "simplify": "Simplify",
            "clarify": "Clarify",
            "enhance": "Enhance",
        }

        action = "Improve"
        for key, value in actions.items():
            if key in description:
                action = value
                break

        # Extract key element
        elements = ["checkout", "navigation", "search", "form", "button", "menu", "error"]
        element = "User Experience"
        for e in elements:
            if e in description:
                element = e.title()
                break

        return f"{action} {element} Experience"

    def _generate_recommendation_description(self, finding: Finding) -> str:
        """Generate detailed recommendation description."""
        description = finding.description

        # Add specific implementation guidance
        if "checkout" in description.lower():
            return f"Streamline the checkout process by addressing {description.lower()}. Implement clear visual hierarchy and reduce cognitive load."
        elif "navigation" in description.lower():
            return f"Enhance navigation clarity by addressing {description.lower()}. Use consistent labeling and logical grouping."
        elif "error" in description.lower():
            return f"Improve error handling by addressing {description.lower()}. Provide clear guidance and recovery options."
        else:
            return f"Address usability issue: {description}. Focus on user needs and clear communication."

    def _generate_rationale(self, finding: Finding) -> str:
        """Generate rationale for the recommendation."""
        severity = finding.severity or 0
        frequency = finding.frequency or 1

        rationale_parts = []

        if severity >= 3:
            rationale_parts.append("This critical issue significantly impacts user success")
        elif severity >= 2:
            rationale_parts.append("This high-priority issue affects user efficiency")

        if frequency > 1:
            rationale_parts.append(f"experienced by {frequency} participants")

        rationale_parts.append("and requires immediate attention to improve overall user experience")

        return " ".join(rationale_parts)

    def _generate_solutions(self, finding: Finding, config: Dict[str, Any]) -> List[RecommendationSolution]:
        """Generate solution options for the recommendation."""
        solutions = []

        # Primary solution
        primary = self._generate_primary_solution(finding)
        solutions.append(primary)

        # Alternative solutions if requested
        if config.get("include_alternatives", True):
            alternatives = self._generate_alternative_solutions(finding)
            solutions.extend(alternatives)

        return solutions

    def _generate_primary_solution(self, finding: Finding) -> RecommendationSolution:
        """Generate the primary recommended solution."""
        description = finding.description.lower()

        if "checkout" in description:
            approach = "Streamlined Checkout Flow"
            solution_desc = "Redesign checkout with progressive disclosure and clear validation"
            implementation = {
                "frontend": "Create modular checkout components",
                "backend": "Implement real-time validation APIs",
                "design": "Design simplified checkout wireframes",
            }
            effort = "3-4 weeks"
            impact = "20-25% increase in conversion"

        elif "navigation" in description:
            approach = "Enhanced Navigation System"
            solution_desc = "Implement clear information architecture with consistent navigation patterns"
            implementation = {
                "frontend": "Update navigation components",
                "design": "Create navigation system design",
                "content": "Audit and update navigation labels",
            }
            effort = "2-3 weeks"
            impact = "30-40% reduction in navigation errors"

        elif "error" in description:
            approach = "Comprehensive Error Handling"
            solution_desc = "Design error states with clear messaging and recovery options"
            implementation = {
                "frontend": "Create error state components",
                "backend": "Add error logging and handling",
                "content": "Write clear error messages",
            }
            effort = "1-2 weeks"
            impact = "50% improvement in error recovery"

        else:
            approach = "Targeted UX Improvement"
            solution_desc = f"Address the specific usability issue: {finding.description}"
            implementation = {
                "design": "Create solution wireframes",
                "frontend": "Implement UI changes",
                "testing": "Validate with user testing",
            }
            effort = "2-3 weeks"
            impact = "15-20% improvement in user satisfaction"

        return RecommendationSolution(
            approach=approach,
            description=solution_desc,
            implementation=ImplementationDetail(**implementation),
            effort_estimate=effort,
            impact_estimate=impact,
        )

    def _generate_alternative_solutions(self, finding: Finding) -> List[RecommendationSolution]:
        """Generate alternative solution approaches."""
        alternatives = []
        description = finding.description.lower()

        if "checkout" in description:
            # Alternative: Quick fix approach
            alternatives.append(RecommendationSolution(
                approach="Quick Validation Fix",
                description="Add immediate validation feedback without full redesign",
                implementation=ImplementationDetail(
                    frontend="Add form validation library",
                    backend="Update validation rules",
                ),
                effort_estimate="1 week",
                impact_estimate="10-15% improvement",
            ))

        elif "navigation" in description:
            # Alternative: Content-focused approach
            alternatives.append(RecommendationSolution(
                approach="Content Organization",
                description="Improve content structure and labeling before navigation changes",
                implementation=ImplementationDetail(
                    content="Audit and rewrite navigation labels",
                    design="Update content organization",
                ),
                effort_estimate="1-2 weeks",
                impact_estimate="20-25% improvement",
            ))

        return alternatives

    def _generate_success_metrics(self, finding: Finding) -> List[str]:
        """Generate success metrics for the recommendation."""
        metrics = []
        description = finding.description.lower()

        # Common metrics
        metrics.append("User satisfaction scores")
        metrics.append("Task completion rates")

        # Specific metrics based on finding type
        if "checkout" in description:
            metrics.extend([
                "Cart abandonment rate",
                "Conversion rate",
                "Checkout completion time",
            ])
        elif "navigation" in description:
            metrics.extend([
                "Navigation error rate",
                "Time to find information",
                "User flow completion",
            ])
        elif "error" in description:
            metrics.extend([
                "Error recovery rate",
                "Support ticket volume",
                "User frustration indicators",
            ])
        elif "search" in description:
            metrics.extend([
                "Search success rate",
                "Search query refinement",
                "Time to find results",
            ])

        return metrics

    def _determine_target_audience(self, finding: Finding, config: Dict[str, Any]) -> str:
        """Determine primary target audience for the recommendation."""
        audiences = config.get("target_audiences", ["design"])

        description = finding.description.lower()

        if "backend" in description or "api" in description or "database" in description:
            return "development"
        elif "design" in description or "ui" in description or "ux" in description:
            return "design"
        elif "content" in description or "copy" in description or "message" in description:
            return "content"
        elif "process" in description or "workflow" in description:
            return "product"
        else:
            return audiences[0] if audiences else "design"

    def _determine_timeline(self, priority: str, config: Dict[str, Any]) -> str:
        """Determine implementation timeline."""
        business_context = config.get("business_context", {})
        timeline = business_context.get("timeline", "3_months")

        if priority == "critical":
            return "immediate"
        elif priority == "high":
            return "short_term"
        elif priority == "medium":
            return "medium_term"
        else:
            return "long_term"

    def _identify_dependencies(self, finding: Finding) -> List[str]:
        """Identify dependencies for the recommendation."""
        dependencies = []
        description = finding.description.lower()

        if "backend" in description:
            dependencies.append("Backend development team")
        if "design" in description:
            dependencies.append("Design team review")
        if "content" in description:
            dependencies.append("Content team")
        if "testing" in description:
            dependencies.append("QA testing")

        return dependencies

    def _create_prioritization_matrix(self, recommendations: List[Recommendation]) -> Dict[str, List[str]]:
        """Create impact vs effort prioritization matrix."""
        matrix = {
            "high_impact_low_effort": [],
            "high_impact_high_effort": [],
            "low_impact_low_effort": [],
            "low_impact_high_effort": [],
        }

        for rec in recommendations:
            impact_high = rec.impact_score >= 7.0
            effort_low = rec.effort_score <= 5.0

            if impact_high and effort_low:
                matrix["high_impact_low_effort"].append(rec.recommendation_id)
            elif impact_high and not effort_low:
                matrix["high_impact_high_effort"].append(rec.recommendation_id)
            elif not impact_high and effort_low:
                matrix["low_impact_low_effort"].append(rec.recommendation_id)
            else:
                matrix["low_impact_high_effort"].append(rec.recommendation_id)

        return matrix

    def _create_implementation_roadmap(
        self, recommendations: List[Recommendation], config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create phased implementation roadmap."""
        roadmap = {}

        # Group by timeline
        phases = {
            "immediate": [],
            "short_term": [],
            "medium_term": [],
            "long_term": [],
        }

        for rec in recommendations:
            phases[rec.timeline].append(rec.recommendation_id)

        # Create phase details
        phase_details = {
            "immediate": {
                "duration_weeks": 4,
                "resources_needed": ["design", "frontend"],
                "expected_impact": "25% improvement",
            },
            "short_term": {
                "duration_weeks": 8,
                "resources_needed": ["design", "frontend", "backend"],
                "expected_impact": "40% improvement",
            },
            "medium_term": {
                "duration_weeks": 16,
                "resources_needed": ["design", "frontend", "backend", "testing"],
                "expected_impact": "60% improvement",
            },
            "long_term": {
                "duration_weeks": 32,
                "resources_needed": ["design", "frontend", "backend", "testing", "content"],
                "expected_impact": "80% improvement",
            },
        }

        for phase, rec_ids in phases.items():
            if rec_ids:  # Only include phases with recommendations
                roadmap[f"phase_{phase.replace('_', '')}"] = {
                    "recommendations": rec_ids,
                    **phase_details[phase],
                }

        return roadmap

    def _calculate_recommendation_stats(self, recommendations: List[Recommendation]) -> Dict[str, Any]:
        """Calculate recommendation generation statistics."""
        total_recs = len(recommendations)

        # Count by priority
        priority_counts = {}
        for rec in recommendations:
            priority_counts[rec.priority] = priority_counts.get(rec.priority, 0) + 1

        # Count by audience
        audience_counts = {}
        for rec in recommendations:
            audience_counts[rec.target_audience] = audience_counts.get(rec.target_audience, 0) + 1

        # Calculate averages
        avg_impact = sum(r.impact_score for r in recommendations) / total_recs if total_recs > 0 else 0
        avg_effort = sum(r.effort_score for r in recommendations) / total_recs if total_recs > 0 else 0

        # Implementation coverage
        implementation_coverage = sum(1 for r in recommendations if r.solutions) / total_recs * 100 if total_recs > 0 else 0

        return {
            "total_recommendations": total_recs,
            "by_priority": priority_counts,
            "by_audience": audience_counts,
            "average_impact_score": round(avg_impact, 1),
            "average_effort_score": round(avg_effort, 1),
            "implementation_coverage": round(implementation_coverage, 1),
        }
