# ut-theme-orchestrator Skill

## Purpose

The **ut-theme-orchestrator** skill coordinates thematic analysis across multiple specialist agents. It takes an extracted findings batch, routes each finding into one or more parallel thematic lanes, and produces a structured handoff artifact for downstream analysts.

## Thematic Lanes

- **pain_points**
- **user_needs**
- **behavioral_patterns**
- **mental_models**
- **trust_confidence**
- **workflow_breakdowns**
- **product_opportunities** (reserved for downstream extension when configured)

## What It Produces

For each populated lane, the orchestrator creates a handoff artifact containing:

- finding IDs
- participant IDs
- task IDs
- assignment rationale
- assigned specialist agent

This makes it possible to fan findings out in parallel while preserving provenance back to the extraction batch.

## Lane Routing Responsibilities

1. Read extracted findings from persisted findings storage
2. Analyze titles, descriptions, and categories for thematic signals
3. Route findings into one or more thematic lanes
4. Preserve provenance for every routed item
5. Save a reusable orchestration plan for downstream specialists

## Analyst Assignments

| Lane | Assigned Agent |
|------|----------------|
| pain_points | `ut-pain-point-analyst` |
| user_needs | `ut-needs-analyst` |
| behavioral_patterns | `ut-behavior-analyst` |
| mental_models | `ut-mental-model-analyst` |
| trust_confidence | `ut-trust-analyst` |
| workflow_breakdowns | `ut-workflow-analyst` |

## Input Format

```json
{
  "command": "create_orchestration_plan",
  "findings_batch_id": "batch_001",
  "run_id": "run_001",
  "project_id": "proj_001"
}
```

## Output Format

```json
{
  "plan_id": "run_001_theme_orchestration",
  "findings_batch_id": "batch_001",
  "run_id": "run_001",
  "project_id": "proj_001",
  "thematic_lanes": [
    {
      "lane_id": "pain_points",
      "assigned_agent": "ut-pain-point-analyst",
      "finding_ids": ["F_001", "F_004"],
      "participant_ids": ["P001", "P003"],
      "task_ids": ["TASK-001"],
      "rationale": "Contains frustration and difficulty signals across the routed findings.",
      "handoff_items": [
        {
          "finding_id": "F_001",
          "participant_id": "P001",
          "task_id": "TASK-001",
          "rationale": "Matched pain point keywords: frustrating, difficult"
        }
      ]
    }
  ],
  "total_findings": 8,
  "created_at": "2026-06-26T12:00:00Z"
}
```

## Routing Logic

The skill uses lightweight keyword matching against finding titles and descriptions. A finding may appear in multiple lanes when it expresses multiple themes.

## Integration Points

- **State Management**: Reads from `FindingsManager`
- **Persistence**: Saves plans via `ThemeOrchestrationManager`
- **Downstream Skills**: Produces specialist-ready handoff artifacts for parallel theme analysis
