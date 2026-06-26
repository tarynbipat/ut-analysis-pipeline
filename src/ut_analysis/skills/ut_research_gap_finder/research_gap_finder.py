"""Research gap finder skill implementation."""

import logging
from datetime import datetime
from typing import Any

from ut_analysis.state_management import ResearchGapManager, StateManager

logger = logging.getLogger(__name__)


class ResearchGapFinderSkill:
    """Identifies research gaps and unanswered questions from pipeline outputs."""

    def __init__(
        self,
        state_manager: StateManager,
        gap_manager: ResearchGapManager | None = None,
    ) -> None:
        self.state_manager = state_manager
        self.gap_manager = gap_manager or ResearchGapManager(
            state_manager.project_dir / "data"
        )

    def find_gaps(
        self,
        consolidated_themes: list[dict[str, Any]],
        reconciliations: list[dict[str, Any]] | None = None,
        eval_results: list[dict[str, Any]] | None = None,
        study_config: dict[str, Any] | None = None,
        project_id: str = "",
        run_id: str = "",
    ) -> dict[str, Any]:
        """Identify research gaps from pipeline outputs."""
        try:
            gaps = []
            gap_counter = 1

            for theme in consolidated_themes:
                if theme.get("evidence_strength") in ("weak", "insufficient"):
                    gaps.append(
                        {
                            "gap_id": f"GAP_{gap_counter:03d}",
                            "gap_title": (
                                f"Insufficient evidence for: {theme.get('title', '')}"
                            ),
                            "why_it_matters": (
                                f"Theme '{theme.get('title')}' emerged but has "
                                f"{theme.get('evidence_strength')} evidence support. "
                                "Decisions based on this theme carry risk."
                            ),
                            "related_theme_ids": [
                                theme.get("consolidated_theme_id", "")
                            ],
                            "evidence_limitation": (
                                f"Only {theme.get('participant_count', 0)} "
                                "participant(s) contributed evidence."
                            ),
                            "recommended_follow_up": (
                                "Conduct targeted follow-up sessions focusing on this "
                                "theme with additional participants."
                            ),
                            "priority": (
                                "high"
                                if theme.get("evidence_strength") == "insufficient"
                                else "medium"
                            ),
                            "suggested_method": (
                                "Follow-up usability sessions or targeted interviews"
                            ),
                            "suggested_participant_segment": "Broader participant pool",
                            "decision_it_would_inform": "; ".join(
                                theme.get("product_implications", [])[:2]
                            ),
                        }
                    )
                    gap_counter += 1

            for theme in consolidated_themes:
                for question in theme.get("open_questions", []):
                    if question:
                        gaps.append(
                            {
                                "gap_id": f"GAP_{gap_counter:03d}",
                                "gap_title": f"Open question: {question[:80]}",
                                "why_it_matters": (
                                    "This limitation was identified during analysis and "
                                    "may affect the reliability of related findings."
                                ),
                                "related_theme_ids": [
                                    theme.get("consolidated_theme_id", "")
                                ],
                                "evidence_limitation": question,
                                "recommended_follow_up": "Address in next study design",
                                "priority": "medium",
                                "suggested_method": (
                                    "Contextual inquiry or follow-up interview"
                                ),
                                "suggested_participant_segment": "",
                                "decision_it_would_inform": "",
                            }
                        )
                        gap_counter += 1

            if reconciliations:
                for recon in reconciliations:
                    if recon.get("further_research_needed") or recon.get(
                        "confidence", 1.0
                    ) < 0.6:
                        gaps.append(
                            {
                                "gap_id": f"GAP_{gap_counter:03d}",
                                "gap_title": (
                                    "Unresolved tension: "
                                    f"{recon.get('tension_description', 'Unknown')[:60]}"
                                ),
                                "why_it_matters": (
                                    "Participant disagreement exists but cannot be fully "
                                    "explained with current evidence."
                                ),
                                "related_theme_ids": recon.get("theme_ids", []),
                                "evidence_limitation": (
                                    "Contradiction between participant groups not fully "
                                    "resolved."
                                ),
                                "recommended_follow_up": "; ".join(
                                    recon.get("research_questions", [])[:2]
                                ),
                                "priority": "high",
                                "suggested_method": (
                                    "Targeted interviews with both segments"
                                ),
                                "suggested_participant_segment": (
                                    "Participants from both sides of the tension"
                                ),
                                "decision_it_would_inform": recon.get(
                                    "design_implication", ""
                                ),
                            }
                        )
                        gap_counter += 1

            if study_config:
                participants = study_config.get("participants", [])
                if len(participants) < 5:
                    gaps.append(
                        {
                            "gap_id": f"GAP_{gap_counter:03d}",
                            "gap_title": (
                                "Small participant sample limits generalizability"
                            ),
                            "why_it_matters": (
                                f"Study included only {len(participants)} participants. "
                                "Patterns may not represent the broader user population."
                            ),
                            "related_theme_ids": [],
                            "evidence_limitation": (
                                "Small sample size limits statistical confidence."
                            ),
                            "recommended_follow_up": (
                                "Consider larger follow-up study or validation survey."
                            ),
                            "priority": "medium",
                            "suggested_method": (
                                "Larger usability study or survey validation"
                            ),
                            "suggested_participant_segment": (
                                "Broader demographic representation"
                            ),
                            "decision_it_would_inform": (
                                "Whether findings generalize to full user base"
                            ),
                        }
                    )
                    gap_counter += 1

            if eval_results:
                failed_evals = [
                    e for e in eval_results if e.get("pass_fail") == "fail"
                ]
                if failed_evals:
                    gaps.append(
                        {
                            "gap_id": f"GAP_{gap_counter:03d}",
                            "gap_title": "Quality issues in pipeline outputs",
                            "why_it_matters": (
                                f"{len(failed_evals)} artifact(s) failed evaluation "
                                "checks, indicating potential reliability concerns."
                            ),
                            "related_theme_ids": [],
                            "evidence_limitation": "; ".join(
                                e.get("issues", ["Unknown"])[0]
                                for e in failed_evals[:3]
                            ),
                            "recommended_follow_up": (
                                "Re-analyze affected artifacts with revised methodology"
                            ),
                            "priority": "high",
                            "suggested_method": "Re-extraction or manual review",
                            "suggested_participant_segment": "",
                            "decision_it_would_inform": (
                                "Reliability of current findings"
                            ),
                        }
                    )
                    gap_counter += 1

            result = {
                "project_id": project_id,
                "run_id": run_id,
                "gaps": gaps,
                "created_at": datetime.utcnow().isoformat(),
            }

            self.gap_manager.save_gaps(run_id, result)
            return result

        except Exception as e:
            logger.error(f"Research gap finding failed: {e}")
            return {"status": "error", "error": str(e)}
