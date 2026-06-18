# ut-extractor Skill

## Purpose

The **ut-extractor** skill analyzes transcripts and observation notes to extract structured usability findings. It identifies and categorizes usability issues, task outcomes, pain points, positive moments, and participant quotes with full provenance tracking.

## Key Responsibilities

1. **Finding Categorization**
   - **Usability Issues**: Problems that hinder task completion or user experience
   - **Task Outcomes**: Success/failure/partial completion of specific tasks
   - **Pain Points**: Frustrations, confusions, or difficulties expressed by participants
   - **Positive Moments**: Successful interactions, satisfactions, or ease of use
   - **Participant Quotes**: Notable statements worth highlighting

2. **Provenance Tracking**
   - Every finding MUST include verbatim quote from transcript/notes
   - Speaker identification (Participant vs Researcher)
   - Exact timestamp from source
   - Task ID attribution (when applicable)
   - Participant ID for cross-participant analysis

3. **Confidence Scoring**
   - High confidence (0.9-1.0): Clear, explicit statements
   - Medium confidence (0.7-0.8): Implied through behavior/context
   - Low confidence (0.5-0.6): Inferred from multiple cues

4. **Task Completion Status**
   - Flag task completion per participant: completed, failed, needed_help, skipped
   - Track time to completion vs time limits
   - Identify help requests and assistance provided

5. **Context Preservation**
   - Include surrounding context (2-3 turns before/after)
   - Preserve original formatting and emphasis
   - Link related findings across participants

## Input Format

```json
{
  "command": "extract_findings",
  "transcript_ids": ["T_P001_session1", "T_P002_session1"],
  "note_session_ids": ["S_P001_obs", "S_P002_obs"],
  "project_config": {
    "tasks": [...],
    "participants": [...]
  },
  "extraction_batch_id": "batch_001"
}
```

## Output Format

```json
{
  "extraction_batch_id": "batch_001",
  "findings": [
    {
      "finding_id": "F_001",
      "category": "usability_issue",
      "title": "Discount code visibility issue",
      "description": "Participant struggled to find discount code input field",
      "verbatim_quote": "Hmm, I'm not seeing a discount code field anywhere. Let me look around...",
      "speaker": "Participant",
      "timestamp": "07:45",
      "source_transcript_id": "T_P001_session1",
      "task_id": "TASK-003",
      "participant_id": "P001",
      "confidence": 0.95,
      "context": {
        "before": ["Researcher: 'Apply discount code SAVE10 during checkout'"],
        "after": ["Participant: 'Oh wait, I see a small link at the bottom'"]
      },
      "task_completion_status": {
        "task_id": "TASK-003",
        "outcome": "needed_help",
        "time_to_completion": 45,
        "help_requested": true
      }
    }
  ],
  "task_completion_matrix": {
    "TASK-001": {
      "P001": {"outcome": "completed", "time_seconds": 120},
      "P002": {"outcome": "completed", "time_seconds": 95}
    }
  },
  "extraction_stats": {
    "total_findings": 15,
    "by_category": {"usability_issue": 8, "pain_point": 4, "positive_moment": 3},
    "average_confidence": 0.87,
    "task_completion_rate": 0.92
  }
}
```

## Categorization Rules

### Usability Issues
- Explicit problems: "I can't find...", "This doesn't work...", "I'm stuck..."
- Behavioral indicators: Long pauses, repeated clicks, scrolling frantically
- Researcher interventions: "Let me help you with that..."
- Error messages or system failures

### Task Outcomes
- Success: "Great! I got the order confirmation"
- Failure: "I couldn't complete the checkout"
- Partial: "I got most of it done, but..."
- Help needed: "Can you show me how to..."

### Pain Points
- Frustration: "This is annoying", "Why is it so hard?"
- Confusion: "I'm not sure what to do", "What does this mean?"
- Dissatisfaction: "I expected it to be easier"

### Positive Moments
- Satisfaction: "That was easy!", "I like how..."
- Success celebrations: "Perfect!", "Great!"
- Positive comparisons: "Better than the old version"

### Participant Quotes
- Insightful comments: "I would never use this in real life"
- Feature requests: "It would be nice if..."
- General feedback: "Overall, the experience was..."

## Confidence Scoring Guidelines

### High Confidence (0.9-1.0)
- Direct, explicit statements
- Clear behavioral evidence
- Multiple corroborating sources
- Researcher confirmation

### Medium Confidence (0.7-0.8)
- Implied through context
- Behavioral patterns
- Consistent across similar situations
- Supported by observation notes

### Low Confidence (0.5-0.6)
- Inferred from single cues
- Ambiguous statements
- Contradictory evidence
- Requires interpretation

## Task Completion Detection

### Completed
- Explicit success statements
- Researcher confirmation
- Order/transaction completion
- Within time limits

### Failed
- Explicit failure statements
- Abandoned attempts
- Time limit exceeded
- Multiple help requests

### Needed Help
- Researcher assistance requested
- Guided through process
- Partial completion with help

### Skipped
- Explicitly skipped by participant
- Not attempted due to time constraints
- Researcher-directed skipping

## Integration Points

- **MCP Tools**: `load_transcript`, `load_notes`, `save_findings`, `get_pipeline_status`
- **State Management**: Persists findings in `data/findings/` with batch IDs
- **ut-controller**: Receives project config and task definitions
- **ut-evaluator**: Downstream skill validates extracted findings
- **Provenance**: Every finding links back to exact source location

## Quality Metrics

- Findings per transcript: Average extraction rate
- Category distribution: Balance across finding types
- Confidence distribution: % high/medium/low confidence
- Task attribution coverage: % findings linked to tasks
- Quote verification: % verbatim matches (validated by evaluator)

## Example Usage

```python
from ut_analysis.skills.extractor import ExtractorSkill

extractor = ExtractorSkill()

# Extract from all loaded transcripts
result = extractor.extract_findings(
    transcript_ids=["T_P001_s1", "T_P002_s1"],
    note_session_ids=["S_P001_obs"],
    project_config=config,
    batch_id="batch_001"
)

# Results include structured findings + task completion matrix
print(f"Extracted {len(result['findings'])} findings")
print(f"Task completion rate: {result['extraction_stats']['task_completion_rate']}")
```

## Validation Rules

- Every finding must have verbatim_quote, speaker, timestamp, source_transcript_id
- Confidence must be 0.0-1.0
- Task IDs must reference valid tasks from config
- Timestamps must exist in source transcript
- Categories must be from predefined enum
- Task completion outcomes must be valid

## Error Handling

**Missing Sources:**
- Skip extraction if transcript/note not found
- Log warning but continue with available data

**Malformed Data:**
- Validate transcript structure before extraction
- Skip invalid turns but process valid ones

**Low Confidence Findings:**
- Flag for manual review
- Include in extraction but mark for evaluation

## Performance Considerations

- Batch processing: Extract from multiple transcripts in single operation
- Incremental extraction: Add findings without reprocessing existing ones
- Caching: Store intermediate results for large datasets
- Parallel processing: Extract from multiple participants concurrently
