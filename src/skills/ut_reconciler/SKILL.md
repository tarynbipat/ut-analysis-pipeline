# ut-reconciler Skill — Contradiction Reconciliation Agent

## Purpose

The **ut-reconciler** skill takes identified contradictions and themes and produces nuanced, context-aware reconciliations rather than averaging conflicting data into bland summaries.

Instead of discarding contradictions or choosing one side, the reconciler:
- Explains *why* participants disagreed
- Identifies contextual factors (experience level, task familiarity, system trust)
- Produces design implications that honor the tension
- Surfaces research gaps and follow-up questions

## Position in Pipeline

```
Contradiction Detector → Reconciler → Critic → Reporter
```

## Key Responsibilities

1. **Tension Analysis**
   - Identify what is genuinely in conflict
   - Distinguish real contradictions from complementary perspectives
   - Map participant groups to each position

2. **Context Attribution**
   - Link disagreements to participant characteristics
   - Identify task context that explains differences
   - Consider temporal factors (early vs late in session)

3. **Nuanced Interpretation**
   - Produce qualified findings that preserve both sides
   - Generate conditional design implications
   - Avoid false consensus

4. **Research Gap Identification**
   - Flag where more data is needed
   - Suggest follow-up research questions
   - Identify which participant segments are underrepresented

## Input Format

```json
{
  "command": "reconcile_contradictions",
  "contradictions_batch_id": "contra_001",
  "synthesis_batch_id": "synthesis_001",
  "reconciliation_batch_id": "recon_001",
  "reconciliation_config": {
    "include_participant_metadata": true,
    "generate_research_questions": true,
    "min_confidence_threshold": 0.5
  }
}
```

## Output Format

```json
{
  "reconciliation_batch_id": "recon_001",
  "reconciliations": [
    {
      "reconciliation_id": "RECON_001",
      "contradiction_id": "CONTRA_001",
      "theme_ids": ["T_checkout", "T_trust"],
      "tension_description": "Some participants valued auto-deploy speed while others distrusted it",
      "participant_groups": {
        "pro_automation": ["P001", "P003"],
        "prefer_control": ["P002", "P005"]
      },
      "possible_explanations": [
        "Deployment experience correlates with automation trust",
        "Participants who saw rollback options were more comfortable",
        "Prior negative deployment experiences reduce automation trust"
      ],
      "design_implication": "Provide progressive automation with visible manual override and rollback confidence indicators",
      "changes_original_finding": true,
      "further_research_needed": true,
      "research_questions": [
        "Does showing deployment history increase willingness to auto-deploy?",
        "What rollback visibility threshold enables trust?"
      ],
      "confidence": 0.75
    }
  ],
  "unresolved_tensions": ["CONTRA_003"],
  "research_gaps": [
    "Insufficient data on novice users' automation preferences",
    "No longitudinal data on trust development"
  ]
}
```

## Reconciliation Strategy

The reconciler avoids "averaging" by following this logic:

1. **Accept the tension** — Both sides are real user experiences
2. **Explain the divergence** — What factors predict which group a user falls into?
3. **Design for both** — Produce recommendations that serve both groups
4. **Flag uncertainty** — Be explicit about what we don't know

## Example Reconciliation

**Contradiction**: P001 loves auto-deploy; P002 distrusts it.

**BAD (averaging)**: "Users have mixed feelings about auto-deploy."

**GOOD (reconciliation)**:
- **Theme**: Auto-deploy reduces effort for users who trust their deployment config
- **Contradiction**: Some users prefer manual control when they lack confidence in environment state
- **Reconciliation**: Trust appears linked to deployment experience, environment visibility, and rollback confidence
- **Design implication**: Surface environment health indicators and make rollback a one-click action
- **Research gap**: Does progressive disclosure of automation build trust over time?

## Integration Points

- **MCP Tools**: `load_contradictions`, `load_synthesis`, `save_reconciliation`
- **State Management**: Persists in `data/reconciliations/`
- **ut-contradiction**: Reads contradiction output
- **ut-synthesizer**: May reference themes from synthesis
- **ut-critic**: Critic reviews reconciliation quality
- **ut-reporter**: Reconciliations feed into final reports

## Human Review Triggers

Generates review checkpoints when:
- Contradiction severity is high but confidence is low
- No plausible explanation can be generated
- Participant groups are too small for reliable segmentation
- Reconciliation changes a previously-approved finding
