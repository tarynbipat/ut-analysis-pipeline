"""Theme orchestrator skill implementation for parallel thematic routing."""

import logging
from datetime import datetime
from typing import Any

from ut_analysis.models import (
    Finding,
    ThematicLane,
    ThemeLaneHandoffItem,
    ThemeOrchestrationPlan,
)
from ut_analysis.state_management import (
    StateManager,
    FindingsManager,
    ThemeOrchestrationManager,
)

logger = logging.getLogger(__name__)

LANE_CONFIG: dict[str, dict[str, Any]] = {
    "pain_points": {
        "assigned_agent": "ut-pain-point-analyst",
        "keywords": ["frustrat", "difficult", "confus", "error", "fail", "struggle", "annoy", "block"],
    },
    "user_needs": {
        "assigned_agent": "ut-needs-analyst",
        "keywords": ["need", "want", "expect", "wish", "prefer", "require", "hope"],
    },
    "behavioral_patterns": {
        "assigned_agent": "ut-behavior-analyst",
        "keywords": ["pattern", "repeat", "consistent", "always", "typically", "habit", "workaround"],
    },
    "mental_models": {
        "assigned_agent": "ut-mental-model-analyst",
        "keywords": ["think", "believe", "assume", "expect", "understand", "concept", "interpret"],
    },
    "trust_confidence": {
        "assigned_agent": "ut-trust-analyst",
        "keywords": ["trust", "confiden", "uncertain", "hesitat", "doubt", "comfort", "safe", "secure"],
    },
    "workflow_breakdowns": {
        "assigned_agent": "ut-workflow-analyst",
        "keywords": ["workflow", "step", "process", "sequence", "flow", "path", "abandon", "stuck"],
    },
}

CATEGORY_LANE_MAP = {
    "pain_point": ["pain_points"],
    "usability_issue": ["pain_points", "workflow_breakdowns"],
}


class ThemeOrchestratorSkill:
    """Coordinates parallel thematic analysis across specialist agents."""

    def __init__(
        self,
        state_manager: StateManager,
        findings_manager: FindingsManager | None = None,
        theme_orchestration_manager: ThemeOrchestrationManager | None = None,
    ) -> None:
        self.state_manager = state_manager
        self.findings_manager = findings_manager or FindingsManager(state_manager.project_dir / "data")
        self.theme_orchestration_manager = (
            theme_orchestration_manager
            or ThemeOrchestrationManager(state_manager.project_dir / "data")
        )

    def create_orchestration_plan(
        self, findings_batch_id: str, run_id: str, project_id: str
    ) -> dict[str, Any]:
        """Create a thematic orchestration plan from an extracted findings batch."""
        try:
            findings_data = self.findings_manager.load_findings(findings_batch_id)
            findings = [Finding(**finding_data) for finding_data in findings_data.get("findings", [])]

            plan_id = f"{run_id}_theme_orchestration"
            lane_buckets: dict[str, dict[str, Any]] = {
                lane_id: {
                    "assigned_agent": config["assigned_agent"],
                    "finding_ids": [],
                    "participant_ids": set(),
                    "task_ids": set(),
                    "handoff_items": [],
                    "matched_keywords": set(),
                }
                for lane_id, config in LANE_CONFIG.items()
            }

            for finding in findings:
                assignments = self._determine_lane_assignments(finding)
                for lane_id, matched_keywords in assignments.items():
                    lane_bucket = lane_buckets[lane_id]
                    lane_bucket["finding_ids"].append(finding.finding_id)
                    lane_bucket["participant_ids"].add(finding.participant_id)
                    if finding.task_id:
                        lane_bucket["task_ids"].add(finding.task_id)
                    lane_bucket["matched_keywords"].update(matched_keywords)
                    lane_bucket["handoff_items"].append(
                        ThemeLaneHandoffItem(
                            finding_id=finding.finding_id,
                            participant_id=finding.participant_id,
                            task_id=finding.task_id,
                            rationale=self._build_item_rationale(lane_id, matched_keywords, finding),
                        )
                    )

            thematic_lanes = [
                ThematicLane(
                    lane_id=lane_id,
                    lane_name=lane_id.replace("_", " "),
                    assigned_agent=lane_bucket["assigned_agent"],
                    finding_ids=lane_bucket["finding_ids"],
                    participant_ids=sorted(lane_bucket["participant_ids"]),
                    task_ids=sorted(lane_bucket["task_ids"]),
                    rationale=self._build_lane_rationale(
                        lane_id,
                        lane_bucket["matched_keywords"],
                        len(lane_bucket["finding_ids"]),
                    ),
                    handoff_items=lane_bucket["handoff_items"],
                )
                for lane_id, lane_bucket in lane_buckets.items()
                if lane_bucket["finding_ids"]
            ]

            plan = ThemeOrchestrationPlan(
                plan_id=plan_id,
                findings_batch_id=findings_batch_id,
                run_id=run_id,
                project_id=project_id,
                source_artifacts=[f"{findings_batch_id}_findings.json"],
                thematic_lanes=thematic_lanes,
                total_findings=len(findings),
                created_at=datetime.utcnow(),
            )

            plan_data = plan.model_dump(mode="json")
            self.theme_orchestration_manager.save_plan(plan_id, plan_data)
            self.state_manager.add_finding(
                f"{plan_id}_plan",
                {
                    "findings_batch_id": findings_batch_id,
                    "run_id": run_id,
                    "project_id": project_id,
                    "lane_count": len(thematic_lanes),
                    "total_findings": len(findings),
                },
            )

            logger.info(
                f"Created theme orchestration plan {plan_id} with {len(thematic_lanes)} lanes"
            )
            return plan_data

        except Exception as e:
            logger.error(f"Theme orchestration failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    def _determine_lane_assignments(self, finding: Finding) -> dict[str, set[str]]:
        """Determine thematic lane assignments for a finding."""
        text = f"{finding.title} {finding.description}".lower()
        assignments: dict[str, set[str]] = {}

        for lane_id, config in LANE_CONFIG.items():
            matched_keywords = {keyword for keyword in config["keywords"] if keyword in text}
            if matched_keywords:
                assignments[lane_id] = matched_keywords

        for lane_id in CATEGORY_LANE_MAP.get(finding.category.value, []):
            assignments.setdefault(lane_id, set()).add(f"category:{finding.category.value}")

        return assignments

    def _build_item_rationale(
        self, lane_id: str, matched_keywords: set[str], finding: Finding
    ) -> str:
        """Build handoff rationale for a routed finding."""
        reasons = sorted(matched_keywords) if matched_keywords else [f"category:{finding.category.value}"]
        return f"Assigned to {lane_id} based on signals: {', '.join(reasons)}"

    def _build_lane_rationale(
        self, lane_id: str, matched_keywords: set[str], finding_count: int
    ) -> str:
        """Build summary rationale for a thematic lane."""
        if matched_keywords:
            keyword_summary = ", ".join(sorted(matched_keywords))
            return (
                f"{finding_count} findings routed to {lane_id} based on matched signals: "
                f"{keyword_summary}"
            )
        return f"{finding_count} findings routed to {lane_id} based on category-level signals"
