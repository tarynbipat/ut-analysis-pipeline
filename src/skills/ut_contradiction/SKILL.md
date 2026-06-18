# ut-contradiction Skill

## Purpose

The **ut-contradiction** skill identifies contradictions, inconsistencies, and conflicts within usability test data. It analyzes findings across participants, tasks, and data sources to detect patterns of disagreement, conflicting user behaviors, and potential data quality issues that could affect analysis validity.

## Key Responsibilities

1. **Contradiction Detection**
   - Cross-participant inconsistencies in behavior patterns
   - Conflicting success/failure reports for same tasks
   - Contradictory user feedback and observations
   - Inconsistent severity ratings across similar findings

2. **Pattern Analysis**
   - Identify systematic vs random inconsistencies
   - Detect participant-specific vs task-specific patterns
   - Analyze temporal inconsistencies within sessions
   - Cross-reference findings with transcripts and notes

3. **Data Quality Assessment**
   - Evaluate finding reliability and consistency
   - Identify potential observer bias or data collection errors
   - Assess inter-rater reliability across evaluators
   - Flag findings requiring additional verification

4. **Conflict Resolution**
   - Prioritize findings based on consistency and reliability
   - Suggest additional research for contradictory areas
   - Provide confidence scores for findings
   - Generate validation recommendations

5. **Reporting and Visualization**
   - Create contradiction matrices and heatmaps
   - Generate consistency reports
   - Visualize agreement/disagreement patterns
   - Provide actionable insights for data quality improvement

## Input Format

```json
{
  "command": "analyze_contradictions",
  "findings_batch_id": "batch_001",
  "contradictions_batch_id": "contra_001",
  "analysis_config": {
    "analysis_scope": "full",
    "consistency_threshold": 0.8,
    "include_participant_analysis": true,
    "include_temporal_analysis": true,
    "cross_reference_sources": ["transcripts", "notes", "observations"],
    "output_detail_level": "comprehensive"
  }
}
```

## Output Format

```json
{
  "contradictions_batch_id": "contra_001",
  "contradiction_analysis": {
    "overall_consistency_score": 0.85,
    "total_findings_analyzed": 45,
    "contradictions_identified": 8,
    "consistency_distribution": {
      "highly_consistent": 32,
      "moderately_consistent": 10,
      "inconsistent": 3
    }
  },
  "contradictions": [
    {
      "contradiction_id": "CONTRA_001",
      "type": "participant_disagreement",
      "severity": "high",
      "description": "Conflicting success rates for checkout completion task",
      "affected_findings": ["F_001", "F_015", "F_022"],
      "evidence": {
        "participant_agreement": {
          "P001": "success",
          "P002": "failure",
          "P003": "success",
          "P004": "failure"
        },
        "consistency_score": 0.5,
        "pattern_type": "split_opinion"
      },
      "analysis": {
        "possible_causes": [
          "Task ambiguity in instructions",
          "Different user approaches to same goal",
          "Context-dependent success factors"
        ],
        "recommended_action": "Clarify task instructions and add success criteria",
        "confidence_impact": "medium",
        "validation_needed": true
      },
      "resolution_suggestions": [
        {
          "approach": "Task Refinement",
          "description": "Provide clearer task instructions with specific success criteria",
          "expected_improvement": "Reduce contradiction by 70%"
        },
        {
          "approach": "Context Analysis",
          "description": "Analyze participant context differences causing varied outcomes",
          "expected_improvement": "Identify root causes for inconsistent results"
        }
      ],
      "detected_at": "2026-05-08T14:30:00Z"
    }
  ],
  "consistency_patterns": {
    "participant_consistency": {
      "P001": 0.92,
      "P002": 0.78,
      "P003": 0.85,
      "P004": 0.71
    },
    "task_consistency": {
      "TASK-001": 0.95,
      "TASK-002": 0.82,
      "TASK-003": 0.68,
      "TASK-004": 0.88
    },
    "finding_type_consistency": {
      "navigation": 0.91,
      "checkout": 0.73,
      "search": 0.86,
      "error_handling": 0.79
    }
  },
  "data_quality_assessment": {
    "overall_reliability": 0.83,
    "inter_rater_agreement": 0.89,
    "temporal_stability": 0.91,
    "cross_source_consistency": 0.87,
    "recommendations": [
      "Improve task instruction clarity",
      "Add participant context collection",
      "Implement dual observation for critical tasks",
      "Standardize success criteria definitions"
    ]
  },
  "validation_recommendations": {
    "immediate_actions": [
      "Retest checkout task with clarified instructions",
      "Review participant recruitment criteria",
      "Add context questions to test protocol"
    ],
    "long_term_improvements": [
      "Implement standardized task library",
      "Add automated consistency checking",
      "Train observers on bias recognition",
      "Establish inter-rater reliability protocols"
    ]
  }
}
```

## Contradiction Types

### Participant Disagreements
**Pattern**: Different participants experience different outcomes for same task
**Examples**:
- Some succeed, some fail at identical tasks
- Conflicting preferences or opinions
- Different interpretation of task requirements

### Temporal Inconsistencies
**Pattern**: Same participant shows inconsistent behavior over time
**Examples**:
- Participant succeeds then fails at same task
- Changing opinions during session
- Learning effects or fatigue impacts

### Observer Discrepancies
**Pattern**: Different observers record different observations
**Examples**:
- Conflicting notes from dual observation
- Different severity ratings for same behavior
- Missing observations in one record

### Source Conflicts
**Pattern**: Transcripts, notes, and findings don't align
**Examples**:
- Finding not supported by transcript evidence
- Contradictory information across data sources
- Missing context in one source

### Cross-Task Inconsistencies
**Pattern**: Findings contradict each other across related tasks
**Examples**:
- Success in one task contradicts failure in related task
- Conflicting user mental models
- Inconsistent system behavior observations

## Analysis Methods

### Consistency Scoring
**Agreement Metrics**:
- Percentage agreement across participants
- Inter-rater reliability scores
- Cross-source consistency measures
- Temporal stability assessments

### Pattern Recognition
**Statistical Analysis**:
- Chi-square tests for independence
- Correlation analysis between variables
- Cluster analysis for behavior patterns
- Outlier detection for inconsistent data

### Contextual Analysis
**Qualitative Assessment**:
- Task instruction clarity evaluation
- Participant context differences
- System state variations
- Observer bias identification

## Quality Assessment Framework

### Data Reliability Metrics
- **Internal Consistency**: Agreement within single data source
- **External Consistency**: Agreement across multiple sources
- **Temporal Consistency**: Stability over time
- **Inter-Rater Reliability**: Agreement between observers

### Confidence Scoring
- **High Confidence**: Consistent across all sources and participants
- **Medium Confidence**: Some inconsistencies but explainable
- **Low Confidence**: Significant contradictions requiring validation
- **Unreliable**: Major conflicts suggesting data quality issues

## Resolution Strategies

### Immediate Actions
- **Task Refinement**: Clarify ambiguous instructions
- **Additional Data Collection**: Gather missing context
- **Participant Follow-up**: Interview for clarification
- **Observer Training**: Address bias or inconsistency issues

### Long-term Improvements
- **Protocol Standardization**: Consistent test procedures
- **Training Programs**: Observer calibration and bias training
- **Tool Implementation**: Automated consistency checking
- **Quality Assurance**: Multi-level review processes

## Integration Points

- **MCP Tools**: `load_findings`, `analyze_contradictions`, `save_contradictions`
- **State Management**: Persists contradiction analysis in `data/contradictions/`
- **ut-evaluator**: Uses consistency scores for finding validation
- **ut-synthesizer**: Incorporates contradiction analysis in insights
- **External Tools**: Statistical analysis libraries, data visualization tools

## Quality Metrics

- Contradiction detection accuracy: % of real inconsistencies identified
- False positive rate: % of false contradictions flagged
- Resolution effectiveness: % of contradictions successfully addressed
- Data quality improvement: Measured improvement in consistency scores
- Analysis efficiency: Processing time per finding batch

## Example Usage

```python
from ut_analysis.skills.contradiction import ContradictionSkill

contradiction_analyzer = ContradictionSkill()

# Analyze contradictions in findings
result = contradiction_analyzer.analyze_contradictions(
    findings_batch_id="batch_001",
    contradictions_batch_id="contra_001",
    analysis_config={
        "analysis_scope": "full",
        "consistency_threshold": 0.8,
        "include_participant_analysis": True,
        "cross_reference_sources": ["transcripts", "notes"]
    }
)

# Check for critical contradictions
critical_contra = [c for c in result["contradictions"] if c["severity"] == "high"]
print(f"Found {len(critical_contra)} critical contradictions requiring attention")
```

## Validation Rules

- All contradictions must be supported by evidence
- Consistency scores must be calculated using valid methods
- Resolution suggestions must be actionable
- Data quality assessments must be based on measurable criteria
- Confidence impacts must be clearly explained

## Error Handling

**Data Quality Issues:**
- Flag findings with insufficient evidence
- Provide data collection recommendations
- Continue analysis with available data

**Analysis Failures:**
- Fallback to simpler consistency checks
- Report analysis limitations clearly
- Suggest manual review for complex cases

**Resolution Gaps:**
- Identify contradictions requiring additional research
- Provide partial resolution suggestions
- Escalate critical inconsistencies to stakeholders

## Performance Considerations

- Batch processing: Analyze multiple findings together for efficiency
- Incremental analysis: Add new findings without full reanalysis
- Parallel processing: Analyze different contradiction types concurrently
- Memory optimization: Process large datasets in chunks
- Caching: Store intermediate consistency calculations
