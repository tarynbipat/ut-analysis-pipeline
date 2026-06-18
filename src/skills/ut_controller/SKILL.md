# ut-controller Skill

## Purpose

The **ut-controller** skill orchestrates the entire usability test analysis pipeline, managing state, phase transitions, and overall execution flow. It serves as the coordinator for all downstream skills and ensures proper sequencing of pipeline stages.

## Key Responsibilities

1. **Pipeline Initialization**
   - Load and validate research configuration
   - Initialize project state and directory structure
   - Set up all managers (transcript, notes, findings, etc.)
   - Validate participant metadata and task definitions

2. **Phase Management**
   - Track current pipeline phase (ingestion → extraction → evaluation → synthesis → reporting)
   - Prevent out-of-order execution
   - Report progress and status at each phase
   - Detect and recover from failures

3. **State Coordination**
   - Provide unified interface for phase transitions
   - Maintain complete audit trail of pipeline execution
   - Enable resumption from any phase
   - Track completion metrics (items processed, success rates)

4. **Quality Gates**
   - Validate that prerequisites are met before each phase
   - Ensure minimum participant/finding counts before synthesis
   - Require successful evaluations before severity rating
   - Flag incomplete pipelines before reporting

5. **Error Handling**
   - Log all errors with context and recommendations
   - Allow retry with modified parameters
   - Collect error summary for reporting
   - Generate recovery instructions

## Configuration

The controller expects a `research_config.yaml`:

```yaml
project_id: ut-2026-01
project_name: "Website Redesign Study"
participants:
  - id: P001
    name: "User A"
    demographics: {age: 35, tech_proficiency: high}
  - id: P002
    name: "User B"
    demographics: {age: 42, tech_proficiency: medium}

tasks:
  - id: TASK-001
    name: "Complete checkout"
    success_criteria: "Payment processed successfully"
    time_limit_seconds: 300
    expected_steps: 7
  - id: TASK-002
    name: "Find product"
    success_criteria: "Product located in search results"
    time_limit_seconds: 120

heuristic_framework: "nielsen_10"
research_date: 2026-05-01
```

## Input Format

```json
{
  "command": "init_pipeline",
  "config_file": "/path/to/research_config.yaml",
  "project_dir": "/path/to/project"
}
```

## Output Format

```json
{
  "status": "success",
  "phase": "initialized",
  "project_id": "ut-2026-01",
  "participants_count": 2,
  "tasks_count": 2,
  "next_steps": ["Load transcripts", "Run extraction"]
}
```

## Phase Flow

```
INITIALIZED 
  ↓
INGESTION_COMPLETE (transcripts + notes loaded)
  ↓
EXTRACTION_COMPLETE (findings extracted)
  ↓
EVALUATION_COMPLETE (findings verified)
  ↓
SEVERITY_RATING_COMPLETE (rated with Nielsen scale)
  ↓
HEURISTIC_MAPPING_COMPLETE (mapped to heuristics)
  ↓
SYNTHESIS_COMPLETE (cross-participant synthesis done)
  ↓
REPORTING_COMPLETE (reports generated)
```

## Integration Points

- **MCP Tools**: `init_project`, `update_phase`, `get_pipeline_status`
- **Downstream Skills**: All other skills receive phase status and project config from controller
- **State Management**: Maintains central state.json with execution history
- **Error Recovery**: Can retry individual phases with modified parameters

## Example Usage

```python
from ut_analysis.skills.controller import ControllerSkill

controller = ControllerSkill()

# Initialize pipeline
result = controller.init_pipeline(
    config_file="research_config.yaml",
    project_dir="/projects/ut-2026-01"
)

# Check status
status = controller.get_status()

# Transition to next phase
controller.advance_phase("extraction")
```

## Validation Rules

- All participants must have unique IDs
- All tasks must have success criteria and time limits
- Heuristic framework must be defined or default to "nielsen_10"
- At least 1 transcript required before extraction
- At least 1 finding required before evaluation
- At least N-1 participants' data required before synthesis (N = total participants)

## Failure Recovery

If pipeline fails at a phase:
1. Log error with full context
2. Keep state up to date
3. Suggest correction (e.g., "Re-run extraction after fixing malformed transcript")
4. Enable retry without reprocessing previous phases
