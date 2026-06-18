# Usability Test Analysis Pipeline

A comprehensive usability test analysis platform built with Python, featuring GitHub Copilot CLI skills and an MCP server for seamless integration.

## Features

- **Multi-source Data Ingestion**: Parse .docx/.md transcripts and HeyMarvin sessions
- **Structured Extraction**: Convert transcripts into timestamped, attributed findings
- **5-Check Verification**: Validate findings against source material
- **Severity Rating**: Nielsen's 5-point severity scale with evidence justification
- **Heuristic Mapping**: Map issues to Nielsen's 10 usability heuristics
- **Cross-Participant Synthesis**: Build themes and patterns across participants
- **Audience-Tailored Reports**: Design, PM, and leadership views with full provenance
- **GitHub Copilot CLI Integration**: Skills-based domain logic for reasoning
- **MCP Server**: State management, file I/O, and external tool integration

## Architecture

```
src/
├── skills/           # Domain logic (SKILL.md + Python implementations)
├── mcp_tools/        # MCP server tools for state management
├── models/           # Data models (Pydantic)
├── mcp_server.py     # MCP server entry point
└── cli.py            # CLI interface
```

## Quick Start

### Installation

```bash
# Clone the repository
git clone <repo>
cd ut-analysis-pipeline

# Install with uv
uv sync
```

### Start MCP Server

```bash
uv run ut-mcp-server
```

### Use CLI

```bash
uv run ut-analysis init-project --config research_config.yaml
uv run ut-analysis ingest-transcript --file transcript.docx
uv run ut-analysis extract
uv run ut-analysis evaluate
uv run ut-analysis synthesize
uv run ut-analysis report --format design
```

## Skills

1. **ut-controller**: Pipeline orchestration and status tracking
2. **ut-ingestor**: Transcript and notes parsing from multiple sources
3. **ut-extractor**: Finding extraction with structured categorization
4. **ut-evaluator**: 5-check verification with revelation loops
5. **ut-severity-rater**: Nielsen severity scale rating
6. **ut-heuristic-mapper**: Heuristic classification
7. **ut-synthesizer**: Cross-participant theme synthesis
8. **ut-reporter**: Audience-tailored report generation
9. **ut-clipper**: Video clip annotation and timestamping
10. **ut-recommender**: Design recommendation generation
11. **ut-contradiction**: Conflict detection across participants

## MCP Tools (19+)

- `init_project`: Initialize from config
- `load_transcript`: Parse and store transcripts
- `load_notes`: Parse and store observation notes
- `save_findings`: Persist extracted findings
- `load_findings`: Retrieve findings
- `save_evaluation`: Persist evaluation results
- `load_evaluation`: Retrieve evaluation results
- `get_task_matrix`: Task completion matrix
- `get_severity_summary`: Severity distribution
- `marvin_pull_transcript`: Fetch from HeyMarvin
- `marvin_search_project`: Search HeyMarvin projects
- `validate_provenance`: Trace claims to sources
- And 7 more...

## Configuration

See `research_config.yaml` for:
- Task definitions with success criteria
- Participant metadata
- Heuristic frameworks
- Report preferences

## Development

```bash
# Run tests
uv run pytest

# Run linting
uv run ruff check src/

# Format code
uv run black src/
```

