# ut-severity-rater Skill

## Purpose

The **ut-severity-rater** skill applies Nielsen's severity rating scale to validated findings. It assesses the impact of each usability issue on task completion and user experience, assigning severity levels from 0 (cosmetic) to 4 (catastrophic) based on systematic criteria.

## Key Responsibilities

1. **Nielsen Severity Scale Application**
   - **0 (Cosmetic)**: Minor visual or wording issues
   - **1 (Minor)**: Small inconvenience, workaround exists
   - **2 (Major)**: Significant problem, task completion difficult
   - **3 (Critical)**: Task completion impossible without help
   - **4 (Catastrophic)**: System unusable, complete failure

2. **Impact Assessment**
   - Frequency: How often does this issue occur?
   - Impact: What is the effect on task completion?
   - Persistence: Does the issue recur for the same user?
   - Scope: How many users are affected?

3. **Evidence-Based Rating**
   - Direct evidence from participant behavior
   - Task completion metrics
   - Participant verbal feedback
   - Researcher observations

4. **Severity Justification**
   - Clear rationale for each rating
   - Supporting evidence from transcripts
   - Consistency with Nielsen criteria
   - Peer review validation

5. **Rating Quality Control**
   - Inter-rater reliability tracking
   - Rating distribution analysis
   - Outlier detection and review

## Input Format

```json
{
  "command": "rate_severity",
  "evaluated_findings_batch_id": "eval_001",
  "severity_batch_id": "severity_001",
  "rating_criteria": {
    "frequency_weight": 0.3,
    "impact_weight": 0.4,
    "persistence_weight": 0.2,
    "scope_weight": 0.1
  }
}
```

## Output Format

```json
{
  "severity_batch_id": "severity_001",
  "rated_findings": [
    {
      "finding_id": "F_001",
      "original_finding": {...},
      "severity_rating": {
        "level": 3,
        "label": "Critical",
        "rationale": "Participant completely unable to complete checkout task due to missing discount code field",
        "criteria_match": {
          "frequency": "High - occurred for all participants",
          "impact": "Critical - prevents task completion",
          "persistence": "High - issue persists throughout session",
          "scope": "All participants affected"
        },
        "evidence": [
          "Participant: 'I can't find the discount code field anywhere'",
          "Researcher intervention required",
          "Task abandoned after 5 minutes"
        ],
        "confidence": 0.95,
        "rated_at": "2026-05-08T14:30:00Z"
      }
    }
  ],
  "severity_stats": {
    "total_rated": 15,
    "severity_distribution": {
      "0_cosmetic": 2,
      "1_minor": 4,
      "2_major": 5,
      "3_critical": 3,
      "4_catastrophic": 1
    },
    "average_severity": 2.1,
    "high_priority_findings": 4,
    "inter_rater_agreement": 0.87
  }
}
```

## Nielsen Severity Scale Details

### Level 0: Cosmetic
**Criteria**: Does not affect functionality
**Examples**:
- Typos in labels
- Inconsistent colors
- Minor spacing issues
- Non-standard but clear icons

**Evidence Required**:
- No impact on task completion
- Participant mentions but continues
- Purely aesthetic feedback

### Level 1: Minor
**Criteria**: Small inconvenience, easy workaround
**Examples**:
- Unclear label but discoverable
- Extra click required
- Non-intuitive but learnable
- Slow response but functional

**Evidence Required**:
- Task completed with minor delay
- Participant finds workaround
- Brief frustration expressed
- No help requested

### Level 2: Major
**Criteria**: Significant problem, task difficult
**Examples**:
- Confusing navigation
- Missing important information
- Error-prone interactions
- Multiple steps where one expected

**Evidence Required**:
- Task completion significantly delayed
- Participant expresses confusion
- Multiple attempts required
- Some participants need help

### Level 3: Critical
**Criteria**: Task completion impossible without help
**Examples**:
- Broken functionality
- Missing required fields
- System errors blocking progress
- Incomprehensible instructions

**Evidence Required**:
- Task cannot be completed
- Researcher intervention required
- Participant abandons task
- Strong negative feedback

### Level 4: Catastrophic
**Criteria**: System completely unusable
**Examples**:
- System crashes
- Complete data loss
- Security issues
- Fundamental functionality broken

**Evidence Required**:
- System failure affects all users
- Complete inability to proceed
- Safety or security implications
- Business-critical impact

## Rating Process

### Step 1: Evidence Gathering
- Review finding description and quote
- Examine task completion data
- Check participant behavior patterns
- Review researcher observations

### Step 2: Criteria Assessment
- Frequency: Single occurrence vs. systematic
- Impact: Cosmetic vs. blocking
- Persistence: One-time vs. recurring
- Scope: Individual vs. all participants

### Step 3: Level Assignment
- Match against Nielsen scale definitions
- Consider weighted combination of criteria
- Apply business context if provided

### Step 4: Justification Documentation
- Clear rationale for rating
- Specific evidence cited
- Alternative interpretations considered

## Integration Points

- **MCP Tools**: `load_evaluations`, `save_severity_ratings`, `get_pipeline_status`
- **State Management**: Persists severity ratings in `data/severity/`
- **ut-evaluator**: Only processes validated findings
- **ut-heuristic-mapper**: Uses severity for prioritization
- **Quality Control**: Tracks rating consistency and accuracy

## Quality Metrics

- Severity distribution: Balance across levels
- Inter-rater agreement: Consistency between raters
- Evidence completeness: % ratings with full justification
- Rating stability: Consistency over time
- Business alignment: Correlation with business impact

## Example Usage

```python
from ut_analysis.skills.severity_rater import SeverityRaterSkill

rater = SeverityRaterSkill()

# Rate severity for evaluated findings
result = rater.rate_severity(
    evaluated_findings_batch_id="eval_001",
    severity_batch_id="severity_001",
    rating_criteria={
        "frequency_weight": 0.3,
        "impact_weight": 0.4,
        "persistence_weight": 0.2,
        "scope_weight": 0.1
    }
)

# Check severity distribution
distribution = result["severity_stats"]["severity_distribution"]
critical_count = distribution.get("3_critical", 0)

print(f"Critical findings: {critical_count}")
```

## Validation Rules

- Severity levels must be 0-4
- Rationale must be provided for each rating
- Evidence must support the assigned level
- Criteria weights must sum to 1.0
- Ratings must be traceable to source findings

## Error Handling

**Missing Evidence:**
- Assign lowest severity if insufficient data
- Flag for manual review
- Log evidence gaps

**Ambiguous Findings:**
- Use conservative rating (lower severity)
- Provide multiple possible interpretations
- Recommend additional data collection

**Conflicting Evidence:**
- Document conflicting signals
- Choose most conservative interpretation
- Flag for expert review

## Performance Considerations

- Batch rating: Process multiple findings together
- Caching: Store evaluation data for repeated access
- Parallel processing: Rate independent findings concurrently
- Incremental rating: Add ratings without reprocessing
- Criteria validation: Pre-validate rating criteria configuration
