# ut-evaluator Skill

## Purpose

The **ut-evaluator** skill implements the 5-check verification process for extracted findings. It validates each finding against the original source material using Hogwild-inspired methodology, ensuring findings are accurate, properly attributed, and free from researcher interpretation.

## Key Responsibilities

1. **5-Check Verification Process**
   - **Check 1**: Verbatim quote exists in transcript
   - **Check 2**: Finding accurately reflects quote meaning
   - **Check 3**: Task attribution is correct
   - **Check 4**: No researcher interpretation presented as participant statement
   - **Check 5**: Severity rating is justified by evidence

2. **Revelation Loop**
   - Failed findings sent back to extractor with correction instructions
   - Maximum 3 iterations per finding
   - Tracks revision history and improvement over iterations

3. **Validation Scoring**
   - Pass/Fail for each check
   - Severity levels: 0 (minor), 1 (moderate), 2 (critical)
   - Overall finding validity assessment

4. **Provenance Verification**
   - Cross-reference quotes against source transcripts
   - Validate timestamps and speaker attribution
   - Ensure task IDs match transcript context

5. **Quality Assurance**
   - Flag findings requiring manual review
   - Generate validation reports
   - Track inter-rater reliability metrics

## Input Format

```json
{
  "command": "evaluate_findings",
  "findings_batch_id": "batch_001",
  "transcript_ids": ["T_P001_session1", "T_P002_session1"],
  "evaluation_batch_id": "eval_001",
  "max_iterations": 3
}
```

## Output Format

```json
{
  "evaluation_batch_id": "eval_001",
  "evaluated_findings": [
    {
      "finding_id": "F_001",
      "original_finding": {...},
      "evaluation_results": [
        {
          "check_type": "verbatim_match",
          "passed": true,
          "feedback": "Quote found exactly at timestamp 07:45"
        },
        {
          "check_type": "meaning_accuracy",
          "passed": true,
          "feedback": "Finding accurately captures participant's confusion"
        },
        {
          "check_type": "task_attribution",
          "passed": true,
          "feedback": "Correctly attributed to TASK-003"
        },
        {
          "check_type": "no_interpretation",
          "passed": true,
          "feedback": "No researcher interpretation detected"
        },
        {
          "check_type": "justified_severity",
          "passed": false,
          "feedback": "Severity rating not supported by evidence",
          "severity": 1
        }
      ],
      "all_passed": false,
      "failed_checks": ["justified_severity"],
      "correction_instructions": "Revise severity rating to match evidence. Current rating suggests critical issue but evidence shows minor inconvenience.",
      "revision_count": 1,
      "evaluated_at": "2026-05-08T14:30:00Z"
    }
  ],
  "evaluation_stats": {
    "total_findings": 15,
    "passed_all_checks": 12,
    "failed_checks": 3,
    "by_failure_reason": {
      "verbatim_match": 0,
      "meaning_accuracy": 1,
      "task_attribution": 0,
      "no_interpretation": 0,
      "justified_severity": 2
    },
    "average_checks_passed": 4.2,
    "needs_revision": 3
  }
}
```

## 5-Check Details

### Check 1: Verbatim Match
**Purpose**: Ensure quote exists exactly in source
**Validation**:
- Exact string match in transcript
- Correct timestamp alignment
- Speaker attribution matches
**Failure Examples**:
- Paraphrased instead of verbatim
- Wrong timestamp
- Quote from different participant

### Check 2: Meaning Accuracy
**Purpose**: Finding reflects actual quote meaning
**Validation**:
- No distortion of participant's intent
- Context preserved accurately
- No cherry-picking of words
**Failure Examples**:
- Taking words out of context
- Misinterpreting sarcasm as literal
- Ignoring qualifying statements

### Check 3: Task Attribution
**Purpose**: Finding correctly linked to task
**Validation**:
- Task ID matches transcript context
- Finding occurred during task execution
- No attribution to wrong task
**Failure Examples**:
- Finding from TASK-001 attributed to TASK-002
- General comment attributed to specific task
- Task ID doesn't exist in config

### Check 4: No Interpretation
**Purpose**: Researcher opinions not presented as participant facts
**Validation**:
- Clear separation between observation and participant statement
- No "participant seemed..." when quoting directly
- Researcher interpretations clearly marked
**Failure Examples**:
- "Participant was confused" instead of direct quote
- Interpreting behavior as fact
- Adding researcher judgment to participant words

### Check 5: Justified Severity
**Purpose**: Severity rating supported by evidence
**Validation**:
- Nielsen scale criteria met
- Evidence supports rating level
- Consistent with impact described
**Failure Examples**:
- Cosmetic issue rated as catastrophic
- No evidence for claimed impact
- Severity doesn't match described problem

## Revelation Loop Process

### Iteration 1
- Run all 5 checks
- Pass: Finding approved
- Fail: Send back with specific correction instructions

### Iteration 2
- Re-run checks on revised finding
- If still failing, provide more detailed guidance
- Track improvement over iterations

### Iteration 3 (Final)
- Final validation
- If still failing, flag for manual review
- Mark as requiring human intervention

## Correction Instructions

### For Verbatim Match Failures
```
"Quote not found in transcript. Please:
1. Use exact text from transcript
2. Verify timestamp is correct
3. Ensure speaker attribution matches"
```

### For Meaning Accuracy Failures
```
"Finding distorts quote meaning. Please:
1. Re-read quote in full context
2. Ensure finding reflects actual participant experience
3. Avoid over-interpretation"
```

### For Task Attribution Failures
```
"Incorrect task attribution. Please:
1. Check transcript context around timestamp
2. Verify which task was being performed
3. Use correct task ID from config"
```

### For Interpretation Issues
```
"Contains researcher interpretation. Please:
1. Use direct participant quotes only
2. Separate observations from participant statements
3. Clearly mark any inferences"
```

### For Severity Rating Issues
```
"Severity not justified by evidence. Please:
1. Review Nielsen severity scale criteria
2. Ensure rating matches actual impact
3. Provide specific evidence for rating"
```

## Integration Points

- **MCP Tools**: `load_findings`, `load_transcript`, `save_evaluation`, `get_pipeline_status`
- **State Management**: Persists evaluation results in `data/evaluations/`
- **ut-extractor**: Receives failed findings for revision
- **ut-severity-rater**: Only processes validated findings
- **Revelation Loop**: Iterative improvement with extractor

## Quality Metrics

- Overall pass rate: % findings passing all checks
- Check-specific failure rates: Which checks fail most often
- Revision success rate: % findings fixed through revelation loop
- Inter-rater reliability: Consistency across evaluators
- Manual review rate: % requiring human intervention

## Example Usage

```python
from ut_analysis.skills.evaluator import EvaluatorSkill

evaluator = EvaluatorSkill()

# Evaluate a batch of findings
result = evaluator.evaluate_findings(
    findings_batch_id="batch_001",
    transcript_ids=["T_P001_s1", "T_P002_s1"],
    evaluation_batch_id="eval_001",
    max_iterations=3
)

# Check results
passed = result["evaluation_stats"]["passed_all_checks"]
needs_revision = result["evaluation_stats"]["needs_revision"]

print(f"Passed: {passed}, Needs revision: {needs_revision}")
```

## Validation Rules

- All 5 checks must pass for finding approval
- Maximum 3 revelation iterations
- Failed findings must include specific correction instructions
- Evaluation results must be traceable to source
- Severity levels must be justified with evidence

## Error Handling

**Missing Sources:**
- Skip evaluation if transcript not found
- Log error but continue with available data

**Malformed Findings:**
- Validate finding structure before evaluation
- Skip invalid findings with error logging

**Revelation Loop Issues:**
- Track iteration count to prevent infinite loops
- Flag findings exceeding max iterations
- Provide escalation path for stuck findings

## Performance Considerations

- Batch evaluation: Process multiple findings together
- Caching: Store transcript content for repeated access
- Parallel processing: Evaluate independent findings concurrently
- Incremental evaluation: Add evaluations without reprocessing
- Source validation: Pre-load and validate all transcripts
