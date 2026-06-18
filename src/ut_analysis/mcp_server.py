"""MCP Server for UT Analysis Pipeline.

Provides tools for state management, file I/O, and integration with HeyMarvin.
"""

import logging
from typing import Any
from pathlib import Path
import asyncio
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server

from .state_management import (
    StateManager,
    TranscriptManager,
    NotesManager,
    FindingsManager,
    EvaluationManager,
    SynthesisManager,
    ClipManager,
    RecommendationsManager,
    ContradictionsManager,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global managers
state_manager: StateManager | None = None
transcript_manager: TranscriptManager | None = None
notes_manager: NotesManager | None = None
findings_manager: FindingsManager | None = None
evaluation_manager: EvaluationManager | None = None
synthesis_manager: SynthesisManager | None = None
clip_manager: ClipManager | None = None
recommendations_manager: RecommendationsManager | None = None
contradictions_manager: ContradictionsManager | None = None


def initialize_managers(project_dir: str) -> None:
    """Initialize all managers with project directory."""
    global state_manager, transcript_manager, notes_manager, findings_manager, evaluation_manager, synthesis_manager, clip_manager, recommendations_manager, contradictions_manager

    project_path = Path(project_dir)
    data_dir = project_path / "data"

    state_manager = StateManager(project_path)
    transcript_manager = TranscriptManager(data_dir)
    notes_manager = NotesManager(data_dir)
    findings_manager = FindingsManager(data_dir)
    evaluation_manager = EvaluationManager(data_dir)
    synthesis_manager = SynthesisManager(data_dir)
    clip_manager = ClipManager(data_dir)
    recommendations_manager = RecommendationsManager(data_dir)
    contradictions_manager = ContradictionsManager(data_dir)

    logger.info(f"Initialized managers for project: {project_dir}")


def get_tools() -> list[Tool]:
    """Get list of available MCP tools."""
    return [
        Tool(
            name="init_project",
            description="Initialize project from config file",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_dir": {
                        "type": "string",
                        "description": "Project directory path",
                    },
                    "config_file": {
                        "type": "string",
                        "description": "Path to research_config.yaml",
                    },
                },
                "required": ["project_dir", "config_file"],
            },
        ),
        Tool(
            name="load_transcript",
            description="Load and parse transcript from file",
            inputSchema={
                "type": "object",
                "properties": {
                    "transcript_id": {
                        "type": "string",
                        "description": "Unique transcript ID",
                    },
                    "file_path": {"type": "string", "description": "Path to transcript file (.docx or .md)"},
                    "participant_id": {
                        "type": "string",
                        "description": "Participant ID",
                    },
                },
                "required": ["transcript_id", "file_path", "participant_id"],
            },
        ),
        Tool(
            name="load_notes",
            description="Load and parse researcher observation notes",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Session ID for notes",
                    },
                    "file_path": {
                        "type": "string",
                        "description": "Path to markdown notes file",
                    },
                    "participant_id": {
                        "type": "string",
                        "description": "Associated participant ID",
                    },
                },
                "required": ["session_id", "file_path", "participant_id"],
            },
        ),
        Tool(
            name="save_findings",
            description="Save extracted findings to storage",
            inputSchema={
                "type": "object",
                "properties": {
                    "findings_id": {
                        "type": "string",
                        "description": "Findings batch ID",
                    },
                    "findings_data": {
                        "type": "object",
                        "description": "Findings data to save",
                    },
                },
                "required": ["findings_id", "findings_data"],
            },
        ),
        Tool(
            name="load_findings",
            description="Load previously extracted findings",
            inputSchema={
                "type": "object",
                "properties": {
                    "findings_id": {
                        "type": "string",
                        "description": "Findings batch ID",
                    },
                },
                "required": ["findings_id"],
            },
        ),
        Tool(
            name="save_evaluation",
            description="Save evaluation results",
            inputSchema={
                "type": "object",
                "properties": {
                    "eval_id": {
                        "type": "string",
                        "description": "Evaluation batch ID",
                    },
                    "eval_data": {
                        "type": "object",
                        "description": "Evaluation data to save",
                    },
                },
                "required": ["eval_id", "eval_data"],
            },
        ),
        Tool(
            name="load_evaluation",
            description="Load evaluation results",
            inputSchema={
                "type": "object",
                "properties": {
                    "eval_id": {
                        "type": "string",
                        "description": "Evaluation batch ID",
                    },
                },
                "required": ["eval_id"],
            },
        ),
        Tool(
            name="save_synthesis",
            description="Save synthesis results",
            inputSchema={
                "type": "object",
                "properties": {
                    "synthesis_id": {
                        "type": "string",
                        "description": "Synthesis batch ID",
                    },
                    "synthesis_data": {
                        "type": "object",
                        "description": "Synthesis data to save",
                    },
                },
                "required": ["synthesis_id", "synthesis_data"],
            },
        ),
        Tool(
            name="load_synthesis",
            description="Load synthesis results",
            inputSchema={
                "type": "object",
                "properties": {
                    "synthesis_id": {
                        "type": "string",
                        "description": "Synthesis batch ID",
                    },
                },
                "required": ["synthesis_id"],
            },
        ),
        Tool(
            name="get_task_matrix",
            description="Get task completion matrix",
            inputSchema={
                "type": "object",
                "properties": {
                    "synthesis_id": {
                        "type": "string",
                        "description": "Synthesis ID to extract matrix from",
                    },
                },
                "required": ["synthesis_id"],
            },
        ),
        Tool(
            name="get_severity_summary",
            description="Get severity distribution summary",
            inputSchema={
                "type": "object",
                "properties": {
                    "synthesis_id": {
                        "type": "string",
                        "description": "Synthesis ID",
                    },
                },
                "required": ["synthesis_id"],
            },
        ),
        Tool(
            name="marvin_pull_transcript",
            description="Pull transcript from HeyMarvin MCP",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "integer",
                        "description": "HeyMarvin project ID",
                    },
                    "file_id": {
                        "type": "string",
                        "description": "HeyMarvin file ID",
                    },
                    "transcript_id": {
                        "type": "string",
                        "description": "Local transcript ID",
                    },
                },
                "required": ["project_id", "file_id", "transcript_id"],
            },
        ),
        Tool(
            name="marvin_search_project",
            description="Search HeyMarvin project for sessions",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "integer",
                        "description": "HeyMarvin project ID",
                    },
                    "query": {
                        "type": "string",
                        "description": "Search query",
                    },
                },
                "required": ["project_id", "query"],
            },
        ),
        Tool(
            name="validate_provenance",
            description="Validate that a claim traces back to source",
            inputSchema={
                "type": "object",
                "properties": {
                    "finding_id": {
                        "type": "string",
                        "description": "Finding ID",
                    },
                    "transcript_id": {
                        "type": "string",
                        "description": "Transcript ID",
                    },
                    "quote": {"type": "string", "description": "Quote to verify"},
                },
                "required": ["finding_id", "transcript_id", "quote"],
            },
        ),
        Tool(
            name="get_pipeline_status",
            description="Get current pipeline execution status",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="list_transcripts",
            description="List all loaded transcripts",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="list_findings",
            description="List all extracted findings",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="update_phase",
            description="Update pipeline phase",
            inputSchema={
                "type": "object",
                "properties": {
                    "phase": {
                        "type": "string",
                        "description": "Phase name",
                        "enum": [
                            "initialized",
                            "ingestion_complete",
                            "extraction_complete",
                            "evaluation_complete",
                            "severity_rating_complete",
                            "heuristic_mapping_complete",
                            "synthesis_complete",
                            "reporting_complete",
                            "clipping_complete",
                            "recommendations_complete",
                            "contradictions_complete",
                        ],
                    },
                },
                "required": ["phase"],
            },
        ),
        Tool(
            name="extract_media_clips",
            description="Extract video/audio clips from findings",
            inputSchema={
                "type": "object",
                "properties": {
                    "findings_batch_id": {
                        "type": "string",
                        "description": "Findings batch ID",
                    },
                    "clip_batch_id": {
                        "type": "string",
                        "description": "Clip batch ID",
                    },
                    "clip_config": {
                        "type": "object",
                        "description": "Clip extraction configuration",
                    },
                },
                "required": ["findings_batch_id", "clip_batch_id"],
            },
        ),
        Tool(
            name="load_clips",
            description="Load extracted clips",
            inputSchema={
                "type": "object",
                "properties": {
                    "clip_batch_id": {
                        "type": "string",
                        "description": "Clip batch ID",
                    },
                },
                "required": ["clip_batch_id"],
            },
        ),
        Tool(
            name="generate_recommendations",
            description="Generate actionable recommendations from findings",
            inputSchema={
                "type": "object",
                "properties": {
                    "findings_batch_id": {
                        "type": "string",
                        "description": "Findings batch ID",
                    },
                    "recommendations_batch_id": {
                        "type": "string",
                        "description": "Recommendations batch ID",
                    },
                    "recommendation_config": {
                        "type": "object",
                        "description": "Recommendation generation configuration",
                    },
                },
                "required": ["findings_batch_id", "recommendations_batch_id"],
            },
        ),
        Tool(
            name="load_recommendations",
            description="Load generated recommendations",
            inputSchema={
                "type": "object",
                "properties": {
                    "recommendations_batch_id": {
                        "type": "string",
                        "description": "Recommendations batch ID",
                    },
                },
                "required": ["recommendations_batch_id"],
            },
        ),
        Tool(
            name="analyze_contradictions",
            description="Analyze contradictions and inconsistencies in findings",
            inputSchema={
                "type": "object",
                "properties": {
                    "findings_batch_id": {
                        "type": "string",
                        "description": "Findings batch ID",
                    },
                    "contradictions_batch_id": {
                        "type": "string",
                        "description": "Contradictions batch ID",
                    },
                    "analysis_config": {
                        "type": "object",
                        "description": "Contradiction analysis configuration",
                    },
                },
                "required": ["findings_batch_id", "contradictions_batch_id"],
            },
        ),
        Tool(
            name="load_contradictions",
            description="Load contradiction analysis results",
            inputSchema={
                "type": "object",
                "properties": {
                    "contradictions_batch_id": {
                        "type": "string",
                        "description": "Contradictions batch ID",
                    },
                },
                "required": ["contradictions_batch_id"],
            },
        ),
    ]


async def handle_tool_call(name: str, arguments: dict[str, Any]) -> str:
    """Handle tool calls."""
    try:
        if name == "init_project":
            if state_manager is None:
                return "Error: State manager not initialized"
            project_dir = arguments.get("project_dir")
            config_file = arguments.get("config_file")
            state_manager.update_phase("initialized")
            return f"Project initialized with config: {config_file}"

        elif name == "get_pipeline_status":
            if state_manager is None:
                return "Error: State manager not initialized"
            status = state_manager.get_pipeline_status()
            return str(status)

        elif name == "list_transcripts":
            if transcript_manager is None:
                return "Error: Transcript manager not initialized"
            transcripts = transcript_manager.list_transcripts()
            return f"Transcripts: {transcripts}"

        elif name == "list_findings":
            if findings_manager is None:
                return "Error: Findings manager not initialized"
            findings_list = findings_manager.list_findings()
            return f"Findings: {findings_list}"

        elif name == "update_phase":
            if state_manager is None:
                return "Error: State manager not initialized"
            phase = arguments.get("phase")
            state_manager.update_phase(phase)
            return f"Updated phase to: {phase}"

        elif name == "extract_media_clips":
            if clip_manager is None:
                return "Error: Clip manager not initialized"
            # This would integrate with the clipper skill
            findings_batch_id = arguments.get("findings_batch_id")
            clip_batch_id = arguments.get("clip_batch_id")
            clip_config = arguments.get("clip_config", {})
            # Placeholder for actual clip extraction
            return f"Clip extraction initiated for findings {findings_batch_id} -> clips {clip_batch_id}"

        elif name == "load_clips":
            if clip_manager is None:
                return "Error: Clip manager not initialized"
            clip_batch_id = arguments.get("clip_batch_id")
            clips = clip_manager.load_clips(clip_batch_id)
            return f"Loaded clips: {clips}"

        elif name == "generate_recommendations":
            if recommendations_manager is None:
                return "Error: Recommendations manager not initialized"
            # This would integrate with the recommender skill
            findings_batch_id = arguments.get("findings_batch_id")
            recommendations_batch_id = arguments.get("recommendations_batch_id")
            recommendation_config = arguments.get("recommendation_config", {})
            # Placeholder for actual recommendation generation
            return f"Recommendation generation initiated for findings {findings_batch_id} -> recommendations {recommendations_batch_id}"

        elif name == "load_recommendations":
            if recommendations_manager is None:
                return "Error: Recommendations manager not initialized"
            recommendations_batch_id = arguments.get("recommendations_batch_id")
            recommendations = recommendations_manager.load_recommendations(recommendations_batch_id)
            return f"Loaded recommendations: {recommendations}"

        elif name == "analyze_contradictions":
            if contradictions_manager is None:
                return "Error: Contradictions manager not initialized"
            # This would integrate with the contradiction skill
            findings_batch_id = arguments.get("findings_batch_id")
            contradictions_batch_id = arguments.get("contradictions_batch_id")
            analysis_config = arguments.get("analysis_config", {})
            # Placeholder for actual contradiction analysis
            return f"Contradiction analysis initiated for findings {findings_batch_id} -> contradictions {contradictions_batch_id}"

        elif name == "load_contradictions":
            if contradictions_manager is None:
                return "Error: Contradictions manager not initialized"
            contradictions_batch_id = arguments.get("contradictions_batch_id")
            contradictions = contradictions_manager.load_contradictions(contradictions_batch_id)
            return f"Loaded contradictions: {contradictions}"

        else:
            return f"Tool '{name}' not yet implemented"

    except Exception as e:
        logger.error(f"Tool error: {e}")
        return f"Error: {str(e)}"


async def main() -> None:
    """Run the MCP server."""
    server = Server("ut-analysis-mcp")

    # Initialize managers with default project directory
    project_dir = Path.home() / ".ut-analysis"
    initialize_managers(str(project_dir))

    # Register tools
    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return get_tools()

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        result = await handle_tool_call(name, arguments)
        return [TextContent(type="text", text=result)]

    async with stdio_server(server) as (read_stream, write_stream):
        logger.info("UT Analysis MCP Server started")
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
