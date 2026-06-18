# ut-synthesizer Skill

## Purpose

The **ut-synthesizer** skill synthesizes validated findings into actionable insights and recommendations. It groups related findings, identifies patterns and themes, and generates prioritized recommendations for design improvements based on severity, frequency, and impact.

## Key Responsibilities

1. **Finding Synthesis**
   - Group related findings by theme or problem type
   - Identify patterns across participants and tasks
   - Consolidate similar issues into higher-level insights
   - Eliminate duplicate or redundant findings

2. **Pattern Recognition**
   - Cross-participant patterns: Issues affecting multiple users
   - Cross-task patterns: Problems recurring across different tasks
   - Workflow breakdowns: Systemic issues in user flows
   - Participant segmentation: Different issues for different user types

3. **Impact Assessment**
   - Business impact quantification
   - User experience impact analysis
   - Task completion impact measurement
   - Comparative analysis across findings

4. **Recommendation Generation**
   - Prioritized improvement suggestions
   - Implementation feasibility assessment
   - Expected impact estimation
   - Resource requirement estimation

5. **Insight Validation**
   - Cross-reference with original data
   - Ensure insights are grounded in evidence
   - Validate synthesis logic
   - Maintain traceability to source findings

## Input Format

```json
{
  "command": "synthesize_findings",
  "heuristic_batch_id": "heuristic_001",
  "synthesis_batch_id": "synthesis_001",
  "synthesis_config": {
    "grouping_method": "thematic",
    "min_finding_threshold": 2,
    "max_insights": 20,
    "prioritization_weights": {
      "severity": 0.4,
      "frequency": 0.3,
      "impact": 0.3
    }
  }
}
```

## Output Format

```json
{
  "synthesis_batch_id": "synthesis_001",
  "insights": [
    {
      "insight_id": "I_001",
      "title": "Discount Code Discovery and Application Issues",
      "theme": "checkout_flow",
      "severity": "critical",
      "description": "Multiple participants struggled to find and apply discount codes during checkout",
      "evidence": {
        "finding_ids": ["F_001", "F_003", "F_007"],
        "participant_count": 3,
        "task_count": 1,
        "severity_distribution": {"3": 2, "2": 1}
      },
      "patterns": {
        "cross_participant": "Consistent confusion about discount code location",
        "cross_task": "Issue isolated to checkout task",
        "workflow_impact": "Blocks final purchase completion"
      },
      "recommendations": [
        {
          "priority": "high",
          "description": "Move discount code field to more prominent location in checkout flow",
          "expected_impact": "Eliminate discount code discovery issues",
          "implementation_effort": "medium",
          "business_value": "Increase conversion rate for discounted purchases"
        },
        {
          "priority": "medium",
          "description": "Add visual cues and help text for discount code section",
          "expected_impact": "Reduce confusion and support requests",
          "implementation_effort": "low",
          "business_value": "Improve user satisfaction and reduce support costs"
        }
      ],
      "synthesized_at": "2026-05-08T14:30:00Z"
    }
  ],
  "synthesis_stats": {
    "total_findings_synthesized": 15,
    "insights_generated": 8,
    "findings_per_insight_avg": 1.9,
    "coverage_rate": 0.87,
    "priority_distribution": {
      "critical": 2,
      "high": 3,
      "medium": 2,
      "low": 1
    },
    "theme_distribution": {
      "checkout_flow": 3,
      "navigation": 2,
      "error_handling": 2,
      "content_discovery": 1
    }
  }
}
```

## Synthesis Methods

### Thematic Grouping
**Approach**: Group findings by common themes or problem types
**Criteria**:
- Similar user problems or pain points
- Related functionality or interface elements
- Common participant behaviors or comments

### Heuristic-Based Grouping
**Approach**: Group findings by violated usability heuristics
**Criteria**:
- Same primary heuristic violation
- Related secondary heuristics
- Similar design principle violations

### Workflow-Based Grouping
**Approach**: Group findings by user workflow or task sequence
**Criteria**:
- Same task or workflow step
- Sequential task dependencies
- Flow interruption points

### Participant Segmentation
**Approach**: Group findings by participant characteristics
**Criteria**:
- User experience level differences
- Task performance variations
- Demographic or behavioral patterns

## Pattern Recognition

### Cross-Participant Patterns
- Issues affecting multiple participants
- Consistent problem descriptions
- Similar behavioral responses
- Recurring quotes or complaints

### Cross-Task Patterns
- Problems appearing in multiple tasks
- Systemic design issues
- Inconsistent experiences
- Platform-wide usability problems

### Workflow Breakdowns
- Task sequence interruptions
- Flow abandonment points
- Error cascades
- Recovery difficulties

### Severity Patterns
- High-severity issue clusters
- Critical path problems
- Show-stopper identification
- Risk concentration areas

## Impact Assessment

### User Impact
- Task completion rates
- Time to completion variations
- Error frequency and recovery
- Satisfaction and frustration levels

### Business Impact
- Conversion rate effects
- Support request volumes
- User retention implications
- Revenue or productivity costs

### Comparative Analysis
- Issue frequency vs severity
- Impact across user segments
- Problem persistence over time
- Comparative benchmarking

## Recommendation Prioritization

### Priority Levels
- **Critical**: Immediate fix required, blocks core functionality
- **High**: Important fix, affects many users or key workflows
- **Medium**: Valuable improvement, affects some users
- **Low**: Nice-to-have, minimal impact

### Prioritization Factors
- Severity weighting (0.4): Higher severity = higher priority
- Frequency weighting (0.3): More users affected = higher priority
- Impact weighting (0.3): Greater business impact = higher priority

### Implementation Considerations
- Effort estimation: Low/Medium/High complexity
- Timeline assessment: Quick wins vs major projects
- Resource requirements: Design, development, testing needs
- Risk evaluation: Implementation complexity and user impact

## Integration Points

- **MCP Tools**: `load_heuristic_mappings`, `save_synthesis`, `get_pipeline_status`
- **State Management**: Persists synthesis results in `data/synthesis/`
- **ut-heuristic-mapper**: Uses heuristic groupings for synthesis
- **ut-reporter**: Provides synthesized insights for final report
- **Pattern Analysis**: Feeds into design strategy and prioritization

## Quality Metrics

- Synthesis coverage: % of findings incorporated into insights
- Insight consolidation: Average findings per insight
- Pattern validity: Cross-validation of identified patterns
- Recommendation quality: Actionability and feasibility scores
- Business alignment: Correlation with business objectives

## Example Usage

```python
from ut_analysis.skills.synthesizer import SynthesizerSkill

synthesizer = SynthesizerSkill()

# Synthesize findings into insights
result = synthesizer.synthesize_findings(
    heuristic_batch_id="heuristic_001",
    synthesis_batch_id="synthesis_001",
    synthesis_config={
        "grouping_method": "thematic",
        "min_finding_threshold": 2,
        "prioritization_weights": {
            "severity": 0.4,
            "frequency": 0.3,
            "impact": 0.3
        }
    }
)

# Check synthesis results
insights = result["insights"]
critical_insights = [i for i in insights if i["severity"] == "critical"]

print(f"Generated {len(insights)} insights, {len(critical_insights)} critical")
```

## Validation Rules

- All insights must be grounded in source findings
- Recommendations must be specific and actionable
- Priority assignments must be justified
- Patterns must be supported by evidence
- Synthesis must maintain traceability

## Error Handling

**Insufficient Data:**
- Reduce grouping thresholds for sparse data
- Generate individual finding insights
- Flag data limitations in results

**Conflicting Patterns:**
- Document alternative interpretations
- Choose most evidence-supported synthesis
- Note areas requiring additional research

**Over-Consolidation:**
- Prevent single insights from encompassing too many findings
- Maintain granularity for actionable recommendations
- Split large insights when appropriate

## Performance Considerations

- Batch synthesis: Process multiple mappings together
- Caching: Store heuristic data for repeated access
- Parallel processing: Synthesize independent finding groups
- Incremental synthesis: Add insights without reprocessing
- Memory management: Handle large finding datasets efficiently
