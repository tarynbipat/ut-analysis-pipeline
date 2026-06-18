"""Synthesizer skill implementation for synthesizing findings into insights."""

import logging
from typing import Any, Optional, Dict, List
from datetime import datetime
from collections import Counter, defaultdict

from ut_analysis.models import (
    Finding,
    SynthesisInsight,
    SynthesisRecommendation,
    SynthesisPattern,
    SynthesisEvidence,
)
from ut_analysis.state_management import (
    StateManager,
    HeuristicManager,
    SynthesisManager,
)

logger = logging.getLogger(__name__)


class SynthesizerSkill:
    """Synthesizes findings into actionable insights and recommendations."""

    def __init__(
        self,
        state_manager: StateManager,
        heuristic_manager: HeuristicManager | None = None,
        synthesis_manager: SynthesisManager | None = None,
    ) -> None:
        self.state_manager = state_manager
        self.heuristic_manager = heuristic_manager or HeuristicManager(
            state_manager.project_dir / "data"
        )
        self.synthesis_manager = synthesis_manager or SynthesisManager(
            state_manager.project_dir / "data"
        )

    def synthesize_findings(
        self,
        heuristic_batch_id: str,
        synthesis_batch_id: str = "synthesis_default",
        synthesis_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Synthesize findings into insights."""
        try:
            # Load heuristic mappings
            heuristic_data = self.heuristic_manager.load_heuristic_mappings(heuristic_batch_id)
            mapped_findings = heuristic_data.get("mapped_findings", [])

            # Default synthesis config
            if synthesis_config is None:
                synthesis_config = {
                    "grouping_method": "thematic",
                    "min_finding_threshold": 2,
                    "max_insights": 20,
                    "prioritization_weights": {
                        "severity": 0.4,
                        "frequency": 0.3,
                        "impact": 0.3,
                    },
                }

            # Group findings based on method
            if synthesis_config["grouping_method"] == "thematic":
                finding_groups = self._group_by_theme(mapped_findings)
            elif synthesis_config["grouping_method"] == "heuristic":
                finding_groups = self._group_by_heuristic(mapped_findings)
            else:
                finding_groups = self._group_by_theme(mapped_findings)

            # Generate insights from groups
            insights = []
            insight_counter = 1

            for group in finding_groups:
                if len(group) >= synthesis_config["min_finding_threshold"]:
                    insight = self._create_insight_from_group(
                        group, insight_counter, synthesis_config
                    )
                    insights.append(insight)
                    insight_counter += 1

                if len(insights) >= synthesis_config["max_insights"]:
                    break

            # Handle remaining individual findings
            processed_finding_ids = set()
            for insight in insights:
                processed_finding_ids.update(insight.evidence.finding_ids)

            remaining_findings = [
                mf for mf in mapped_findings
                if mf["finding_id"] not in processed_finding_ids
            ]

            for mf in remaining_findings[:synthesis_config["max_insights"] - len(insights)]:
                insight = self._create_individual_insight(mf, insight_counter)
                insights.append(insight)
                insight_counter += 1

            # Calculate synthesis statistics
            stats = self._calculate_synthesis_stats(insights, mapped_findings)

            # Prepare result
            result = {
                "synthesis_batch_id": synthesis_batch_id,
                "insights": [insight.model_dump() for insight in insights],
                "synthesis_stats": stats,
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Save synthesis results
            self.synthesis_manager.save_synthesis(synthesis_batch_id, result)

            # Update state
            self.state_manager.add_finding(f"{synthesis_batch_id}_synthesis", {
                "total_insights": len(insights),
                "critical_insights": sum(1 for i in insights if i.severity == "critical"),
                "themes_covered": len(set(i.theme for i in insights)),
            })

            logger.info(f"Synthesized {len(insights)} insights from {len(mapped_findings)} findings")

            return result

        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            return {"status": "error", "error": str(e)}

    def _group_by_theme(self, mapped_findings: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """Group findings by thematic similarity."""
        groups = []

        # Simple thematic grouping based on finding descriptions
        processed = set()

        for i, mf in enumerate(mapped_findings):
            if mf["finding_id"] in processed:
                continue

            group = [mf]
            processed.add(mf["finding_id"])

            finding_text = mf["original_finding"]["description"].lower()

            # Find similar findings
            for j, other_mf in enumerate(mapped_findings[i + 1:], i + 1):
                if other_mf["finding_id"] in processed:
                    continue

                other_text = other_mf["original_finding"]["description"].lower()

                # Simple similarity check - could be enhanced with NLP
                similarity_score = self._calculate_text_similarity(finding_text, other_text)
                if similarity_score > 0.3:  # Similarity threshold
                    group.append(other_mf)
                    processed.add(other_mf["finding_id"])

            if len(group) > 1:  # Only keep groups with multiple findings
                groups.append(group)

        # Sort groups by size (largest first)
        groups.sort(key=len, reverse=True)

        return groups

    def _group_by_heuristic(self, mapped_findings: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """Group findings by heuristic violations."""
        heuristic_groups = defaultdict(list)

        for mf in mapped_findings:
            mapping = mf["heuristic_mapping"]
            primary_h = mapping.get("primary_heuristic")
            if primary_h:
                h_id = primary_h["id"]
                heuristic_groups[h_id].append(mf)

        # Convert to list of groups, sorted by group size
        groups = list(heuristic_groups.values())
        groups.sort(key=len, reverse=True)

        return groups

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple text similarity score."""
        words1 = set(text1.split())
        words2 = set(text2.split())

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        if not union:
            return 0.0

        return len(intersection) / len(union)

    def _create_insight_from_group(
        self,
        finding_group: List[Dict[str, Any]],
        insight_id: int,
        config: Dict[str, Any],
    ) -> SynthesisInsight:
        """Create a synthesis insight from a group of findings."""
        # Extract finding data
        findings = [mf["original_finding"] for mf in finding_group]
        finding_ids = [mf["finding_id"] for mf in finding_group]

        # Determine theme from most common words
        theme = self._determine_theme(findings)

        # Calculate aggregate severity
        severities = [f.get("severity", 0) or 0 for f in findings]
        avg_severity = sum(severities) / len(severities)
        severity_label = self._severity_to_label(avg_severity)

        # Count participants and tasks
        participants = set(f.get("participant_id") for f in findings)
        tasks = set(f.get("task_id") for f in findings)

        # Severity distribution
        severity_dist = Counter(severities)

        # Create evidence
        evidence = SynthesisEvidence(
            finding_ids=finding_ids,
            participant_count=len(participants),
            task_count=len(tasks),
            severity_distribution=dict(severity_dist),
        )

        # Identify patterns
        patterns = self._identify_patterns(finding_group)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            finding_group, config["prioritization_weights"]
        )

        # Create insight
        insight = SynthesisInsight(
            insight_id=f"I_{insight_id:03d}",
            title=self._generate_insight_title(theme, severity_label),
            theme=theme,
            severity=severity_label,
            description=self._generate_insight_description(findings, theme),
            evidence=evidence,
            patterns=patterns,
            recommendations=recommendations,
            synthesized_at=datetime.utcnow(),
        )

        return insight

    def _create_individual_insight(
        self, mapped_finding: Dict[str, Any], insight_id: int
    ) -> SynthesisInsight:
        """Create insight from individual finding."""
        finding = mapped_finding["original_finding"]

        theme = self._determine_theme([finding])
        severity_label = self._severity_to_label(finding.get("severity", 0) or 0)

        evidence = SynthesisEvidence(
            finding_ids=[mapped_finding["finding_id"]],
            participant_count=1,
            task_count=1 if finding.get("task_id") else 0,
            severity_distribution={finding.get("severity", 0) or 0: 1},
        )

        patterns = SynthesisPattern(
            cross_participant="Individual issue",
            cross_task="Single task impact",
            workflow_impact=finding.get("description", ""),
        )

        recommendations = self._generate_individual_recommendations(mapped_finding)

        insight = SynthesisInsight(
            insight_id=f"I_{insight_id:03d}",
            title=f"Individual Issue: {finding.get('title', 'Finding')}",
            theme=theme,
            severity=severity_label,
            description=finding.get("description", ""),
            evidence=evidence,
            patterns=patterns,
            recommendations=recommendations,
            synthesized_at=datetime.utcnow(),
        )

        return insight

    def _determine_theme(self, findings: List[Dict[str, Any]]) -> str:
        """Determine thematic category for findings."""
        # Simple keyword-based theming
        themes = {
            "checkout_flow": ["checkout", "payment", "purchase", "buy", "order"],
            "navigation": ["find", "navigate", "menu", "search", "location"],
            "error_handling": ["error", "mistake", "wrong", "failed", "problem"],
            "content_discovery": ["content", "information", "find", "discover"],
            "user_input": ["enter", "input", "form", "field", "type"],
            "performance": ["slow", "loading", "wait", "delay", "performance"],
        }

        theme_scores = Counter()

        for finding in findings:
            text = finding.get("description", "").lower()
            for theme, keywords in themes.items():
                if any(keyword in text for keyword in keywords):
                    theme_scores[theme] += 1

        if theme_scores:
            return theme_scores.most_common(1)[0][0]

        return "general_usability"

    def _severity_to_label(self, severity_score: float) -> str:
        """Convert severity score to label."""
        if severity_score >= 3:
            return "critical"
        elif severity_score >= 2:
            return "high"
        elif severity_score >= 1:
            return "medium"
        else:
            return "low"

    def _generate_insight_title(self, theme: str, severity: str) -> str:
        """Generate descriptive title for insight."""
        theme_titles = {
            "checkout_flow": "Checkout Flow Issues",
            "navigation": "Navigation Problems",
            "error_handling": "Error Handling Issues",
            "content_discovery": "Content Discovery Problems",
            "user_input": "User Input Issues",
            "performance": "Performance Issues",
        }

        base_title = theme_titles.get(theme, f"{theme.replace('_', ' ').title()} Issues")
        return f"{severity.title()} {base_title}"

    def _generate_insight_description(self, findings: List[Dict[str, Any]], theme: str) -> str:
        """Generate description for grouped insight."""
        participant_count = len(set(f.get("participant_id") for f in findings))
        descriptions = [f.get("description", "") for f in findings]

        return f"{participant_count} participants experienced issues with {theme.replace('_', ' ')}: {descriptions[0][:100]}..."

    def _identify_patterns(self, finding_group: List[Dict[str, Any]]) -> SynthesisPattern:
        """Identify patterns in finding group."""
        findings = [mf["original_finding"] for mf in finding_group]

        # Cross-participant pattern
        participants = set(f.get("participant_id") for f in findings)
        if len(participants) > 1:
            cross_participant = f"Issue affected {len(participants)} participants"
        else:
            cross_participant = "Individual participant issue"

        # Cross-task pattern
        tasks = set(f.get("task_id") for f in findings if f.get("task_id"))
        if len(tasks) > 1:
            cross_task = f"Issue occurred across {len(tasks)} different tasks"
        else:
            cross_task = "Issue isolated to single task"

        # Workflow impact
        severities = [f.get("severity", 0) or 0 for f in findings]
        max_severity = max(severities)
        if max_severity >= 3:
            workflow_impact = "Critical workflow blockage identified"
        elif max_severity >= 2:
            workflow_impact = "Significant workflow disruption"
        else:
            workflow_impact = "Minor workflow impact"

        return SynthesisPattern(
            cross_participant=cross_participant,
            cross_task=cross_task,
            workflow_impact=workflow_impact,
        )

    def _generate_recommendations(
        self, finding_group: List[Dict[str, Any]], weights: Dict[str, float]
    ) -> List[SynthesisRecommendation]:
        """Generate prioritized recommendations."""
        recommendations = []

        # Extract common themes and issues
        findings = [mf["original_finding"] for mf in finding_group]
        severities = [f.get("severity", 0) or 0 for f in findings]

        # Calculate priority score
        avg_severity = sum(severities) / len(severities)
        frequency = len(findings)
        impact = avg_severity * frequency  # Simple impact calculation

        priority_score = (
            weights["severity"] * avg_severity +
            weights["frequency"] * min(frequency / 5, 1) +  # Normalize frequency
            weights["impact"] * min(impact / 10, 1)  # Normalize impact
        )

        if priority_score > 0.7:
            priority = "high"
        elif priority_score > 0.4:
            priority = "medium"
        else:
            priority = "low"

        # Generate recommendation based on theme
        theme = self._determine_theme(findings)
        rec_text = self._get_recommendation_text(theme, findings)

        recommendation = SynthesisRecommendation(
            priority=priority,
            description=rec_text,
            expected_impact=f"Address issues for {len(findings)} findings",
            implementation_effort="medium",
            business_value="Improve user experience and task completion rates",
        )

        recommendations.append(recommendation)

        return recommendations

    def _generate_individual_recommendations(
        self, mapped_finding: Dict[str, Any]
    ) -> List[SynthesisRecommendation]:
        """Generate recommendations for individual finding."""
        finding = mapped_finding["original_finding"]
        theme = self._determine_theme([finding])

        rec_text = self._get_recommendation_text(theme, [finding])

        recommendation = SynthesisRecommendation(
            priority="medium",
            description=rec_text,
            expected_impact="Address specific user issue",
            implementation_effort="low",
            business_value="Improve individual user experience",
        )

        return [recommendation]

    def _get_recommendation_text(self, theme: str, findings: List[Dict[str, Any]]) -> str:
        """Get recommendation text based on theme."""
        recommendations = {
            "checkout_flow": "Review and improve checkout flow to reduce completion barriers",
            "navigation": "Enhance navigation structure and visual cues",
            "error_handling": "Improve error messages and recovery mechanisms",
            "content_discovery": "Make content more discoverable and accessible",
            "user_input": "Simplify input requirements and provide better guidance",
            "performance": "Optimize loading times and provide progress feedback",
        }

        return recommendations.get(theme, "Review and improve based on user feedback")

    def _calculate_synthesis_stats(
        self, insights: List[SynthesisInsight], mapped_findings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate synthesis statistics."""
        total_findings = len(mapped_findings)
        total_insights = len(insights)

        # Findings per insight
        findings_per_insight = []
        for insight in insights:
            findings_per_insight.append(len(insight.evidence.finding_ids))
        avg_findings_per_insight = (
            sum(findings_per_insight) / len(findings_per_insight)
            if findings_per_insight else 0
        )

        # Coverage rate
        covered_findings = sum(len(i.evidence.finding_ids) for i in insights)
        coverage_rate = covered_findings / total_findings if total_findings > 0 else 0

        # Priority distribution
        priorities = Counter(i.recommendations[0].priority for i in insights if i.recommendations)

        # Theme distribution
        themes = Counter(i.theme for i in insights)

        return {
            "total_findings_synthesized": total_findings,
            "insights_generated": total_insights,
            "findings_per_insight_avg": round(avg_findings_per_insight, 1),
            "coverage_rate": round(coverage_rate, 2),
            "priority_distribution": dict(priorities),
            "theme_distribution": dict(themes),
        }
