# ut-critic Skill — Evidence Challenge Agent

## Purpose

The **ut-critic** skill is an evidence challenge agent that reviews draft findings, synthesis insights, themes, and recommendations to assess whether the supporting evidence is strong enough to justify the claims made.

This agent sits between synthesis and reporting in the pipeline, enforcing research rigor by identifying:
- Claims based on too few participants
- Themes that conflate separate issues
- Vague assertions lacking supporting quotes
- Recommendations that do not logically follow from findings
- Missing contradictions or outlier perspectives
- Findings that should be downgraded from "pattern" to "individual insight"

## Position in Pipeline

```
Synthesizer → Critic → Revision / Human Review → Reporter
```

## Key Responsibilities

1. **Evidence Strength Assessment**
   - Evaluate participant count vs. claim scope
   - Verify verbatim quotes support the finding
   - Check provenance chain completeness
   - Assess whether severity ratings are justified

2. **Overgeneralization Detection**
   - Flag claims that imply universality from limited data
   - Identify themes conflating distinct issues
   - Detect unsupported causal claims

3. **Gap Identification**
   - Missing participant perspectives
   - Unexamined edge cases
   - Absent contradictory evidence acknowledgment

4. **Revision Guidance**
   - Provide specific revision instructions
   - Suggest downgrade/upgrade of confidence
   - Recommend human review when automated assessment is insufficient

## Input Format

```json
{
  "command": "critique_synthesis",
  "synthesis_batch_id": "synthesis_001",
  "critic_batch_id": "critic_001",
  "critic_config": {
    "min_participants_for_pattern": 3,
    "require_verbatim_quotes": true,
    "severity_justification_required": true,
    "flag_single_participant_themes": true,
    "confidence_threshold": 0.7
  }
}
```

## Output Format

```json
{
  "critic_batch_id": "critic_001",
  "source_synthesis_id": "synthesis_001",
  "critiques": [
    {
      "critique_id": "CRIT_001",
      "target_type": "insight",
      "target_id": "I_001",
      "critique_summary": "Claim of 'widespread checkout confusion' based on only 2 participants",
      "evidence_strength": "weak",
      "issues_found": ["insufficient_participant_count", "missing_task_context"],
      "unsupported_claims": ["'widespread' implies majority but only 2/5 participants affected"],
      "overgeneralizations": ["Pattern claimed from 2 participants"],
      "missing_participant_segments": ["P003", "P004", "P005"],
      "recommended_revision": "Downgrade from pattern to 'observed in subset' and add qualifier",
      "confidence_rating": 0.4,
      "requires_human_review": true,
      "review_reason": "Low evidence for high-severity claim"
    }
  ],
  "overall_evidence_quality": "concerning",
  "human_review_required": true,
  "summary": {
    "total_critiqued": 8,
    "strong_evidence": 3,
    "moderate_evidence": 2,
    "weak_evidence": 2,
    "insufficient_evidence": 1
  }
}
```

## Evidence Strength Criteria

| Rating | Definition |
|--------|-----------|
| **strong** | 3+ participants, verbatim quotes, clear provenance, consistent across tasks |
| **moderate** | 2+ participants, quotes present, minor gaps in provenance |
| **weak** | 1-2 participants, partial quotes, some provenance gaps |
| **insufficient** | Single data point, no verbatim support, no provenance |

## Critique Triggers

The critic flags items when:
- Participant count < `min_participants_for_pattern` but claim implies pattern
- No verbatim quotes support the finding
- Severity ≥ 3 but evidence comes from < 2 participants
- Recommendation lacks logical connection to underlying findings
- Theme title uses absolute language ("all users", "always", "never")
- Contradictory evidence exists but is not acknowledged
- Confidence score conflicts with evidence strength

## Human Review Triggers

Generates `HumanReviewCheckpoint` when:
- Evidence strength is "weak" or "insufficient" for severity ≥ 2
- Confidence rating < configured threshold
- Contradictions are unacknowledged in the synthesis
- Source provenance is incomplete (missing transcript/session ID)
- Single participant drives a high-priority recommendation

## Integration Points

- **MCP Tools**: `load_synthesis`, `save_critique`, `create_review_checkpoint`
- **State Management**: Persists critiques in `data/critiques/`
- **ut-synthesizer**: Reads synthesis output as input
- **ut-reporter**: Reporter should include critic findings in provenance
- **Human Review**: Generates review checkpoints for flagged items

## Example Usage

```python
from ut_analysis.skills.ut_critic.critic import CriticSkill

critic = CriticSkill(state_manager)
result = critic.critique_synthesis(
    synthesis_batch_id="synthesis_001",
    critic_batch_id="critic_001",
)

if result["human_review_required"]:
    print("Human review needed before reporting")
    for critique in result["critiques"]:
        if critique["requires_human_review"]:
            print(f"  - {critique['critique_summary']}")
```
