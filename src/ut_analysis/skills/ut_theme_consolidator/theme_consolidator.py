"""Theme consolidator skill implementation."""

import logging
from datetime import datetime
from typing import Any

from ut_analysis.state_management import StateManager, ThematicAnalysisManager

logger = logging.getLogger(__name__)


class ThemeConsolidatorSkill:
    """Consolidates themes from parallel thematic lane analyses."""

    def __init__(
        self,
        state_manager: StateManager,
        thematic_manager: ThematicAnalysisManager | None = None,
    ) -> None:
        self.state_manager = state_manager
        self.thematic_manager = thematic_manager or ThematicAnalysisManager(
            state_manager.project_dir / "data"
        )

    def consolidate_themes(
        self,
        lane_analyses: list[dict[str, Any]],
        project_id: str,
        consolidation_id: str,
    ) -> dict[str, Any]:
        """Consolidate themes from multiple lane analyses into unified themes."""
        try:
            all_themes = []
            for lane in lane_analyses:
                lane_id = lane.get("lane_id", "unknown")
                lane_name = lane.get("lane_name", "unknown")
                for theme in lane.get("themes", []):
                    theme["_source_lane_id"] = lane_id
                    theme["_source_lane_name"] = lane_name
                    all_themes.append(theme)

            if not all_themes:
                return {"status": "empty", "consolidated_themes": []}

            consolidated = self._merge_overlapping_themes(all_themes)
            relationships = self._find_cross_lane_relationships(consolidated)

            result = {
                "consolidation_id": consolidation_id,
                "project_id": project_id,
                "consolidated_themes": consolidated,
                "cross_lane_relationships": relationships,
                "created_at": datetime.utcnow().isoformat(),
            }

            self.thematic_manager.save_consolidation(consolidation_id, result)
            return result

        except Exception as e:
            logger.error(f"Theme consolidation failed: {e}")
            return {"status": "error", "error": str(e)}

    def _merge_overlapping_themes(
        self, all_themes: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Merge themes that appear to cover the same topic across lanes."""
        consolidated = []
        processed = set()

        for i, theme in enumerate(all_themes):
            if i in processed:
                continue

            group = [theme]
            processed.add(i)

            theme_words = set(theme.get("theme_title", "").lower().split())

            for j, other in enumerate(all_themes[i + 1 :], i + 1):
                if j in processed:
                    continue
                other_words = set(other.get("theme_title", "").lower().split())
                if theme_words and other_words:
                    overlap = len(theme_words & other_words) / max(
                        len(theme_words | other_words), 1
                    )
                    if overlap > 0.3:
                        group.append(other)
                        processed.add(j)

            contributing_lanes = list(
                set(t.get("_source_lane_name", "unknown") for t in group)
            )
            source_theme_ids = [t.get("theme_id", "") for t in group]
            all_quotes = []
            for t in group:
                all_quotes.extend(t.get("representative_quotes", []))
            all_contradictions = []
            for t in group:
                all_contradictions.extend(t.get("contradictions_or_outliers", []))
            all_implications = [
                t.get("product_implication", "")
                for t in group
                if t.get("product_implication")
            ]
            all_questions = []
            for t in group:
                all_questions.extend(t.get("limitations", []))

            total_participants = sum(t.get("participant_count", 0) for t in group)
            total_evidence = sum(t.get("evidence_count", 0) for t in group)

            if total_participants >= 4 and total_evidence >= 5:
                strength = "strong"
            elif total_participants >= 2 and total_evidence >= 3:
                strength = "moderate"
            elif total_participants >= 1:
                strength = "weak"
            else:
                strength = "insufficient"

            avg_confidence = sum(t.get("confidence", 0.5) for t in group) / len(group)

            consolidated.append(
                {
                    "consolidated_theme_id": f"CT_{len(consolidated) + 1:03d}",
                    "title": group[0].get("theme_title", "Untitled Theme"),
                    "summary": self._build_consolidated_summary(group),
                    "contributing_lanes": contributing_lanes,
                    "source_theme_ids": source_theme_ids,
                    "evidence_strength": strength,
                    "participant_count": total_participants,
                    "key_quotes": all_quotes[:5],
                    "tensions_or_contradictions": all_contradictions,
                    "product_implications": all_implications,
                    "confidence": round(avg_confidence, 2),
                    "open_questions": all_questions[:5],
                }
            )

        strength_order = {"strong": 0, "moderate": 1, "weak": 2, "insufficient": 3}
        consolidated.sort(key=lambda x: strength_order.get(x["evidence_strength"], 4))

        return consolidated

    def _build_consolidated_summary(self, group: list[dict[str, Any]]) -> str:
        """Build a summary from a group of related themes."""
        lanes = set(t.get("_source_lane_name", "") for t in group)
        total_evidence = sum(t.get("evidence_count", 0) for t in group)
        return (
            f"Cross-lane theme spanning {', '.join(lanes)} with {total_evidence} "
            f"supporting findings. {group[0].get('theme_summary', '')}"
        )

    def _find_cross_lane_relationships(
        self, consolidated: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Identify relationships between consolidated themes."""
        relationships = []
        for i, theme_a in enumerate(consolidated):
            for theme_b in consolidated[i + 1 :]:
                shared_lanes = set(theme_a["contributing_lanes"]) & set(
                    theme_b["contributing_lanes"]
                )
                if shared_lanes:
                    relationships.append(
                        {
                            "theme_a": theme_a["consolidated_theme_id"],
                            "theme_b": theme_b["consolidated_theme_id"],
                            "relationship": "shared_lanes",
                            "shared_lanes": list(shared_lanes),
                            "description": (
                                f"'{theme_a['title']}' and '{theme_b['title']}' "
                                f"both appear in {', '.join(shared_lanes)}"
                            ),
                        }
                    )
        return relationships
