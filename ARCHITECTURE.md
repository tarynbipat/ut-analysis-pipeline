"""
Comprehensive architecture and setup documentation for UT Analysis Pipeline.
"""

# UT Analysis Pipeline - Complete Architecture

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     GitHub Copilot CLI Integration                   │
│  (via Skills: .md files with domain logic + reasoning instructions)  │
└─────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────┐
│                        MCP Server (stdio)                            │
│  • 19+ Tools for state management                                   │
│  • File I/O and persistence                                         │
│  • External service integration (HeyMarvin)                         │
└─────────────────────────────────────────────────────────────────────┘
                                   ↓
┌──────────────────────────────────┬──────────────────────────────────┐
│        Skills Layer               │     State Management Layer       │
│  (Domain Logic & Reasoning)       │    (Persistence & Coordination) │
├──────────────────────────────────┼──────────────────────────────────┤
│ • ut-controller                  │ • StateManager                   │
│ • ut-ingestor ✓                  │ • TranscriptManager              │
│ • ut-extractor                   │ • NotesManager                   │
│ • ut-evaluator                   │ • FindingsManager                │
│ • ut-severity-rater              │ • EvaluationManager              │
│ • ut-heuristic-mapper            │ • SynthesisManager               │
│ • ut-synthesizer                 │ • Data Models (Pydantic)         │
│ • ut-reporter                    │                                  │
│ • ut-clipper                     │                                  │
│ • ut-recommender                 │                                  │
│ • ut-contradiction               │                                  │
└──────────────────────────────────┴──────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    Data Storage Layer (JSON Files)                   │
│  ┌────────────┬──────────────┬──────────────┬──────────────────┐   │
│  │ Transcripts│ Notes        │ Findings     │ Evaluations      │   │
│  │            │              │              │ Synthesis        │   │
│  │            │              │              │ Reports          │   │
│  └────────────┴──────────────┴──────────────┴──────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                   ↓
┌──────────────────────────────────┬──────────────────────────────────┐
│      External Data Sources        │     External Integrations        │
├──────────────────────────────────┼──────────────────────────────────┤
│ • Local .docx/.md transcripts    │ • HeyMarvin MCP                  │
│ • Markdown observation notes     │ • GitHub Copilot CLI             │
│ • research_config.yaml          │ • LLM Services (GPT-4, etc)      │
└──────────────────────────────────┴──────────────────────────────────┘
```

## Data Flow

```
1. INGESTION PHASE
   ├─ Load transcripts (.docx/.md) via ut-ingestor
   │  └─ Parse into TranscriptTurn objects
   ├─ Load observation notes (markdown) via ut-ingestor
   │  └─ Parse into ObservationNote objects
   └─ Load config + tasks via ut-controller
      └─ Store in project_state.json

2. EXTRACTION PHASE
   ├─ ut-extractor analyzes transcripts + notes
   ├─ Categorizes: issues, outcomes, pain points, positive moments, quotes
   └─ Creates Finding objects with full provenance

3. EVALUATION PHASE (Revelation Loop, max 3 iterations)
   ├─ ut-evaluator runs 5 checks per finding:
   │  ├─ Verbatim quote match
   │  ├─ Meaning accuracy
   │  ├─ Task attribution
   │  ├─ No researcher interpretation
   │  └─ Severity justification
   ├─ Failed findings → ut-extractor with corrections
   └─ EvaluatedFinding objects created

4. SEVERITY RATING PHASE
   ├─ ut-severity-rater applies Nielsen scale (0-4)
   ├─ Considers: frequency, task impact, persistence
   └─ SeverityRating objects with evidence

5. HEURISTIC MAPPING PHASE
   ├─ ut-heuristic-mapper categorizes by Nielsen's 10 heuristics
   ├─ Supports custom heuristic frameworks
   └─ HeuristicMapping objects created

6. SYNTHESIS PHASE
   ├─ ut-synthesizer identifies cross-participant themes
   ├─ Builds task completion matrix
   ├─ Finds high-failure tasks and violated heuristics
   └─ SynthesisReport object created

7. REPORTING PHASE
   ├─ ut-reporter generates audience-specific reports:
   │  ├─ Design team (detailed issues, screenshots, recommendations)
   │  ├─ PM team (executive summary, top 5 issues)
   │  └─ Leadership (one-page with go/no-go recommendation)
   └─ Full provenance tracing each claim to source
```

## File Organization

```
project_dir/
├── project_state.json
│   └─ Central state tracking all phases + metrics
│
└── data/
    ├── transcripts/
    │   ├─ T_P001_session1.json  (parsed turns)
    │   ├─ T_P002_session1.json
    │   └─ ... (one per transcript)
    │
    ├── notes/
    │   ├─ S_P001_obs_notes.json  (parsed observations)
    │   └─ ... (one per session)
    │
    ├── findings/
    │   ├─ batch_001_findings.json  (extracted findings)
    │   ├─ batch_002_findings.json
    │   └─ ...
    │
    ├── evaluations/
    │   ├─ batch_001_eval.json
    │   └─ ...
    │
    └── synthesis/
        ├─ synthesis_001.json
        ├─ report_001_design_report.json
        ├─ report_001_pm_report.json
        └─ report_001_leadership_report.json
```

## Key Data Models

### TranscriptTurn
```python
turn_id: str                    # Unique within transcript
speaker: str                    # "Participant", "Researcher", etc
timestamp: str                  # ISO format or MM:SS
utterance: str                  # Verbatim text
task_id: Optional[str]         # Link to task definition
```

### Finding
```python
finding_id: str
category: FindingCategory      # usability_issue, task_outcome, etc
verbatim_quote: str            # Exact text from source
speaker: str
timestamp: str
source_transcript_id: str      # Full provenance
task_id: Optional[str]
participant_id: str
confidence: float              # 0.0-1.0
severity: Optional[SeverityLevel]  # 0-4 (Nielsen scale)
```

### EvaluatedFinding
```python
original_finding: Finding
evaluation_results: List[EvaluationResult]
all_passed: bool
failed_checks: List[str]       # Items failing 5-check verification
correction_instructions: Optional[str]  # For revelation loop
revision_count: int            # Tracks iterations
```

### Theme
```python
title: str
description: str
finding_ids: List[str]         # Cross-participant
participant_count: int         # How many participants affected
frequency: int                 # Absolute count
primary_heuristic: Optional[str]
severity_distribution: Dict    # {CRITICAL: 3, MAJOR: 2, ...}
```

## Pipeline Phases

```
INITIALIZED
  ↓ (load transcripts + notes)
INGESTION_COMPLETE
  ↓ (extract findings)
EXTRACTION_COMPLETE
  ↓ (verify with 5 checks)
EVALUATION_COMPLETE
  ↓ (rate severity 0-4)
SEVERITY_RATING_COMPLETE
  ↓ (map to heuristics)
HEURISTIC_MAPPING_COMPLETE
  ↓ (cross-participant synthesis)
SYNTHESIS_COMPLETE
  ↓ (generate reports)
REPORTING_COMPLETE
```

## MCP Tools (19+)

### Project Management
- `init_project` - Initialize from config
- `get_pipeline_status` - Current phase + metrics
- `update_phase` - Advance to next phase

### Data Ingestion (ut-ingestor skill)
- `load_transcript` - Parse .docx/.md files
- `load_notes` - Parse observation markdown
- `marvin_pull_transcript` - Fetch from HeyMarvin
- `marvin_search_project` - Search HeyMarvin sessions

### Data Persistence
- `save_findings` / `load_findings` - Extract storage
- `save_evaluation` / `load_evaluation` - Eval storage
- `save_synthesis` / `load_synthesis` - Synthesis storage

### Querying
- `list_transcripts` - All loaded transcripts
- `list_findings` - All extracted findings
- `get_task_matrix` - Task completion grid
- `get_severity_summary` - Distribution by severity

### Validation
- `validate_provenance` - Trace claim to source

## Skill Integration

Each skill is:
1. **SKILL.md** - Reasoning instructions for GitHub Copilot CLI
2. **Python module** - Implementation with business logic
3. **MCP tools** - Stateless functions for the MCP server

### Example: ut-extractor (upcoming)

**SKILL.md** contains:
- Purpose and responsibilities
- Input/output format specifications
- Categorization rules (usability issue vs pain point vs positive moment)
- Example extractions
- Confidence scoring guidelines

**Python implementation** handles:
- Actual LLM calls or ML models for extraction
- Formatting validation
- Quote verification against source
- Caching and batching

**MCP tools** provide:
- `save_findings` - Persist extracted findings
- `load_transcript` - Access parsed transcripts
- `validate_provenance` - Link findings to sources

## Configuration

`research_config.yaml` defines:
```yaml
project_id: unique-id
project_name: Human name
participants:
  - id: P001
    demographics: {...}
tasks:
  - id: TASK-001
    success_criteria: "..."
    time_limit_seconds: 300
heuristic_framework: "nielsen_10"
custom_heuristics: [...]  # Optional override
```

## Quality Gates

Before advancing phases:
1. **Ingestion** - At least 1 transcript loaded
2. **Extraction** - At least 1 finding extracted
3. **Evaluation** - All findings must pass 5-check (with revelation loop)
4. **Severity Rating** - Each finding must have justification
5. **Heuristic Mapping** - All findings must map to heuristics
6. **Synthesis** - Data from at least N-1 participants
7. **Reporting** - Synthesis must be complete

## Provenance Tracking

Every finding includes:
```json
{
  "finding_id": "F_001",
  "verbatim_quote": "...",
  "speaker": "Participant",
  "timestamp": "02:15",
  "source_transcript_id": "T_P001_session1",
  "task_id": "TASK-001"
}
```

Reports generate claims like:
```json
{
  "claim": "4 of 5 participants struggled with discount code visibility",
  "evidence": [
    "F_001 from T_P001, T_P002, T_P004, T_P005",
    "Observer note: N_P001_002"
  ],
  "severity": 2
}
```

---

Full architecture designed for extensibility, auditability, and integration with GitHub Copilot CLI for intelligent reasoning at every step.
