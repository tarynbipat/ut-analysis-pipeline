"""Reporter skill implementation for generating usability test reports."""

import logging
from typing import Any, Optional, Dict, List
from datetime import datetime
from pathlib import Path
import json

from ut_analysis.models import (
    SynthesisInsight,
    ReportSection,
    ReportMetadata,
)
from ut_analysis.state_management import (
    StateManager,
    SynthesisManager,
    ReportManager,
)

logger = logging.getLogger(__name__)


class ReporterSkill:
    """Generates comprehensive usability test analysis reports."""

    def __init__(
        self,
        state_manager: StateManager,
        synthesis_manager: SynthesisManager | None = None,
        report_manager: ReportManager | None = None,
    ) -> None:
        self.state_manager = state_manager
        self.synthesis_manager = synthesis_manager or SynthesisManager(
            state_manager.project_dir / "data"
        )
        self.report_manager = report_manager or ReportManager(
            state_manager.project_dir / "data"
        )

    def generate_report(
        self,
        synthesis_batch_id: str,
        report_batch_id: str = "report_default",
        report_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generate usability test reports."""
        try:
            # Load synthesis data
            synthesis_data = self.synthesis_manager.load_synthesis(synthesis_batch_id)
            insights = [
                SynthesisInsight(**i) for i in synthesis_data.get("insights", [])
            ]

            # Default report config
            if report_config is None:
                report_config = {
                    "report_types": ["executive", "detailed"],
                    "output_formats": ["markdown", "json"],
                    "include_visualizations": True,
                    "audience_focus": "mixed",
                    "detail_level": "comprehensive",
                }

            # Generate requested report types
            reports = {}
            for report_type in report_config["report_types"]:
                if report_type == "executive":
                    reports["executive_summary"] = self._generate_executive_summary(
                        insights, synthesis_data
                    )
                elif report_type == "detailed":
                    reports["detailed_report"] = self._generate_detailed_report(
                        insights, synthesis_data
                    )
                elif report_type == "technical":
                    reports["technical_report"] = self._generate_technical_report(
                        insights, synthesis_data
                    )

            # Generate output formats
            output_files = []
            for format_type in report_config["output_formats"]:
                if format_type == "markdown":
                    output_files.extend(self._export_markdown_reports(reports, report_batch_id))
                elif format_type == "json":
                    output_files.extend(self._export_json_reports(reports, report_batch_id))

            # Calculate report statistics
            stats = self._calculate_report_stats(reports, insights)

            # Prepare result
            result = {
                "report_batch_id": report_batch_id,
                "reports": reports,
                "output_files": output_files,
                "report_stats": stats,
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Save report metadata
            self.report_manager.save_report_metadata(report_batch_id, result)

            # Update state
            self.state_manager.add_finding(f"{report_batch_id}_report", {
                "report_types": list(reports.keys()),
                "output_formats": report_config["output_formats"],
                "insights_covered": len(insights),
            })

            logger.info(f"Generated {len(reports)} reports in batch {report_batch_id}")

            return result

        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            return {"status": "error", "error": str(e)}

    def _generate_executive_summary(
        self, insights: List[SynthesisInsight], synthesis_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate executive summary report."""
        # Calculate key metrics
        total_insights = len(insights)
        critical_insights = sum(1 for i in insights if i.severity == "critical")
        high_insights = sum(1 for i in insights if i.severity in ["critical", "high"])

        # Synthesis stats
        synth_stats = synthesis_data.get("synthesis_stats", {})

        sections = [
            ReportSection(
                heading="Study Overview",
                content=self._generate_study_overview(synth_stats),
                key_metrics={
                    "total_insights": total_insights,
                    "critical_findings": critical_insights,
                    "task_completion_rate": synth_stats.get("task_completion_rate", "N/A"),
                },
            ),
            ReportSection(
                heading="Key Findings",
                content=self._generate_key_findings_summary(insights[:5]),  # Top 5 insights
                insights=self._format_top_insights(insights[:3]),  # Top 3 for executives
            ),
            ReportSection(
                heading="Business Impact",
                content=self._generate_business_impact_summary(insights),
                key_metrics={
                    "high_priority_issues": high_insights,
                    "affected_user_flows": len(set(i.theme for i in insights)),
                },
            ),
            ReportSection(
                heading="Recommendations",
                content=self._generate_executive_recommendations(insights),
            ),
        ]

        return {
            "title": "Usability Test Executive Summary",
            "sections": [s.model_dump() for s in sections],
            "generated_at": datetime.utcnow().isoformat(),
        }

    def _generate_detailed_report(
        self, insights: List[SynthesisInsight], synthesis_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate detailed analysis report."""
        sections = [
            ReportSection(
                heading="Methodology",
                content=self._generate_methodology_section(synthesis_data),
            ),
            ReportSection(
                heading="Detailed Findings",
                content=self._generate_detailed_findings(insights),
                insights=[self._format_detailed_insight(i) for i in insights],
            ),
            ReportSection(
                heading="Pattern Analysis",
                content=self._generate_pattern_analysis(insights),
            ),
            ReportSection(
                heading="Recommendations",
                content=self._generate_detailed_recommendations(insights),
            ),
        ]

        appendices = [
            {
                "title": "Raw Data Export",
                "content": "Complete dataset available in project data directory",
            },
            {
                "title": "Participant Details",
                "content": "Detailed participant information and demographics",
            },
        ]

        return {
            "title": "Detailed Usability Analysis Report",
            "sections": [s.model_dump() for s in sections],
            "appendices": appendices,
            "generated_at": datetime.utcnow().isoformat(),
        }

    def _generate_technical_report(
        self, insights: List[SynthesisInsight], synthesis_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate technical implementation report."""
        sections = [
            ReportSection(
                heading="Technical Requirements",
                content=self._generate_technical_requirements(insights),
            ),
            ReportSection(
                heading="Implementation Roadmap",
                content=self._generate_implementation_roadmap(insights),
            ),
            ReportSection(
                heading="Testing and Validation",
                content=self._generate_testing_criteria(insights),
            ),
        ]

        return {
            "title": "Technical Implementation Report",
            "sections": [s.model_dump() for s in sections],
            "generated_at": datetime.utcnow().isoformat(),
        }

    def _generate_study_overview(self, synth_stats: Dict[str, Any]) -> str:
        """Generate study overview content."""
        total_findings = synth_stats.get("total_findings_synthesized", 0)
        insights_generated = synth_stats.get("insights_generated", 0)

        return f"""Usability testing analysis completed with {total_findings} findings synthesized into {insights_generated} key insights.

The analysis covered multiple user tasks and identified patterns across participant experiences. Findings were evaluated using Nielsen's severity scale and mapped to usability heuristics."""

    def _generate_key_findings_summary(self, insights: List[SynthesisInsight]) -> str:
        """Generate key findings summary."""
        critical_count = sum(1 for i in insights if i.severity == "critical")
        high_count = sum(1 for i in insights if i.severity == "high")

        themes = list(set(i.theme for i in insights))

        return f"""Analysis revealed {critical_count} critical and {high_count} high-priority issues across {len(themes)} key themes: {', '.join(themes)}.

Most significant findings include workflow blockages and user experience barriers that impact task completion rates."""

    def _generate_business_impact_summary(self, insights: List[SynthesisInsight]) -> str:
        """Generate business impact summary."""
        critical_insights = [i for i in insights if i.severity == "critical"]

        if critical_insights:
            impact_areas = list(set(i.theme for i in critical_insights))
            return f"""Critical issues identified in: {', '.join(impact_areas)}.

These findings represent significant barriers to user success and require immediate attention to prevent business impact on user satisfaction and conversion rates."""
        else:
            return "No critical issues identified. Focus should be on high-priority improvements to enhance user experience."

    def _generate_executive_recommendations(self, insights: List[SynthesisInsight]) -> str:
        """Generate executive-level recommendations."""
        high_priority = [i for i in insights if i.severity in ["critical", "high"]]

        if high_priority:
            top_recs = []
            for insight in high_priority[:3]:
                if insight.recommendations:
                    top_recs.append(insight.recommendations[0].description)

            return f"""Immediate priorities:

{chr(10).join(f'• {rec}' for rec in top_recs)}

Allocate resources for these high-impact improvements to maximize user experience ROI."""
        else:
            return "Focus on incremental improvements identified in the detailed findings to enhance overall user satisfaction."

    def _generate_methodology_section(self, synthesis_data: Dict[str, Any]) -> str:
        """Generate methodology section."""
        return """Usability testing followed established research methodology:

• Findings extracted from participant transcripts and observation notes
• 5-check validation process ensuring finding accuracy
• Nielsen severity rating for impact assessment
• Heuristic mapping to usability principles
• Thematic synthesis of related findings

All findings include verbatim participant quotes and are traceable to source materials."""

    def _generate_detailed_findings(self, insights: List[SynthesisInsight]) -> str:
        """Generate detailed findings content."""
        total_findings = sum(len(i.evidence.finding_ids) for i in insights)

        return f"""Analysis identified {len(insights)} distinct insights from {total_findings} individual findings.

Findings are organized by severity and thematic patterns, with each insight including:
• Detailed description and user impact
• Supporting evidence and participant quotes
• Cross-participant and cross-task patterns
• Specific design recommendations"""

    def _generate_pattern_analysis(self, insights: List[SynthesisInsight]) -> str:
        """Generate pattern analysis content."""
        themes = {}
        for insight in insights:
            theme = insight.theme
            themes[theme] = themes.get(theme, 0) + 1

        theme_summary = ", ".join(f"{theme}: {count}" for theme, count in themes.items())

        return f"""Pattern analysis revealed thematic groupings: {theme_summary}

Key patterns include:
• Cross-participant consistency in critical issues
• Task-specific workflow blockages
• Systemic design principle violations
• Opportunities for holistic design improvements"""

    def _generate_detailed_recommendations(self, insights: List[SynthesisInsight]) -> str:
        """Generate detailed recommendations."""
        total_recs = sum(len(i.recommendations) for i in insights)

        return f"""Generated {total_recs} specific recommendations prioritized by impact and implementation effort.

Recommendations include:
• Immediate fixes for critical issues
• Design improvements for user experience enhancement
• Technical implementation guidance
• Success metrics and validation criteria"""

    def _generate_technical_requirements(self, insights: List[SynthesisInsight]) -> str:
        """Generate technical requirements."""
        return """Technical implementation requirements:

• Frontend: UI/UX modifications for identified issues
• Backend: API changes for improved functionality
• Database: Data structure updates if needed
• Testing: Validation criteria for implemented fixes
• Documentation: Updated user guidance materials"""

    def _generate_implementation_roadmap(self, insights: List[SynthesisInsight]) -> str:
        """Generate implementation roadmap."""
        critical_insights = [i for i in insights if i.severity == "critical"]
        high_insights = [i for i in insights if i.severity == "high"]

        roadmap = "Implementation Roadmap:\n\n"

        if critical_insights:
            roadmap += "Phase 1 (Immediate - 1-2 weeks):\n"
            for insight in critical_insights:
                if insight.recommendations:
                    roadmap += f"• {insight.recommendations[0].description}\n"

        if high_insights:
            roadmap += "\nPhase 2 (Short-term - 2-4 weeks):\n"
            for insight in high_insights:
                if insight.recommendations:
                    roadmap += f"• {insight.recommendations[0].description}\n"

        return roadmap

    def _generate_testing_criteria(self, insights: List[SynthesisInsight]) -> str:
        """Generate testing and validation criteria."""
        return """Validation Criteria:

• User testing: Re-test critical user flows after implementation
• Success metrics: Task completion rates, error rates, user satisfaction
• Regression testing: Ensure fixes don't introduce new issues
• Accessibility testing: Verify improvements for all user groups
• Performance testing: Confirm no degradation in system performance"""

    def _format_top_insights(self, insights: List[SynthesisInsight]) -> List[Dict[str, Any]]:
        """Format insights for executive summary."""
        formatted = []
        for insight in insights:
            formatted.append({
                "title": insight.title,
                "impact": insight.severity.title(),
                "recommendation": insight.recommendations[0].description if insight.recommendations else "TBD",
            })
        return formatted

    def _format_detailed_insight(self, insight: SynthesisInsight) -> Dict[str, Any]:
        """Format insight for detailed report."""
        return {
            "title": insight.title,
            "severity": insight.severity,
            "description": insight.description,
            "evidence": {
                "findings_count": len(insight.evidence.finding_ids),
                "participants_affected": insight.evidence.participant_count,
                "severity_breakdown": insight.evidence.severity_distribution,
            },
            "patterns": insight.patterns.model_dump(),
            "recommendations": [r.model_dump() for r in insight.recommendations],
        }

    def _export_markdown_reports(self, reports: Dict[str, Any], batch_id: str) -> List[str]:
        """Export reports in Markdown format."""
        output_files = []

        for report_name, report_data in reports.items():
            filename = f"{batch_id}_{report_name}.md"
            filepath = self.state_manager.project_dir / "reports" / filename

            # Generate markdown content
            content = self._generate_markdown_content(report_data)

            # Save file
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

            output_files.append(str(filepath))

        return output_files

    def _export_json_reports(self, reports: Dict[str, Any], batch_id: str) -> List[str]:
        """Export reports in JSON format."""
        output_files = []

        for report_name, report_data in reports.items():
            filename = f"{batch_id}_{report_name}.json"
            filepath = self.state_manager.project_dir / "reports" / filename

            # Save JSON
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, default=str)

            output_files.append(str(filepath))

        return output_files

    def _generate_markdown_content(self, report_data: Dict[str, Any]) -> str:
        """Generate Markdown content for report."""
        content = f"# {report_data['title']}\n\n"
        content += f"Generated: {report_data['generated_at']}\n\n"

        for section in report_data.get('sections', []):
            content += f"## {section['heading']}\n\n"
            content += f"{section['content']}\n\n"

            if 'key_metrics' in section:
                content += "### Key Metrics\n\n"
                for key, value in section['key_metrics'].items():
                    content += f"- **{key.replace('_', ' ').title()}**: {value}\n"
                content += "\n"

            if 'insights' in section:
                content += "### Insights\n\n"
                for insight in section['insights']:
                    content += f"- **{insight['title']}** ({insight.get('impact', 'Unknown')} impact)\n"
                    if 'recommendation' in insight:
                        content += f"  - {insight['recommendation']}\n"
                content += "\n"

        return content

    def _calculate_report_stats(
        self, reports: Dict[str, Any], insights: List[SynthesisInsight]
    ) -> Dict[str, Any]:
        """Calculate report generation statistics."""
        total_reports = len(reports)
        total_insights = len(insights)

        # Count recommendations
        total_recs = sum(
            len(insight.recommendations) for insight in insights
        )

        # Report types generated
        report_types = list(reports.keys())

        return {
            "total_reports_generated": total_reports,
            "insights_covered": total_insights,
            "recommendations_prioritized": total_recs,
            "report_types": report_types,
        }
