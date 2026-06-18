"""Getting Started Guide for UT Analysis Pipeline."""

# Getting Started with UT Analysis Pipeline

## Installation

### Prerequisites
- Python 3.11 or higher
- `uv` package manager (https://docs.astral.sh/uv/getting-started/installation/)

### Setup

```bash
# Clone or navigate to the project
cd ut-analysis-pipeline

# Install dependencies using uv
uv sync
```

## Quick Start

### 1. Initialize Your Project

Create a `research_config.yaml` with your study details:

```yaml
project_id: ut-2026-my-study
project_name: "My Usability Study"
description: "Testing new features"

participants:
  - id: P001
    name: "User A"
    demographics:
      age: 35
      tech_proficiency: high

tasks:
  - id: TASK-001
    name: "Complete task"
    success_criteria: "Task completed successfully"
    time_limit_seconds: 300
```

Then initialize:

```bash
uv run ut-analysis init-project \
  --config research_config.yaml \
  --project-dir ./project_data
```

### 2. Ingest Transcripts and Notes

Load a transcript file (supports `.docx` or `.md`):

```bash
uv run ut-analysis ingest-transcript \
  --file participant_001_transcript.md \
  --transcript-id T_P001_session1 \
  --participant-id P001 \
  --project-dir ./project_data
```

Load observation notes:

```bash
uv run ut-analysis ingest-notes \
  --file observer_notes_p001.md \
  --session-id S_P001_obs \
  --participant-id P001 \
  --project-dir ./project_data
```

### 3. Check Pipeline Status

```bash
uv run ut-analysis status --project-dir ./project_data
```

## Transcript Format

### Markdown Format

```markdown
## [MM:SS] - Speaker Name - [Task ID]
"Utterance text here..."

## [MM:SS] - Speaker Name - [Task ID]
"More utterance text..."
```

### DOCX Format

```
Speaker Name: [Timestamp] [Task ID]
"Utterance text..."

Another Speaker: [Timestamp] [Task ID]
"More text..."
```

## Notes Format

```markdown
## Observation 1 - [MM:SS]
Observer: Name
Task: TASK-ID
Confidence: 0.95

Observation description here...

---

## Observation 2 - [MM:SS]
...
```

## Running the MCP Server

The pipeline includes an MCP server for GitHub Copilot CLI integration:

```bash
uv run ut-mcp-server
```

This starts the server on stdio and provides tools for:
- State management
- File I/O
- Integration with HeyMarvin MCP
- Pipeline orchestration

## Project Structure

```
project_data/
├── project_state.json          # Pipeline state
└── data/
    ├── transcripts/            # Parsed transcripts
    ├── notes/                  # Parsed observation notes
    ├── findings/               # Extracted findings
    ├── evaluations/            # Evaluation results
    └── synthesis/              # Synthesis and reports
```

## Sample Data

The repository includes sample files for testing:
- `research_config.yaml` - Example project configuration
- `sample_transcript.md` - Example transcript
- `sample_notes.md` - Example observation notes

Try with:

```bash
uv run ut-analysis init-project \
  --config research_config.yaml \
  --project-dir ./sample_project

uv run ut-analysis ingest-transcript \
  --file sample_transcript.md \
  --transcript-id T_sample_001 \
  --participant-id P001 \
  --project-dir ./sample_project

uv run ut-analysis status --project-dir ./sample_project
```

## Next Steps

1. **Extract findings** (ut-extractor skill) - Identify usability issues and moments
2. **Evaluate findings** (ut-evaluator skill) - 5-check verification process
3. **Rate severity** (ut-severity-rater skill) - Nielsen's 5-point scale
4. **Map heuristics** (ut-heuristic-mapper skill) - Categorize by heuristics
5. **Synthesize** (ut-synthesizer skill) - Cross-participant patterns
6. **Generate reports** (ut-reporter skill) - Audience-tailored outputs

## Skills Overview

### Implemented
- **ut-controller** - Pipeline orchestration
- **ut-ingestor** - Data ingestion and parsing

### Coming Soon
- **ut-extractor** - Extract findings
- **ut-evaluator** - Verification loop
- **ut-severity-rater** - Nielsen severity scale
- **ut-heuristic-mapper** - Heuristic categorization
- **ut-synthesizer** - Theme synthesis
- **ut-reporter** - Report generation
- **ut-clipper** - Video annotations
- **ut-recommender** - Design recommendations
- **ut-contradiction** - Conflict detection

## API Usage

```python
from ut_analysis.skills.ut_controller.controller import ControllerSkill
from ut_analysis.state_management import StateManager

# Initialize
state_mgr = StateManager("/path/to/project")
controller = ControllerSkill(state_mgr)

# Initialize pipeline
result = controller.init_pipeline(
    config_file="research_config.yaml",
    project_dir="/path/to/project"
)

# Check status
status = controller.get_status()

# Get metrics
metrics = controller.get_metrics()
```

## Troubleshooting

**File not found error:**
- Ensure file paths are absolute or relative from the current working directory
- Check that file encoding is UTF-8

**Config validation errors:**
- Verify all required fields in `research_config.yaml`
- Ensure participant IDs and task IDs are unique

**State issues:**
- Delete `project_data/project_state.json` to reset
- State is auto-recovered from individual data files

## Support

For issues or questions:
1. Check existing findings in the project state
2. Review SKILL.md files for detailed documentation
3. Run with `--verbose` flag for debug output

---

Happy analyzing!
