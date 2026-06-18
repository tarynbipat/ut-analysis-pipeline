# ut-heuristic-mapper Skill

## Purpose

The **ut-heuristic-mapper** skill maps validated and severity-rated findings to Nielsen's 10 usability heuristics. It categorizes each finding according to the violated heuristic principle, enabling systematic analysis of usability issues and prioritization of design improvements.

## Key Responsibilities

1. **Heuristic Mapping**
   - **H1**: Visibility of system status
   - **H2**: Match between system and real world
   - **H3**: User control and freedom
   - **H4**: Consistency and standards
   - **H5**: Error prevention
   - **H6**: Recognition rather than recall
   - **H7**: Flexibility and efficiency of use
   - **H8**: Aesthetic and minimalist design
   - **H9**: Help users recognize, diagnose, and recover from errors
   - **H10**: Help and documentation

2. **Mapping Confidence Scoring**
   - Primary heuristic: Main principle violated
   - Secondary heuristics: Related principles affected
   - Confidence level: Certainty of mapping (0.0-1.0)
   - Rationale: Explanation of mapping decision

3. **Heuristic Violation Analysis**
   - Frequency of violations per heuristic
   - Severity distribution across heuristics
   - Most problematic heuristics identification
   - Cross-heuristic patterns

4. **Design Recommendation Generation**
   - Specific improvement suggestions per heuristic
   - Priority based on severity and frequency
   - Implementation feasibility assessment

5. **Heuristic Coverage Analysis**
   - Identification of untested heuristics
   - Gaps in usability evaluation coverage
   - Recommendations for additional testing

## Input Format

```json
{
  "command": "map_heuristics",
  "severity_batch_id": "severity_001",
  "heuristic_batch_id": "heuristic_001",
  "mapping_config": {
    "min_confidence_threshold": 0.7,
    "allow_multiple_mappings": true,
    "max_secondary_heuristics": 2
  }
}
```

## Output Format

```json
{
  "heuristic_batch_id": "heuristic_001",
  "mapped_findings": [
    {
      "finding_id": "F_001",
      "original_finding": {...},
      "heuristic_mapping": {
        "primary_heuristic": {
          "id": "H4",
          "name": "Consistency and standards",
          "confidence": 0.95,
          "rationale": "Inconsistent discount code field placement violates platform conventions"
        },
        "secondary_heuristics": [
          {
            "id": "H1",
            "name": "Visibility of system status",
            "confidence": 0.75,
            "rationale": "Lack of feedback about discount code validation status"
          }
        ],
        "design_recommendations": [
          "Place discount code field in consistent location across checkout flow",
          "Add real-time validation feedback for discount codes"
        ],
        "mapped_at": "2026-05-08T14:30:00Z"
      }
    }
  ],
  "heuristic_analysis": {
    "violation_frequency": {
      "H1": 3, "H2": 1, "H3": 2, "H4": 5, "H5": 1,
      "H6": 2, "H7": 1, "H8": 0, "H9": 3, "H10": 0
    },
    "severity_by_heuristic": {
      "H4": {"avg_severity": 2.8, "max_severity": 3, "critical_count": 2},
      "H1": {"avg_severity": 2.2, "max_severity": 3, "critical_count": 1}
    },
    "most_problematic_heuristics": ["H4", "H1", "H9"],
    "untested_heuristics": ["H8", "H10"],
    "coverage_gaps": [
      "No testing of aesthetic design elements",
      "Help system not evaluated"
    ]
  }
}
```

## Nielsen's 10 Usability Heuristics

### H1: Visibility of System Status
**Definition**: The system should always keep users informed about what is going on
**Indicators**:
- Loading states not shown
- No progress indicators
- Silent failures
- Unclear current state

### H2: Match Between System and Real World
**Definition**: The system should speak the users' language and follow real-world conventions
**Indicators**:
- Technical jargon
- Counter-intuitive workflows
- Non-standard terminology
- Confusing metaphors

### H3: User Control and Freedom
**Definition**: Users often choose system functions by mistake and need clearly marked emergency exits
**Indicators**:
- No undo functionality
- Difficult to cancel actions
- Forced workflows
- No escape routes

### H4: Consistency and Standards
**Definition**: Users should not have to wonder whether different words, situations, or actions mean the same thing
**Indicators**:
- Inconsistent terminology
- Different behaviors for same actions
- Platform convention violations
- Inconsistent visual design

### H5: Error Prevention
**Definition**: Even better than good error messages is a careful design which prevents problems from occurring
**Indicators**:
- No input validation
- Dangerous actions not protected
- Easy to make mistakes
- No confirmation for critical actions

### H6: Recognition Rather Than Recall
**Definition**: Minimize the user's memory load by making objects, actions, and options visible
**Indicators**:
- Hidden functionality
- Required information not visible
- Memory-dependent navigation
- No visible cues

### H7: Flexibility and Efficiency of Use
**Definition**: Accelerators may often speed up the interaction for the expert user
**Indicators**:
- No shortcuts for experts
- Rigid workflows
- No customization options
- Inefficient for power users

### H8: Aesthetic and Minimalist Design
**Definition**: Dialogues should not contain information which is irrelevant or rarely needed
**Indicators**:
- Cluttered interfaces
- Irrelevant information displayed
- Poor visual hierarchy
- Overwhelming amount of content

### H9: Help Users Recognize, Diagnose, and Recover from Errors
**Definition**: Error messages should be expressed in plain language, precisely indicate the problem, and constructively suggest a solution
**Indicators**:
- Technical error messages
- No clear recovery path
- Blaming error messages
- Unhelpful error information

### H10: Help and Documentation
**Definition**: It is better if the system can be used without documentation, but it may be necessary to provide help and documentation
**Indicators**:
- No help available
- Hard to find help
- Inadequate documentation
- No context-sensitive help

## Mapping Process

### Step 1: Finding Analysis
- Review finding description and quote
- Identify core problem or issue
- Consider user impact and context

### Step 2: Heuristic Matching
- Compare finding against each heuristic definition
- Identify primary violated heuristic
- Find secondary related heuristics
- Calculate mapping confidence

### Step 3: Rationale Development
- Explain why this heuristic applies
- Provide specific evidence from finding
- Consider alternative interpretations

### Step 4: Recommendation Generation
- Suggest specific design improvements
- Link to violated heuristic principles
- Consider implementation feasibility

## Integration Points

- **MCP Tools**: `load_severity_ratings`, `save_heuristic_mappings`, `get_pipeline_status`
- **State Management**: Persists heuristic mappings in `data/heuristics/`
- **ut-severity-rater**: Uses severity for prioritization
- **ut-synthesizer**: Groups findings by heuristic for analysis
- **Design Recommendations**: Feeds into final report generation

## Quality Metrics

- Mapping confidence distribution: Average confidence scores
- Heuristic coverage: % of heuristics tested
- Mapping consistency: Agreement across similar findings
- Recommendation quality: Actionability of suggestions
- Gap identification: Untested usability areas

## Example Usage

```python
from ut_analysis.skills.heuristic_mapper import HeuristicMapperSkill

mapper = HeuristicMapperSkill()

# Map findings to heuristics
result = mapper.map_heuristics(
    severity_batch_id="severity_001",
    heuristic_batch_id="heuristic_001",
    mapping_config={
        "min_confidence_threshold": 0.7,
        "allow_multiple_mappings": True,
        "max_secondary_heuristics": 2
    }
)

# Check most problematic heuristics
problematic = result["heuristic_analysis"]["most_problematic_heuristics"]
print(f"Most problematic heuristics: {problematic}")
```

## Validation Rules

- Primary heuristic must be assigned to each finding
- Confidence scores must be 0.0-1.0
- Heuristic IDs must be valid (H1-H10)
- Rationale must be provided for each mapping
- Design recommendations must be actionable

## Error Handling

**Unmappable Findings:**
- Assign to "Other" category with explanation
- Flag for manual review
- Document mapping challenges

**Low Confidence Mappings:**
- Include in results but mark uncertain
- Provide alternative possible mappings
- Recommend additional context

**Multiple Possible Heuristics:**
- Choose most specific primary heuristic
- Include related heuristics as secondary
- Explain mapping decision rationale

## Performance Considerations

- Batch mapping: Process multiple findings together
- Caching: Store severity data for repeated access
- Parallel processing: Map independent findings concurrently
- Incremental mapping: Add mappings without reprocessing
- Heuristic validation: Pre-validate heuristic definitions
