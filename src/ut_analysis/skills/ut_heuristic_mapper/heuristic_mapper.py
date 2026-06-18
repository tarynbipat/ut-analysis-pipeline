"""Heuristic mapper skill implementation for mapping findings to Nielsen heuristics."""

import logging
from typing import Any, Optional, Dict, List
from datetime import datetime
from collections import Counter, defaultdict

from ut_analysis.models import (
    Finding,
    HeuristicMapping,
    HeuristicViolation,
    NielsenHeuristic,
)
from ut_analysis.state_management import (
    StateManager,
    SeverityManager,
    HeuristicManager,
)

logger = logging.getLogger(__name__)


class HeuristicMapperSkill:
    """Maps findings to Nielsen's 10 usability heuristics."""

    # Nielsen's 10 heuristics with keywords for mapping
    HEURISTICS = {
        "H1": {
            "name": "Visibility of system status",
            "keywords": ["loading", "progress", "status", "feedback", "waiting", "processing", "silent", "no indication"],
        },
        "H2": {
            "name": "Match between system and real world",
            "keywords": ["jargon", "technical", "confusing", "doesn't make sense", "weird", "strange", "counter-intuitive"],
        },
        "H3": {
            "name": "User control and freedom",
            "keywords": ["can't cancel", "stuck", "no undo", "forced", "trapped", "no way out", "can't go back"],
        },
        "H4": {
            "name": "Consistency and standards",
            "keywords": ["inconsistent", "different", "confusing", "not the same", "varies", "changes", "inconsistent"],
        },
        "H5": {
            "name": "Error prevention",
            "keywords": ["mistake", "accident", "wrong", "error", "no validation", "easy to mess up", "dangerous"],
        },
        "H6": {
            "name": "Recognition rather than recall",
            "keywords": ["hidden", "can't find", "forgot", "memory", "remember", "recall", "not visible"],
        },
        "H7": {
            "name": "Flexibility and efficiency of use",
            "keywords": ["slow", "inefficient", "rigid", "no shortcuts", "tedious", "repetitive", "cumbersome"],
        },
        "H8": {
            "name": "Aesthetic and minimalist design",
            "keywords": ["cluttered", "messy", "overwhelming", "too much", "confusing", "busy", "crowded"],
        },
        "H9": {
            "name": "Help users recognize, diagnose, and recover from errors",
            "keywords": ["error message", "confusing error", "technical error", "no help", "can't recover", "stuck"],
        },
        "H10": {
            "name": "Help and documentation",
            "keywords": ["no help", "can't find help", "documentation", "instructions", "guidance", "support"],
        },
    }

    def __init__(
        self,
        state_manager: StateManager,
        severity_manager: SeverityManager | None = None,
        heuristic_manager: HeuristicManager | None = None,
    ) -> None:
        self.state_manager = state_manager
        self.severity_manager = severity_manager or SeverityManager(
            state_manager.project_dir / "data"
        )
        self.heuristic_manager = heuristic_manager or HeuristicManager(
            state_manager.project_dir / "data"
        )

    def map_heuristics(
        self,
        severity_batch_id: str,
        heuristic_batch_id: str = "heuristic_default",
        mapping_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Map findings to usability heuristics."""
        try:
            # Load severity-rated findings
            severity_data = self.severity_manager.load_severity_ratings(severity_batch_id)
            rated_findings = severity_data.get("rated_findings", [])

            # Default mapping config
            if mapping_config is None:
                mapping_config = {
                    "min_confidence_threshold": 0.7,
                    "allow_multiple_mappings": True,
                    "max_secondary_heuristics": 2,
                }

            # Map each finding
            mapped_findings = []
            for rf in rated_findings:
                mapped = self._map_single_finding(rf, mapping_config)
                if mapped["heuristic_mapping"]["primary_heuristic"]:
                    mapped_findings.append(mapped)

            # Calculate heuristic analysis
            analysis = self._analyze_heuristics(mapped_findings)

            # Prepare result
            result = {
                "heuristic_batch_id": heuristic_batch_id,
                "mapped_findings": mapped_findings,
                "heuristic_analysis": analysis,
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Save heuristic mappings
            self.heuristic_manager.save_heuristic_mappings(heuristic_batch_id, result)

            # Update state
            self.state_manager.add_finding(f"{heuristic_batch_id}_heuristic", {
                "total_mapped": len(mapped_findings),
                "most_problematic": analysis["most_problematic_heuristics"][:3],
                "coverage_gaps": len(analysis["untested_heuristics"]),
            })

            logger.info(f"Mapped {len(mapped_findings)} findings to heuristics in batch {heuristic_batch_id}")

            return result

        except Exception as e:
            logger.error(f"Heuristic mapping failed: {e}")
            return {"status": "error", "error": str(e)}

    def _map_single_finding(
        self, rated_finding: Dict[str, Any], config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Map a single finding to heuristics."""
        finding = rated_finding["original_finding"]
        text = finding.description.lower() + " " + finding.verbatim_quote.lower()

        # Calculate confidence scores for each heuristic
        heuristic_scores = {}
        for h_id, h_data in self.HEURISTICS.items():
            score = self._calculate_heuristic_score(text, h_data["keywords"])
            if score >= config["min_confidence_threshold"]:
                heuristic_scores[h_id] = score

        # Select primary heuristic (highest score)
        primary_heuristic = None
        if heuristic_scores:
            primary_id = max(heuristic_scores, key=heuristic_scores.get)
            primary_heuristic = HeuristicViolation(
                id=primary_id,
                name=self.HEURISTICS[primary_id]["name"],
                confidence=heuristic_scores[primary_id],
                rationale=self._generate_rationale(finding, primary_id),
            )

        # Select secondary heuristics
        secondary_heuristics = []
        if config["allow_multiple_mappings"] and len(heuristic_scores) > 1:
            # Sort by score, skip primary
            sorted_heuristics = sorted(
                heuristic_scores.items(),
                key=lambda x: x[1],
                reverse=True
            )[1:]  # Skip the primary

            for h_id, score in sorted_heuristics[:config["max_secondary_heuristics"]]:
                secondary = HeuristicViolation(
                    id=h_id,
                    name=self.HEURISTICS[h_id]["name"],
                    confidence=score,
                    rationale=self._generate_secondary_rationale(finding, h_id),
                )
                secondary_heuristics.append(secondary)

        # Generate design recommendations
        design_recommendations = self._generate_recommendations(
            primary_heuristic, secondary_heuristics, finding
        )

        # Create mapping
        heuristic_mapping = HeuristicMapping(
            primary_heuristic=primary_heuristic,
            secondary_heuristics=secondary_heuristics,
            design_recommendations=design_recommendations,
            mapped_at=datetime.utcnow(),
        )

        return {
            "finding_id": rated_finding["finding_id"],
            "original_finding": finding,
            "heuristic_mapping": heuristic_mapping,
        }

    def _calculate_heuristic_score(self, text: str, keywords: List[str]) -> float:
        """Calculate confidence score for heuristic mapping."""
        score = 0.0
        matched_keywords = 0

        for keyword in keywords:
            if keyword in text:
                matched_keywords += 1
                # Give higher weight to exact matches
                if keyword in text:
                    score += 0.2
                else:
                    score += 0.1

        # Normalize by number of keywords
        if keywords:
            base_score = matched_keywords / len(keywords)
            score = min(base_score + score, 1.0)

        return score

    def _generate_rationale(self, finding: Finding, heuristic_id: str) -> str:
        """Generate rationale for primary heuristic mapping."""
        heuristic_name = self.HEURISTICS[heuristic_id]["name"]

        # Simple rationale generation based on finding content
        text = finding.description.lower()

        rationales = {
            "H1": f"The finding indicates lack of system status visibility: {finding.verbatim_quote}",
            "H2": f"The issue shows mismatch with real-world expectations: {finding.verbatim_quote}",
            "H3": f"The problem demonstrates lack of user control: {finding.verbatim_quote}",
            "H4": f"The issue violates consistency principles: {finding.verbatim_quote}",
            "H5": f"The finding shows inadequate error prevention: {finding.verbatim_quote}",
            "H6": f"The problem requires user recall instead of recognition: {finding.verbatim_quote}",
            "H7": f"The issue lacks flexibility for efficient use: {finding.verbatim_quote}",
            "H8": f"The finding indicates poor aesthetic design: {finding.verbatim_quote}",
            "H9": f"The problem shows poor error handling: {finding.verbatim_quote}",
            "H10": f"The issue demonstrates lack of helpful documentation: {finding.verbatim_quote}",
        }

        return rationales.get(heuristic_id, f"Violates {heuristic_name}: {finding.verbatim_quote}")

    def _generate_secondary_rationale(self, finding: Finding, heuristic_id: str) -> str:
        """Generate rationale for secondary heuristic mapping."""
        heuristic_name = self.HEURISTICS[heuristic_id]["name"]
        return f"Related to {heuristic_name} principles: {finding.description}"

    def _generate_recommendations(
        self,
        primary: Optional[HeuristicViolation],
        secondary: List[HeuristicViolation],
        finding: Finding,
    ) -> List[str]:
        """Generate design recommendations based on violated heuristics."""
        recommendations = []

        # Primary heuristic recommendations
        if primary:
            recs = self._get_heuristic_recommendations(primary.id, finding)
            recommendations.extend(recs)

        # Secondary heuristic recommendations
        for sec in secondary:
            recs = self._get_heuristic_recommendations(sec.id, finding)
            recommendations.extend(recs[:1])  # Limit secondary recommendations

        return recommendations[:5]  # Limit total recommendations

    def _get_heuristic_recommendations(self, heuristic_id: str, finding: Finding) -> List[str]:
        """Get specific recommendations for a heuristic."""
        recommendations = {
            "H1": [
                "Add clear status indicators during loading/processing",
                "Provide progress feedback for long operations",
                "Show current state clearly in the interface",
            ],
            "H2": [
                "Use familiar terminology and concepts",
                "Follow real-world conventions in the interface",
                "Replace technical jargon with user-friendly language",
            ],
            "H3": [
                "Add clear cancel/undo options",
                "Provide escape routes from unwanted states",
                "Make it easy to correct mistakes",
            ],
            "H4": [
                "Ensure consistent behavior across similar actions",
                "Follow platform design standards",
                "Use consistent terminology throughout",
            ],
            "H5": [
                "Add input validation and confirmation dialogs",
                "Prevent common user mistakes",
                "Guide users away from dangerous actions",
            ],
            "H6": [
                "Make important options and information visible",
                "Reduce memory load by showing available actions",
                "Provide clear navigation cues",
            ],
            "H7": [
                "Add keyboard shortcuts for power users",
                "Allow customization of frequent actions",
                "Provide multiple paths to common goals",
            ],
            "H8": [
                "Remove irrelevant information from the interface",
                "Improve visual hierarchy and organization",
                "Focus on essential content and actions",
            ],
            "H9": [
                "Write clear, helpful error messages",
                "Provide specific guidance for error recovery",
                "Use plain language in error communications",
            ],
            "H10": [
                "Add context-sensitive help and documentation",
                "Make help easily discoverable",
                "Provide searchable assistance resources",
            ],
        }

        return recommendations.get(heuristic_id, ["Review and improve based on usability principles"])

    def _analyze_heuristics(self, mapped_findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze heuristic violation patterns."""
        # Count violations per heuristic
        violation_counts = Counter()
        severity_by_heuristic = defaultdict(list)

        for mf in mapped_findings:
            mapping = mf["heuristic_mapping"]

            # Primary heuristic
            if mapping["primary_heuristic"]:
                h_id = mapping["primary_heuristic"]["id"]
                violation_counts[h_id] += 1
                severity = mf["original_finding"]["severity"] or 0
                severity_by_heuristic[h_id].append(severity)

            # Secondary heuristics
            for sec in mapping["secondary_heuristics"]:
                h_id = sec["id"]
                violation_counts[h_id] += 0.5  # Weight secondary less
                severity = mf["original_finding"]["severity"] or 0
                severity_by_heuristic[h_id].append(severity)

        # Calculate severity statistics
        severity_stats = {}
        for h_id, severities in severity_by_heuristic.items():
            if severities:
                severity_stats[h_id] = {
                    "avg_severity": round(sum(severities) / len(severities), 2),
                    "max_severity": max(severities),
                    "critical_count": sum(1 for s in severities if s >= 3),
                }

        # Most problematic heuristics (by violation count)
        most_problematic = [
            h_id for h_id, _ in violation_counts.most_common(5)
        ]

        # Untested heuristics
        tested_heuristics = set(violation_counts.keys())
        all_heuristics = set(self.HEURISTICS.keys())
        untested_heuristics = list(all_heuristics - tested_heuristics)

        # Coverage gaps
        coverage_gaps = []
        if "H8" in untested_heuristics:
            coverage_gaps.append("No testing of aesthetic design elements")
        if "H10" in untested_heuristics:
            coverage_gaps.append("Help system not evaluated")
        if len(untested_heuristics) > 2:
            coverage_gaps.append(f"{len(untested_heuristics)} heuristics not tested")

        return {
            "violation_frequency": dict(violation_counts),
            "severity_by_heuristic": severity_stats,
            "most_problematic_heuristics": most_problematic,
            "untested_heuristics": untested_heuristics,
            "coverage_gaps": coverage_gaps,
        }
