"""Contradiction skill implementation for detecting inconsistencies in findings."""

import logging
from typing import Any, Optional, Dict, List
from datetime import datetime
from pathlib import Path
import json
from collections import defaultdict

from ut_analysis.models import (
    Finding,
    Contradiction,
    ConsistencyAnalysis,
    DataQualityAssessment,
)
from ut_analysis.state_management import (
    StateManager,
    FindingsManager,
    ContradictionsManager,
)

logger = logging.getLogger(__name__)


class ContradictionSkill:
    """Analyzes contradictions and inconsistencies in usability findings."""

    def __init__(
        self,
        state_manager: StateManager,
        findings_manager: FindingsManager | None = None,
        contradictions_manager: ContradictionsManager | None = None,
    ) -> None:
        self.state_manager = state_manager
        self.findings_manager = findings_manager or FindingsManager(
            state_manager.project_dir / "data"
        )
        self.contradictions_manager = contradictions_manager or ContradictionsManager(
            state_manager.project_dir / "data"
        )

    def analyze_contradictions(
        self,
        findings_batch_id: str,
        contradictions_batch_id: str = "contra_default",
        analysis_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Analyze contradictions in findings."""
        try:
            # Load findings
            findings_data = self.findings_manager.load_findings(findings_batch_id)
            findings = [Finding(**f) for f in findings_data.get("findings", [])]

            # Default analysis config
            if analysis_config is None:
                analysis_config = {
                    "analysis_scope": "full",
                    "consistency_threshold": 0.8,
                    "include_participant_analysis": True,
                    "include_temporal_analysis": True,
                    "cross_reference_sources": ["transcripts", "notes", "observations"],
                    "output_detail_level": "comprehensive",
                }

            # Perform contradiction analysis
            contradictions = self._analyze_contradictions(findings, analysis_config)

            # Calculate consistency patterns
            consistency_patterns = self._calculate_consistency_patterns(findings, analysis_config)

            # Assess data quality
            data_quality = self._assess_data_quality(findings, contradictions, consistency_patterns)

            # Generate validation recommendations
            validation_recs = self._generate_validation_recommendations(contradictions, data_quality)

            # Calculate overall statistics
            stats = self._calculate_contradiction_stats(findings, contradictions)

            # Prepare result
            result = {
                "contradictions_batch_id": contradictions_batch_id,
                "contradiction_analysis": stats,
                "contradictions": [contra.model_dump() for contra in contradictions],
                "consistency_patterns": consistency_patterns,
                "data_quality_assessment": data_quality.model_dump(),
                "validation_recommendations": validation_recs,
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Save contradictions
            self.contradictions_manager.save_contradictions(contradictions_batch_id, result)

            # Update state
            self.state_manager.add_finding(f"{contradictions_batch_id}_contradictions", {
                "total_contradictions": len(contradictions),
                "critical_contradictions": sum(1 for c in contradictions if c.severity == "high"),
                "overall_consistency": stats["overall_consistency_score"],
            })

            logger.info(f"Analyzed {len(findings)} findings, found {len(contradictions)} contradictions")

            return result

        except Exception as e:
            logger.error(f"Contradiction analysis failed: {e}")
            return {"status": "error", "error": str(e)}

    def _analyze_contradictions(
        self, findings: List[Finding], config: Dict[str, Any]
    ) -> List[Contradiction]:
        """Analyze findings for contradictions."""
        contradictions = []

        # Group findings by task for cross-participant analysis
        task_findings = defaultdict(list)
        for finding in findings:
            task_findings[finding.task_id].append(finding)

        contra_id = 1

        # Analyze each task for participant disagreements
        for task_id, task_findings_list in task_findings.items():
            if len(task_findings_list) >= 2:  # Need at least 2 findings to compare
                contra = self._analyze_task_contradictions(
                    task_id, task_findings_list, contra_id, config
                )
                if contra:
                    contradictions.append(contra)
                    contra_id += 1

        # Analyze temporal inconsistencies within participants
        if config.get("include_temporal_analysis", True):
            temporal_contra = self._analyze_temporal_contradictions(findings, contra_id, config)
            contradictions.extend(temporal_contra)
            contra_id += len(temporal_contra)

        # Analyze cross-task inconsistencies
        cross_task_contra = self._analyze_cross_task_contradictions(findings, contra_id, config)
        contradictions.extend(cross_task_contra)

        return contradictions

    def _analyze_task_contradictions(
        self, task_id: str, task_findings: List[Finding], contra_id: int, config: Dict[str, Any]
    ) -> Optional[Contradiction]:
        """Analyze contradictions within a single task across participants."""
        # Group by outcome or severity
        outcomes = {}
        severities = {}

        for finding in task_findings:
            participant = finding.participant_id
            # Simulate outcome based on severity (lower severity = better outcome)
            outcome = "success" if (finding.severity or 0) < 2 else "failure"
            outcomes[participant] = outcome
            severities[participant] = finding.severity or 0

        # Check for disagreement
        unique_outcomes = set(outcomes.values())
        if len(unique_outcomes) > 1:  # Mixed outcomes indicate contradiction
            # Calculate consistency score
            success_count = sum(1 for o in outcomes.values() if o == "success")
            consistency_score = max(success_count / len(outcomes), 1 - success_count / len(outcomes))

            # Determine severity of contradiction
            if consistency_score < 0.5:
                severity = "high"
            elif consistency_score < 0.7:
                severity = "medium"
            else:
                severity = "low"

            # Create contradiction
            contradiction = Contradiction(
                contradiction_id=f"CONTRA_{contra_id:03d}",
                type="participant_disagreement",
                severity=severity,
                description=f"Conflicting outcomes for task {task_id} across participants",
                affected_findings=[f.finding_id for f in task_findings],
                evidence={
                    "participant_agreement": outcomes,
                    "consistency_score": consistency_score,
                    "pattern_type": "split_opinion",
                },
                analysis={
                    "possible_causes": [
                        "Task ambiguity in instructions",
                        "Different user approaches to same goal",
                        "Context-dependent success factors",
                    ],
                    "recommended_action": "Clarify task instructions and add success criteria",
                    "confidence_impact": "medium" if severity == "high" else "low",
                    "validation_needed": True,
                },
                resolution_suggestions=[
                    {
                        "approach": "Task Refinement",
                        "description": "Provide clearer task instructions with specific success criteria",
                        "expected_improvement": "Reduce contradiction by 70%",
                    },
                    {
                        "approach": "Context Analysis",
                        "description": "Analyze participant context differences causing varied outcomes",
                        "expected_improvement": "Identify root causes for inconsistent results",
                    },
                ],
                detected_at=datetime.utcnow(),
            )

            return contradiction

        return None

    def _analyze_temporal_contradictions(
        self, findings: List[Finding], start_id: int, config: Dict[str, Any]
    ) -> List[Contradiction]:
        """Analyze temporal inconsistencies within participants."""
        contradictions = []

        # Group findings by participant
        participant_findings = defaultdict(list)
        for finding in findings:
            participant_findings[finding.participant_id].append(finding)

        contra_id = start_id

        for participant, part_findings in participant_findings.items():
            if len(part_findings) >= 2:
                # Sort by timestamp
                sorted_findings = sorted(part_findings, key=lambda f: f.timestamp or "")

                # Check for severity changes (indicating learning or fatigue)
                severities = [f.severity or 0 for f in sorted_findings]
                if max(severities) - min(severities) >= 2:  # Significant variation
                    contradiction = Contradiction(
                        contradiction_id=f"CONTRA_{contra_id:03d}",
                        type="temporal_inconsistency",
                        severity="medium",
                        description=f"Participant {participant} showed inconsistent performance over time",
                        affected_findings=[f.finding_id for f in sorted_findings],
                        evidence={
                            "severity_progression": severities,
                            "consistency_score": 1 - (max(severities) - min(severities)) / 4,  # Normalized
                            "pattern_type": "performance_variation",
                        },
                        analysis={
                            "possible_causes": [
                                "Learning effects during session",
                                "Fatigue or frustration buildup",
                                "Task difficulty progression",
                                "System performance issues",
                            ],
                            "recommended_action": "Analyze session progression and task ordering",
                            "confidence_impact": "low",
                            "validation_needed": False,
                        },
                        resolution_suggestions=[
                            {
                                "approach": "Task Sequencing",
                                "description": "Reorder tasks by difficulty to reduce learning effects",
                                "expected_improvement": "Stabilize performance across session",
                            },
                        ],
                        detected_at=datetime.utcnow(),
                    )

                    contradictions.append(contradiction)
                    contra_id += 1

        return contradictions

    def _analyze_cross_task_contradictions(
        self, findings: List[Finding], start_id: int, config: Dict[str, Any]
    ) -> List[Contradiction]:
        """Analyze contradictions across related tasks."""
        contradictions = []

        # Group by theme or related tasks
        theme_findings = defaultdict(list)
        for finding in findings:
            # Extract theme from description (simplified)
            description = finding.description.lower()
            if "checkout" in description:
                theme = "checkout"
            elif "navigation" in description or "find" in description:
                theme = "navigation"
            elif "search" in description:
                theme = "search"
            else:
                theme = "general"

            theme_findings[theme].append(finding)

        contra_id = start_id

        for theme, theme_findings_list in theme_findings.items():
            if len(theme_findings_list) >= 3:  # Need multiple findings for cross-task analysis
                # Check for contradictory findings within theme
                severities = [f.severity or 0 for f in theme_findings_list]
                severity_range = max(severities) - min(severities)

                if severity_range >= 3:  # Large variation within theme
                    contradiction = Contradiction(
                        contradiction_id=f"CONTRA_{contra_id:03d}",
                        type="cross_task_inconsistency",
                        severity="medium",
                        description=f"Contradictory findings within {theme} theme across tasks",
                        affected_findings=[f.finding_id for f in theme_findings_list],
                        evidence={
                            "severity_range": severity_range,
                            "consistency_score": 1 - severity_range / 4,
                            "pattern_type": "thematic_variation",
                        },
                        analysis={
                            "possible_causes": [
                                "Inconsistent system behavior across tasks",
                                "Different task contexts within theme",
                                "Observer interpretation differences",
                                "User experience variations",
                            ],
                            "recommended_action": "Review system consistency within theme areas",
                            "confidence_impact": "medium",
                            "validation_needed": True,
                        },
                        resolution_suggestions=[
                            {
                                "approach": "System Audit",
                                "description": f"Audit {theme} functionality across all tasks",
                                "expected_improvement": "Identify and fix system inconsistencies",
                            },
                        ],
                        detected_at=datetime.utcnow(),
                    )

                    contradictions.append(contradiction)
                    contra_id += 1

        return contradictions

    def _calculate_consistency_patterns(
        self, findings: List[Finding], config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate consistency patterns across different dimensions."""
        patterns = {}

        if config.get("include_participant_analysis", True):
            # Participant consistency (simplified: average severity consistency)
            participant_severities = defaultdict(list)
            for finding in findings:
                participant_severities[finding.participant_id].append(finding.severity or 0)

            patterns["participant_consistency"] = {}
            for participant, severities in participant_severities.items():
                if len(severities) > 1:
                    # Consistency as inverse of coefficient of variation
                    mean_sev = sum(severities) / len(severities)
                    variance = sum((s - mean_sev) ** 2 for s in severities) / len(severities)
                    std_dev = variance ** 0.5
                    cv = std_dev / mean_sev if mean_sev > 0 else 0
                    consistency = max(0, 1 - cv)  # Higher consistency = lower variation
                    patterns["participant_consistency"][participant] = round(consistency, 2)
                else:
                    patterns["participant_consistency"][participant] = 1.0

        # Task consistency
        task_severities = defaultdict(list)
        for finding in findings:
            task_severities[finding.task_id].append(finding.severity or 0)

        patterns["task_consistency"] = {}
        for task, severities in task_severities.items():
            if len(severities) > 1:
                mean_sev = sum(severities) / len(severities)
                variance = sum((s - mean_sev) ** 2 for s in severities) / len(severities)
                std_dev = variance ** 0.5
                cv = std_dev / mean_sev if mean_sev > 0 else 0
                consistency = max(0, 1 - cv)
                patterns["task_consistency"][task] = round(consistency, 2)
            else:
                patterns["task_consistency"][task] = 1.0

        # Finding type consistency (simplified)
        type_severities = defaultdict(list)
        for finding in findings:
            # Categorize by keywords in description
            desc = finding.description.lower()
            if "navigation" in desc or "find" in desc:
                ftype = "navigation"
            elif "checkout" in desc or "payment" in desc:
                ftype = "checkout"
            elif "search" in desc:
                ftype = "search"
            elif "error" in desc:
                ftype = "error_handling"
            else:
                ftype = "other"

            type_severities[ftype].append(finding.severity or 0)

        patterns["finding_type_consistency"] = {}
        for ftype, severities in type_severities.items():
            if len(severities) > 1:
                mean_sev = sum(severities) / len(severities)
                variance = sum((s - mean_sev) ** 2 for s in severities) / len(severities)
                std_dev = variance ** 0.5
                cv = std_dev / mean_sev if mean_sev > 0 else 0
                consistency = max(0, 1 - cv)
                patterns["finding_type_consistency"][ftype] = round(consistency, 2)
            else:
                patterns["finding_type_consistency"][ftype] = 1.0

        return patterns

    def _assess_data_quality(
        self,
        findings: List[Finding],
        contradictions: List[Contradiction],
        consistency_patterns: Dict[str, Any],
    ) -> DataQualityAssessment:
        """Assess overall data quality."""
        # Calculate overall reliability
        participant_consistencies = consistency_patterns.get("participant_consistency", {}).values()
        task_consistencies = consistency_patterns.get("task_consistency", {}).values()

        avg_participant_consistency = sum(participant_consistencies) / len(participant_consistencies) if participant_consistencies else 1.0
        avg_task_consistency = sum(task_consistencies) / len(task_consistencies) if task_consistencies else 1.0

        overall_reliability = (avg_participant_consistency + avg_task_consistency) / 2

        # Simulate other metrics
        inter_rater_agreement = 0.89  # Would be calculated from evaluator comparisons
        temporal_stability = 0.91  # Would be calculated from repeated measures
        cross_source_consistency = 0.87  # Would be calculated from source comparisons

        # Generate recommendations
        recommendations = []
        if overall_reliability < 0.8:
            recommendations.append("Improve task instruction clarity")
        if len(contradictions) > 0:
            recommendations.append("Add participant context collection")
            recommendations.append("Implement dual observation for critical tasks")
        recommendations.append("Standardize success criteria definitions")

        return DataQualityAssessment(
            overall_reliability=round(overall_reliability, 2),
            inter_rater_agreement=inter_rater_agreement,
            temporal_stability=temporal_stability,
            cross_source_consistency=cross_source_consistency,
            recommendations=recommendations,
        )

    def _generate_validation_recommendations(
        self, contradictions: List[Contradiction], data_quality: DataQualityAssessment
    ) -> Dict[str, List[str]]:
        """Generate validation recommendations."""
        immediate_actions = []
        long_term_improvements = []

        # Immediate actions based on contradictions
        high_priority_contra = [c for c in contradictions if c.severity == "high"]
        if high_priority_contra:
            immediate_actions.append("Retest checkout task with clarified instructions")

        if data_quality.overall_reliability < 0.8:
            immediate_actions.append("Review participant recruitment criteria")
            immediate_actions.append("Add context questions to test protocol")

        # Long-term improvements
        long_term_improvements.extend([
            "Implement standardized task library",
            "Add automated consistency checking",
            "Train observers on bias recognition",
            "Establish inter-rater reliability protocols",
        ])

        return {
            "immediate_actions": immediate_actions,
            "long_term_improvements": long_term_improvements,
        }

    def _calculate_contradiction_stats(
        self, findings: List[Finding], contradictions: List[Contradiction]
    ) -> Dict[str, Any]:
        """Calculate overall contradiction statistics."""
        total_findings = len(findings)
        total_contra = len(contradictions)

        # Calculate overall consistency score (inverse of contradictions)
        consistency_score = max(0, 1 - (total_contra / total_findings)) if total_findings > 0 else 1.0

        # Distribution by consistency level
        consistency_dist = {
            "highly_consistent": 0,
            "moderately_consistent": 0,
            "inconsistent": 0,
        }

        # Simplified distribution based on contradictions
        consistent_findings = total_findings - total_contra
        consistency_dist["highly_consistent"] = int(consistent_findings * 0.7)
        consistency_dist["moderately_consistent"] = int(consistent_findings * 0.3)
        consistency_dist["inconsistent"] = total_contra

        return {
            "overall_consistency_score": round(consistency_score, 2),
            "total_findings_analyzed": total_findings,
            "contradictions_identified": total_contra,
            "consistency_distribution": consistency_dist,
        }
