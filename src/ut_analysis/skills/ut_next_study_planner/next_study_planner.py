"""Next study planner skill implementation."""

import logging
from datetime import datetime
from typing import Any

from ut_analysis.state_management import NextStudyManager, StateManager

logger = logging.getLogger(__name__)


class NextStudyPlannerSkill:
    """Generates next-study recommendations from research gaps."""

    def __init__(
        self,
        state_manager: StateManager,
        next_study_manager: NextStudyManager | None = None,
    ) -> None:
        self.state_manager = state_manager
        self.next_study_manager = next_study_manager or NextStudyManager(
            state_manager.project_dir / "data"
        )

    def generate_plans(
        self,
        research_gaps: list[dict[str, Any]],
        study_config: dict[str, Any] | None = None,
        project_id: str = "",
        run_id: str = "",
    ) -> dict[str, Any]:
        """Generate next-study plans from research gaps."""
        try:
            plans = []
            plan_counter = 1

            priority_order = {"high": 0, "medium": 1, "low": 2}
            sorted_gaps = sorted(
                research_gaps,
                key=lambda g: priority_order.get(g.get("priority", "low"), 3),
            )

            for gap in sorted_gaps[:5]:
                method = self._recommend_method(gap)
                plan = {
                    "plan_id": f"PLAN_{plan_counter:03d}",
                    "study_objective": self._formulate_objective(gap),
                    "method_recommendation": method,
                    "target_participant_profile": (
                        gap.get("suggested_participant_segment", "")
                        or "Representative users from the target population"
                    ),
                    "key_research_questions": self._formulate_questions(gap),
                    "suggested_tasks_or_topics": self._suggest_tasks(gap, method),
                    "decision_it_would_inform": (
                        gap.get("decision_it_would_inform", "")
                        or "Whether current findings hold with additional evidence"
                    ),
                    "why_this_method": self._explain_method_choice(gap, method),
                    "risks_and_limitations": self._identify_risks(gap, method),
                    "priority": gap.get("priority", "medium"),
                }
                plans.append(plan)
                plan_counter += 1

            result = {
                "project_id": project_id,
                "run_id": run_id,
                "plans": plans,
                "created_at": datetime.utcnow().isoformat(),
            }

            self.next_study_manager.save_plan(run_id, result)
            return result

        except Exception as e:
            logger.error(f"Next study planning failed: {e}")
            return {"status": "error", "error": str(e)}

    def _recommend_method(self, gap: dict[str, Any]) -> str:
        """Recommend a research method based on the gap type."""
        suggested = gap.get("suggested_method", "")
        if suggested:
            return suggested

        title = gap.get("gap_title", "").lower()
        if "contradiction" in title or "tension" in title:
            return "Targeted interviews with participants from each segment"
        elif "sample" in title or "generalize" in title:
            return "Larger-scale usability study or validation survey"
        elif "insufficient" in title or "weak" in title:
            return "Small follow-up usability study with think-aloud protocol"
        else:
            return "Contextual inquiry or semi-structured interview"

    def _formulate_objective(self, gap: dict[str, Any]) -> str:
        """Create a study objective from the gap."""
        title = gap.get("gap_title", "Unknown gap")
        return f"Investigate and resolve: {title}"

    def _formulate_questions(self, gap: dict[str, Any]) -> list[str]:
        """Generate research questions from the gap."""
        questions = []
        follow_up = gap.get("recommended_follow_up", "")
        if follow_up:
            questions.append(follow_up)

        title = gap.get("gap_title", "")
        questions.append(f"What additional evidence exists for or against: {title}?")
        questions.append("What contextual factors influence this behavior?")

        return questions[:3]

    def _suggest_tasks(self, gap: dict[str, Any], method: str) -> list[str]:
        """Suggest tasks or discussion topics."""
        if "interview" in method.lower():
            return [
                "Open discussion about experiences related to the gap",
                "Specific scenarios that triggered the observed behavior",
                "Exploration of expectations vs reality",
            ]
        elif "usability" in method.lower():
            return [
                "Task scenarios covering the gap area",
                "Think-aloud observation of relevant workflows",
                "Post-task reflection questions",
            ]
        else:
            return [
                "Explore the gap area through relevant activities",
                "Observe natural behavior in context",
            ]

    def _explain_method_choice(self, gap: dict[str, Any], method: str) -> str:
        """Explain why the recommended method fits the gap."""
        if "interview" in method.lower():
            return (
                "Interviews allow deeper exploration of participant reasoning "
                "and can surface nuances that observation alone might miss."
            )
        elif "survey" in method.lower():
            return (
                "A survey provides broader coverage to validate whether patterns "
                "observed in a small sample hold at scale."
            )
        elif "usability" in method.lower():
            return (
                "Direct observation of task performance provides behavioral evidence "
                "to confirm or challenge current findings."
            )
        else:
            return (
                "This method provides contextual understanding that helps "
                "explain the observed gap in current evidence."
            )

    def _identify_risks(self, gap: dict[str, Any], method: str) -> list[str]:
        """Identify risks and limitations of the recommended study."""
        risks = []
        risks.append(
            "Recruitment challenges may limit access to target participant profile"
        )
        if "survey" in method.lower():
            risks.append(
                "Survey data lacks behavioral depth — consider supplementing "
                "with qualitative follow-ups"
            )
        if gap.get("priority") == "high":
            risks.append(
                "Delaying this research may lead to product decisions based on "
                "insufficient evidence"
            )
        return risks
