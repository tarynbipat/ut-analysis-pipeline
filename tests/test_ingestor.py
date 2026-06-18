"""Tests for ingestor skill."""

import pytest
import tempfile
from pathlib import Path
from docx import Document

from ut_analysis.skills.ut_ingestor.ingestor import IngestorSkill
from ut_analysis.state_management import StateManager, TranscriptManager, NotesManager


@pytest.fixture
def temp_project_dir() -> Path:
    """Create temporary project directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_managers(temp_project_dir: Path):
    """Create managers."""
    state_mgr = StateManager(str(temp_project_dir))
    transcript_mgr = TranscriptManager(temp_project_dir / "data")
    notes_mgr = NotesManager(temp_project_dir / "data")
    return state_mgr, transcript_mgr, notes_mgr


@pytest.fixture
def sample_markdown_transcript(temp_project_dir: Path) -> Path:
    """Create sample markdown transcript."""
    content = """## [00:00] - Researcher - 
"Hello, thanks for joining us."

## [00:15] - Participant - TASK-001
"Happy to be here!"

## [01:00] - Researcher - TASK-001
"Let's begin with the first task."
"""
    path = temp_project_dir / "test_transcript.md"
    with open(path, "w") as f:
        f.write(content)
    return path


def test_parse_markdown_transcript(sample_markdown_transcript: Path) -> None:
    """Test markdown transcript parsing."""
    temp_dir = sample_markdown_transcript.parent
    state_mgr = StateManager(str(temp_dir))
    ingestor = IngestorSkill(state_mgr)

    result = ingestor.load_transcript(
        "T_001",
        str(sample_markdown_transcript),
        "P001",
        "2026-05-01T10:00:00Z",
    )

    assert result["status"] == "success"
    assert result["turns_count"] == 3


def test_load_notes(temp_project_dir: Path, sample_managers) -> None:
    """Test observation notes loading."""
    state_mgr, _, notes_mgr = sample_managers

    content = """## Observation 1 - [00:15]
Observer: Test Observer
Task: TASK-001
Confidence: 0.95

User hesitated briefly at this step.
"""

    notes_path = temp_project_dir / "test_notes.md"
    with open(notes_path, "w") as f:
        f.write(content)

    ingestor = IngestorSkill(state_mgr, notes_manager=notes_mgr)
    result = ingestor.load_notes("S_001", str(notes_path), "P001")

    assert result["status"] == "success"
    assert result["notes_count"] >= 1
