"""Pipeline run summary skill implementation."""

import logging
from datetime import datetime
from typing import Any

from ut_analysis.state_management import PipelineRunManager, StateManager

logger = logging.getLogger(__name__)


class RunSummarySkill:
    """Generates observable pipeline run summaries."""

    def __init__(
        self,
        state_manager: StateManager,
        run_manager: PipelineRunManager | None = None,
    ) -> None:
        self.state_manager = state_manager
        self.run_manager = run_manager or PipelineRunManager(
            state_manager.project_dir / "data"
        )

    def generate_run_summary(
        self,
        run_id: str,
        project_id: str,
        stages_completed: list[str] | None = None,
        artifacts_created: list[str] | None = None,
        agents_invoked: list[str] | None = None,
        evals_passed: int = 0,
        evals_failed: int = 0,
        review_checkpoints_created: int = 0,
        unresolved_issues: list[str] | None = None,
    ) -> dict[str, Any]:
        """Generate and persist a pipeline run summary."""
        try:
            next_action = self._suggest_next_action(
                stages_completed or [],
                evals_failed,
                review_checkpoints_created,
                unresolved_issues or [],
            )

            summary = {
                "run_id": run_id,
                "project_id": project_id,
                "stages_completed": stages_completed or [],
                "artifacts_created": artifacts_created or [],
                "agents_invoked": agents_invoked or [],
                "evals_passed": evals_passed,
                "evals_failed": evals_failed,
                "review_checkpoints_created": review_checkpoints_created,
                "unresolved_issues": unresolved_issues or [],
                "next_suggested_action": next_action,
                "created_at": datetime.utcnow().isoformat(),
            }

            self.run_manager.save_run_summary(run_id, summary)

            md_content = self._render_markdown(summary)
            md_path = self.run_manager.runs_dir / f"{run_id}_run_summary.md"
            with open(md_path, "w", encoding="utf-8") as file_handle:
                file_handle.write(md_content)

            return summary

        except Exception as exc:
            logger.error("Run summary generation failed: %s", exc)
            return {"status": "error", "error": str(exc)}

    def _suggest_next_action(
        self,
        stages: list[str],
        evals_failed: int,
        checkpoints_created: int,
        unresolved: list[str],
    ) -> str:
        """Suggest next action based on run state."""
        if evals_failed > 0:
            return (
                f"Address {evals_failed} failed evaluation(s) before proceeding. "
                "Review eval_results.json for details."
            )
        if checkpoints_created > 0:
            return (
                f"Review {checkpoints_created} human review checkpoint(s). "
                "Approve or revise before final reporting."
            )
        if unresolved:
            return f"Resolve {len(unresolved)} outstanding issue(s): {unresolved[0]}"

        if "reporting" not in " ".join(stages).lower():
            return "Generate final research intelligence report."
        return "Pipeline complete. Share report with stakeholders."

    def _render_markdown(self, summary: dict[str, Any]) -> str:
        """Render run summary as readable markdown."""
        lines = [
            f"# Pipeline Run Summary: {summary['run_id']}",
            "",
            f"**Project:** {summary['project_id']}",
            f"**Generated:** {summary['created_at']}",
            "",
            "## Stages Completed",
            "",
        ]

        for stage in summary["stages_completed"]:
            lines.append(f"- ✓ {stage}")

        lines.extend(
            [
                "",
                "## Artifacts Created",
                "",
            ]
        )
        for artifact in summary["artifacts_created"]:
            lines.append(f"- {artifact}")

        lines.extend(
            [
                "",
                "## Agents Invoked",
                "",
            ]
        )
        for agent in summary["agents_invoked"]:
            lines.append(f"- {agent}")

        lines.extend(
            [
                "",
                "## Evaluation Results",
                "",
                f"- Passed: {summary['evals_passed']}",
                f"- Failed: {summary['evals_failed']}",
                "",
                (
                    "## Review Checkpoints Created: "
                    f"{summary['review_checkpoints_created']}"
                ),
                "",
            ]
        )

        if summary["unresolved_issues"]:
            lines.append("## Unresolved Issues")
            lines.append("")
            for issue in summary["unresolved_issues"]:
                lines.append(f"- ⚠️ {issue}")
            lines.append("")

        lines.extend(
            [
                "## Next Suggested Action",
                "",
                f"> {summary['next_suggested_action']}",
                "",
            ]
        )

        return "\n".join(lines)
