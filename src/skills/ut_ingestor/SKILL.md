# ut-ingestor Skill

## Purpose

The **ut-ingestor** skill handles data ingestion from multiple sources:
- Local `.docx` and `.md` transcript files
- HeyMarvin MCP server (via mcp.heymarvin.com)
- Researcher observation notes (timestamped markdown)
- Task definitions from `research_config.yaml`

It parses raw data into structured JSON turns with speaker attribution, timestamps, task IDs, and metadata.

## Key Responsibilities

1. **Transcript Parsing**
   - Parse `.docx` files (handles different formatting)
   - Parse `.md` files with timestamp markers
   - Extract speaker, timestamp, utterance per turn
   - Assign task IDs based on timestamp ranges or explicit markers
   - Preserve original formatting and quotes

2. **Notes Parsing**
   - Parse markdown observation files with timestamps
   - Extract observer name, timestamp, observation text
   - Link to participant and task IDs
   - Preserve formatting and emphasis

3. **HeyMarvin Integration**
   - Call HeyMarvin MCP to list sessions in project
   - Fetch full transcript from HeyMarvin
   - Convert HeyMarvin format to standard schema
   - Handle authentication and API errors gracefully

4. **Task Definition Loading**
   - Extract task definitions from `research_config.yaml`
   - Build lookup tables by task ID, name, and time ranges
   - Parse success criteria and time limits

5. **Validation**
   - Ensure all turns have speaker, timestamp, utterance
   - Validate timestamp formatting (ISO or MM:SS)
   - Check task ID references are valid
   - Flag missing or malformed data with line numbers

## Input Format

### Load Local Transcript

```json
{
  "command": "load_transcript",
  "transcript_id": "T_P001_session1",
  "file_path": "/data/participant_001_transcript.docx",
  "participant_id": "P001",
  "session_date": "2026-05-01"
}
```

### Load HeyMarvin Transcript

```json
{
  "command": "load_marvin_transcript",
  "project_id": 12345,
  "file_id": "abc-def-ghi",
  "transcript_id": "T_marvin_session1",
  "participant_id": "P001"
}
```

### Load Notes

```json
{
  "command": "load_notes",
  "session_id": "S_P001_obs",
  "file_path": "/data/observer_notes_p001.md",
  "participant_id": "P001"
}
```

## Output Format

### Parsed Transcript

```json
{
  "transcript_id": "T_P001_session1",
  "participant_id": "P001",
  "session_date": "2026-05-01T10:00:00Z",
  "duration_seconds": 1800,
  "turns": [
    {
      "turn_id": "T_P001_session1_001",
      "speaker": "Researcher",
      "timestamp": "00:00",
      "utterance": "Good morning, thanks for joining...",
      "task_id": null,
      "metadata": {"speaker_role": "researcher"}
    },
    {
      "turn_id": "T_P001_session1_002",
      "speaker": "Participant",
      "timestamp": "00:15",
      "utterance": "Happy to be here!",
      "task_id": null,
      "metadata": {"speaker_role": "participant"}
    },
    {
      "turn_id": "T_P001_session1_003",
      "speaker": "Researcher",
      "timestamp": "00:30",
      "utterance": "Okay, your first task is to find our product...",
      "task_id": "TASK-001",
      "metadata": {"speaker_role": "researcher", "instruction": true}
    }
  ],
  "source_file": "/data/participant_001_transcript.docx",
  "metadata": {"format": "docx", "encoding": "utf-8"}
}
```

### Parsed Notes

```json
{
  "session_id": "S_P001_obs",
  "participant_id": "P001",
  "notes": [
    {
      "note_id": "N_P001_001",
      "timestamp": "00:45",
      "observation": "User seemed confused about navigation menu",
      "task_id": "TASK-001",
      "confidence": 0.95,
      "observer": "Researcher A",
      "metadata": {"note_type": "behavior"}
    }
  ],
  "source_file": "/data/observer_notes_p001.md"
}
```

## Supported Formats

### Transcript Formats

**DOCX Format:**
```
[Speaker Name]: [Timestamp] [Task ID?]
"Utterance text..."

[Speaker Name]: [Timestamp] [Task ID?]
"Utterance text..."
```

**Markdown Format:**
```
## [Timestamp] - [Speaker Name] - [Task ID?]
Utterance text...

## [Timestamp] - [Speaker Name] - [Task ID?]
More utterance text...
```

### Notes Markdown Format

```
## Observation 1 - [Timestamp]
Observer: [Name]
Task: [Task ID]
Confidence: [0.0-1.0]

[Observation text...]

---

## Observation 2 - [Timestamp]
...
```

## Timestamp Handling

- **ISO Format**: `2026-05-01T10:15:30Z`
- **MM:SS Format**: `10:15`
- **Auto-conversion**: Convert MM:SS to absolute timestamps based on session start time

## Task ID Assignment

Three methods (in priority order):
1. **Explicit Marker**: Task ID in turn header (`[Task-001]`)
2. **Config-based**: Match turn timestamp to task time ranges in config
3. **None**: Leave task_id null if not determinable

## Validation Rules

- Every turn must have: turn_id, speaker, timestamp, utterance
- Timestamps must be in ISO format or MM:SS (will be normalized)
- Speaker name must be non-empty
- Utterance length ≥ 1 character
- Task IDs must reference valid tasks from config
- Notes timestamps must align within transcript timespan
- Observation text must be non-empty

## Error Handling

**Malformed Transcript:**
- Line number reported for each error
- Suggested correction provided
- Option to skip line or fill in placeholder values

**Missing Task References:**
- Warning logged but processing continues
- Task ID remains null
- Can be manually assigned later if needed

**HeyMarvin API Errors:**
- Retry with exponential backoff
- Provide auth troubleshooting steps
- Fallback to manual transcript upload

## Example Usage

```python
from ut_analysis.skills.ingestor import IngestorSkill
from ut_analysis.state_management import StateManager

state_mgr = StateManager("/project/dir")
ingestor = IngestorSkill(state_mgr)

# Load local transcript
result = ingestor.load_transcript(
    transcript_id="T_P001_s1",
    file_path="transcript.docx",
    participant_id="P001",
    session_date="2026-05-01"
)

# Load notes
notes_result = ingestor.load_notes(
    session_id="S_P001_obs",
    file_path="observer_notes.md",
    participant_id="P001"
)

# Validate all loaded data
validation = ingestor.validate_ingestion()
```

## Integration Points

- **MCP Tools**: `load_transcript`, `load_notes`, `marvin_pull_transcript`, `marvin_search_project`
- **State Management**: Stores parsed transcripts in `data/transcripts/` and notes in `data/notes/`
- **HeyMarvin MCP**: Calls HeyMarvin endpoints for session retrieval
- **ut-controller**: Receives config for task definitions and participant metadata
- **ut-extractor**: Downstream skill consumes parsed turn structure

## Quality Metrics

- Transcripts loaded: Count of successfully parsed transcripts
- Turns parsed: Total utterance turns across all transcripts
- Notes parsed: Total observation notes across all files
- Task ID coverage: % of turns with valid task IDs
- Validation errors: Count and severity of parsing issues
