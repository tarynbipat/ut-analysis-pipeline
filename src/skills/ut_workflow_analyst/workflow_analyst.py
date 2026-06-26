"""Workflow analyst skill implementation."""

import logging
import re
from collections import defaultdict
from datetime import datetime
from typing import Any

from ut_analysis.state_management import StateManager, ThematicAnalysisManager

logger = logging.getLogger(__name__)

STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "but",
    "by",
    "for",
    "from",
    "has",
    "have",
    "in",
    "into",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "their",
    "them",
    "they",
    "this",
    "to",
    "users",
    "using",
    "with",
}

THEME_KEYWORDS = {
    "Step Sequence Breakdowns": ["step", "sequence", "order", "next", "back", "flow"],
    "Navigation Dead Ends": ["dead", "end", "lost", "loop", "return", "backtrack"],
    "Abandonment Points": ["abandon", "quit", "drop", "exit", "leave", "stop"],
    "Handoff Gaps": ["handoff", "transition", "between", "switch", "context", "handover"],
    "Process Confusion": ["process", "workflow", "where", "start", "finish", "complete"],
}
THEME_IMPLICATIONS = {
    "Step Sequence Breakdowns": "Redesign the flow so the next step is obvious and resilient.",
    "Navigation Dead Ends": "Remove dead ends and give users a clear recovery path through the flow.",
    "Abandonment Points": "Redesign the abandonment point to keep users progressing with less friction.",
    "Handoff Gaps": "Tighten the transition between steps so context is preserved across the workflow.",
    "Process Confusion": "Clarify the process so users understand where they are and what comes next.",
}
DEFAULT_IMPLICATION = (
    "Redesign the flow around {theme_title_lower} to make the workflow easier to complete."
)
FALLBACK_THEME_TITLE = "Workflow Theme"


class WorkflowAnalystSkill:
    """Analyzes workflow issues, process breakdowns, and navigation failures."""

    def __init__(
        self,
        state_manager: StateManager,
        thematic_manager: ThematicAnalysisManager | None = None,
    ) -> None:
        self.state_manager = state_manager
        self.thematic_manager = thematic_manager or ThematicAnalysisManager(
            state_manager.project_dir / "data"
        )

    def analyze_lane(self, lane_data: dict[str, Any], run_id: str) -> dict[str, Any]:
        """Analyze findings assigned to the workflow lane."""
        try:
            lane_id = lane_data.get("lane_id", "ut_workflow_analyst")
            findings = lane_data.get("findings", [])

            if not findings:
                return {"status": "empty", "lane_id": lane_id, "themes": []}

            theme_groups = self._identify_themes(findings)
            themes: list[dict[str, Any]] = []

            for idx, (theme_title, group) in enumerate(theme_groups.items(), start=1):
                participants: set[str] = set()
                tasks: set[str] = set()
                quotes: list[str] = []

                for finding in group:
                    participant_id = finding.get("participant_id")
                    task_id = finding.get("task_id")
                    quote = finding.get("verbatim_quote")
                    if participant_id:
                        participants.add(str(participant_id))
                    if task_id:
                        tasks.add(str(task_id))
                    if quote:
                        quotes.append(str(quote)[:200])

                group_size = len(group)
                confidence_floor = 0.3 if group_size == 1 else 0.45
                confidence = min(
                    0.95,
                    confidence_floor + (group_size * 0.1) + (len(participants) * 0.08),
                )

                themes.append(
                    {
                        "theme_id": f"{lane_id}_T{idx:03d}",
                        "theme_title": theme_title,
                        "theme_summary": self._generate_summary(group, theme_title),
                        "evidence_count": group_size,
                        "participant_count": len(participants),
                        "task_coverage": sorted(tasks),
                        "representative_quotes": quotes[:3],
                        "contradictions_or_outliers": self._find_outliers(group),
                        "product_implication": self._generate_implication(theme_title, group),
                        "confidence": round(confidence, 2),
                        "limitations": self._identify_limitations(group, participants),
                    }
                )

            source_ids = lane_data.get("finding_ids") or lane_data.get("input_finding_ids")
            if not source_ids:
                source_ids = [
                    finding.get("finding_id") for finding in findings if finding.get("finding_id")
                ]

            result = {
                "run_id": run_id,
                "lane_id": lane_id,
                "lane_name": lane_data.get("lane_name", "Workflow Breakdowns"),
                "agent_name": "workflow-analyst",
                "source_finding_ids": source_ids,
                "themes": themes,
                "analyzed_at": datetime.utcnow().isoformat(),
            }

            self.thematic_manager.save_lane_analysis(lane_id, result)
            return result

        except Exception as exc:
            logger.error("Workflow analysis failed: %s", exc)
            return {"status": "error", "error": str(exc)}

    def _identify_themes(self, findings: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        """Group findings into themes based on content similarity."""
        themes: dict[str, list[dict[str, Any]]] = defaultdict(list)
        processed: set[int] = set()

        for index, finding in enumerate(findings):
            if index in processed:
                continue

            text = self._combine_text(finding)
            theme_label = self._extract_theme_label(text)
            if theme_label in themes and not any(
                self._are_similar(text, self._combine_text(existing))
                for existing in themes[theme_label]
            ):
                theme_label = self._build_unique_theme_label(theme_label, text, themes)

            themes[theme_label].append(finding)
            processed.add(index)

            for other_index in range(index + 1, len(findings)):
                if other_index in processed:
                    continue
                other = findings[other_index]
                other_text = self._combine_text(other)
                if self._are_similar(text, other_text):
                    themes[theme_label].append(other)
                    processed.add(other_index)

        return dict(
            sorted(
                themes.items(),
                key=lambda item: (len(item[1]), item[0]),
                reverse=True,
            )
        )

    def _build_unique_theme_label(
        self,
        base_label: str,
        text: str,
        themes: dict[str, list[dict[str, Any]]],
    ) -> str:
        """Create a unique label when separate clusters map to the same theme family."""
        fallback_words = [word.capitalize() for word in list(self._normalize_words(text))[:3]]
        candidate = " ".join(fallback_words)[:60] or f"{base_label} Variant"

        if candidate == base_label:
            candidate = f"{base_label} Variant"

        suffix = 2
        unique_candidate = candidate
        while unique_candidate in themes:
            unique_candidate = f"{candidate} {suffix}"
            suffix += 1

        return unique_candidate

    def _combine_text(self, finding: dict[str, Any]) -> str:
        """Combine title and description text for comparison."""
        title = str(finding.get("title", "")).strip().lower()
        description = str(finding.get("description", "")).strip().lower()
        return f"{title} {description}".strip()

    def _normalize_words(self, text: str) -> set[str]:
        """Normalize text into meaningful comparison tokens."""
        words = re.findall(r"[a-z0-9]+", text.lower())
        normalized = set()
        for word in words:
            if len(word) <= 2 or word in STOP_WORDS:
                continue
            normalized.add(word[:-1] if word.endswith("s") and len(word) > 4 else word)
        return normalized

    def _extract_theme_label(self, text: str) -> str:
        """Extract a lane-specific theme label from finding text."""
        words = self._normalize_words(text)
        best_label = ""
        best_score = 0

        for label, keywords in THEME_KEYWORDS.items():
            score = len(words.intersection(keywords))
            if score > best_score:
                best_label = label
                best_score = score

        if best_label:
            return best_label

        fallback_words = [word.capitalize() for word in list(words)[:4]]
        return " ".join(fallback_words)[:60] or FALLBACK_THEME_TITLE

    def _are_similar(self, text1: str, text2: str) -> bool:
        """Check if two findings are thematically similar."""
        words1 = self._normalize_words(text1)
        words2 = self._normalize_words(text2)
        if not words1 or not words2:
            return False

        shared_words = words1.intersection(words2)
        if len(shared_words) >= 2:
            return True

        overlap = len(shared_words) / len(words1.union(words2))
        return overlap >= 0.2

    def _generate_summary(self, findings: list[dict[str, Any]], theme_title: str) -> str:
        """Generate a summary for a theme group."""
        participant_ids = {
            str(finding.get("participant_id"))
            for finding in findings
            if finding.get("participant_id")
        }
        return (
            f"{len(findings)} finding(s) from {len(participant_ids)} participant(s) "
            f"highlighting workflow issues, process breakdowns, and flow failures around {theme_title.lower()}."
        )

    def _find_outliers(self, findings: list[dict[str, Any]]) -> list[str]:
        """Identify contradictions or outliers within the theme."""
        outliers: list[str] = []
        severities = [self._coerce_severity(finding.get("severity")) for finding in findings]
        valid_severities = [severity for severity in severities if severity is not None]

        if len(valid_severities) >= 3:
            average = sum(valid_severities) / len(valid_severities)
            for finding in findings:
                severity = self._coerce_severity(finding.get("severity"))
                if severity is None:
                    continue
                if abs(severity - average) > 1.5:
                    outliers.append(
                        f"Finding {finding.get('finding_id', '?')} has severity {severity} "
                        f"vs group average {average:.1f}"
                    )

        sentiments = {
            str(finding.get("sentiment", "")).lower()
            for finding in findings
            if finding.get("sentiment")
        }
        if "positive" in sentiments and "negative" in sentiments:
            outliers.append("Mixed sentiment within the theme suggests a possible contradiction")

        return outliers

    def _coerce_severity(self, value: Any) -> int | None:
        """Convert severity values to integers when possible."""
        if value in (None, ""):
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def _generate_implication(self, theme_title: str, findings: list[dict[str, Any]]) -> str:
        """Generate a lane-specific product implication for the theme."""
        del findings
        if theme_title in THEME_IMPLICATIONS:
            return THEME_IMPLICATIONS[theme_title]
        return DEFAULT_IMPLICATION.format(theme_title_lower=theme_title.lower())

    def _identify_limitations(
        self, findings: list[dict[str, Any]], participants: set[str]
    ) -> list[str]:
        """Identify limitations in the evidence."""
        limitations: list[str] = []
        if len(participants) == 1:
            limitations.append("Based on a single participant and may not generalize")
        if len(findings) < 3:
            limitations.append("Limited evidence with fewer than 3 supporting findings")
        task_ids = {str(finding.get("task_id")) for finding in findings if finding.get("task_id")}
        if len(task_ids) <= 1:
            limitations.append("Theme is concentrated in one task or workflow context")
        return limitations
