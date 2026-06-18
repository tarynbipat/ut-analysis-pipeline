# ut-reporter Skill

## Purpose

The **ut-reporter** skill generates comprehensive usability test analysis reports from synthesized insights. It creates executive summaries, detailed findings reports, and actionable recommendations formatted for different audiences (executives, designers, developers, stakeholders).

## Key Responsibilities

1. **Report Generation**
   - Executive summaries for leadership
   - Detailed technical reports for design teams
   - Implementation roadmaps for developers
   - Stakeholder communication materials

2. **Content Structuring**
   - Study overview and methodology
   - Key findings and insights
   - Prioritized recommendations
   - Impact assessments and metrics

3. **Multiple Output Formats**
   - Markdown reports for documentation
   - JSON data exports for integration
   - HTML reports for web viewing
   - PDF reports for formal distribution

4. **Audience Adaptation**
   - Executive summaries: High-level insights, business impact, ROI
   - Design teams: Detailed findings, user quotes, design recommendations
   - Development teams: Technical requirements, implementation priorities
   - Stakeholders: Progress updates, success metrics, next steps

5. **Visualization Support**
   - Severity distribution charts
   - Finding frequency graphs
   - Timeline visualizations
   - Impact assessment matrices

## Input Format

```json
{
  "command": "generate_report",
  "synthesis_batch_id": "synthesis_001",
  "report_batch_id": "report_001",
  "report_config": {
    "report_types": ["executive", "detailed", "technical"],
    "output_formats": ["markdown", "json"],
    "include_visualizations": true,
    "audience_focus": "mixed",
    "detail_level": "comprehensive"
  }
}
```

## Output Format

```json
{
  "report_batch_id": "report_001",
  "reports": {
    "executive_summary": {
      "title": "Usability Test Executive Summary",
      "sections": [
        {
          "heading": "Study Overview",
          "content": "Usability testing conducted with 5 participants across 8 tasks...",
          "key_metrics": {
            "task_completion_rate": "87%",
            "average_severity_score": "2.1",
            "critical_findings": "3"
          }
        },
        {
          "heading": "Key Findings",
          "content": "Three critical issues identified in checkout flow...",
          "insights": [
            {
              "title": "Checkout Flow Blockers",
              "impact": "High",
              "recommendation": "Redesign discount code application process"
            }
          ]
        }
      ],
      "generated_at": "2026-05-08T14:30:00Z"
    },
    "detailed_report": {
      "title": "Detailed Usability Analysis Report",
      "sections": [...],
      "appendices": [...]
    }
  },
  "report_stats": {
    "total_reports_generated": 3,
    "insights_covered": 8,
    "recommendations_prioritized": 12,
    "output_formats": ["markdown", "json"]
  }
}
```

## Report Types

### Executive Summary
**Purpose**: High-level overview for leadership and stakeholders
**Content**:
- Study methodology summary
- Key metrics and KPIs
- Critical findings and business impact
- High-priority recommendations
- Next steps and timeline

**Length**: 2-3 pages
**Tone**: Business-focused, actionable
**Visuals**: Executive dashboards, impact charts

### Detailed Report
**Purpose**: Comprehensive analysis for design and product teams
**Content**:
- Full methodology description
- All findings with evidence
- User quotes and behavioral data
- Thematic analysis and patterns
- Detailed recommendations with rationale

**Length**: 10-20 pages
**Tone**: Analytical, evidence-based
**Visuals**: Finding matrices, user journey maps

### Technical Report
**Purpose**: Implementation guidance for development teams
**Content**:
- Technical requirements for fixes
- Code-level recommendations
- Implementation priorities and dependencies
- Testing and validation criteria
- Resource estimates

**Length**: 15-25 pages
**Tone**: Technical, specific
**Visuals**: System architecture diagrams, implementation flowcharts

### Stakeholder Report
**Purpose**: Progress updates and communication materials
**Content**:
- Project status and milestones
- Success metrics and KPIs
- Risk assessments and mitigation
- Timeline and resource needs
- Communication plans

**Length**: 5-10 pages
**Tone**: Collaborative, forward-looking
**Visuals**: Timeline charts, status dashboards

## Content Organization

### Study Overview Section
- Test objectives and scope
- Participant demographics
- Task scenarios and success criteria
- Methodology and tools used

### Findings Section
- Severity-ranked findings
- Evidence and user quotes
- Impact assessments
- Cross-references to heuristics

### Insights Section
- Thematic groupings
- Pattern analysis
- Root cause identification
- Comparative analysis

### Recommendations Section
- Prioritized action items
- Implementation guidance
- Expected impact estimates
- Success metrics

### Appendices
- Raw data exports
- Detailed methodologies
- Participant details
- Full finding lists

## Output Formats

### Markdown Format
**Advantages**: Version controllable, readable, flexible
**Structure**:
- Front matter with metadata
- Section headers and content
- Embedded visualizations
- Table of contents

### JSON Format
**Advantages**: Machine-readable, integrable, structured
**Structure**:
- Complete data export
- Nested object hierarchy
- Standardized schemas
- API-ready format

### HTML Format
**Advantages**: Web-viewable, interactive, styled
**Structure**:
- Responsive design
- Interactive charts
- Collapsible sections
- Print-friendly styling

### PDF Format
**Advantages**: Formal, distributable, archivable
**Structure**:
- Professional layout
- Embedded charts and graphics
- Table of contents
- Page headers/footers

## Visualization Types

### Severity Distribution Chart
- Bar chart showing finding counts by severity level
- Color-coded by Nielsen scale
- Percentage breakdowns

### Finding Frequency Matrix
- Heat map of findings by task and participant
- Severity color coding
- Completion rate overlays

### Timeline Visualization
- Chronological view of findings during sessions
- Task boundaries marked
- Severity progression shown

### Impact Assessment Matrix
- Scatter plot of severity vs frequency
- Bubble size representing user impact
- Quadrant analysis for prioritization

## Integration Points

- **MCP Tools**: `load_synthesis`, `save_reports`, `get_pipeline_status`
- **State Management**: Persists reports in `data/reports/`
- **ut-synthesizer**: Uses synthesized insights as input
- **External Tools**: Integrates with document generation libraries
- **File System**: Saves reports to project directories

## Quality Metrics

- Report completeness: All required sections present
- Content accuracy: Facts verified against source data
- Readability scores: Appropriate for target audience
- Actionability: Recommendations are specific and implementable
- Stakeholder satisfaction: Feedback from report recipients

## Example Usage

```python
from ut_analysis.skills.reporter import ReporterSkill

reporter = ReporterSkill()

# Generate comprehensive reports
result = reporter.generate_report(
    synthesis_batch_id="synthesis_001",
    report_batch_id="report_001",
    report_config={
        "report_types": ["executive", "detailed"],
        "output_formats": ["markdown", "json"],
        "include_visualizations": True,
        "audience_focus": "design_team"
    }
)

# Check generated reports
reports = result["reports"]
print(f"Generated {len(reports)} report types")
```

## Validation Rules

- All reports must include required sections
- Data accuracy verified against source insights
- Recommendations traceable to findings
- Visualizations properly labeled and explained
- Formats validated for correctness

## Error Handling

**Missing Data:**
- Generate reports with available information
- Flag data gaps in report content
- Provide data collection recommendations

**Format Errors:**
- Fallback to basic formats if advanced formatting fails
- Validate output files before completion
- Log formatting issues for debugging

**Content Issues:**
- Verify all insights have required fields
- Handle missing recommendations gracefully
- Ensure report structure remains intact

## Performance Considerations

- Batch report generation: Process multiple formats together
- Memory management: Handle large insight datasets
- File I/O optimization: Stream large reports to disk
- Template caching: Reuse report templates when possible
- Parallel processing: Generate different report types concurrently
