"""Tests for controller skill."""

import pytest
import tempfile
from pathlib import Path
import yaml

from ut_analysis.skills.ut_controller.controller import ControllerSkill
from ut_analysis.state_management import StateManager


@pytest.fixture
def temp_project_dir() -> Path:
    """Create temporary project directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_config(temp_project_dir: Path) -> Path:
    """Create sample configuration."""
    config = {
        "project_id": "test-ut-001",
        "project_name": "Test Usability Study",
        "participants": [
            {"id": "P001", "name": "Test User 1"},
            {"id": "P002", "name": "Test User 2"},
        ],
        "tasks": [
            {
                "id": "TASK-001",
                "name": "Test Task 1",
                "success_criteria": "Task completed",
                "time_limit_seconds": 300,
            }
        ],
        "research_date": "2026-05-01",
    }

    config_path = temp_project_dir / "config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config, f)

    return config_path


def test_init_pipeline(temp_project_dir: Path, sample_config: Path) -> None:
    """Test pipeline initialization."""
    state_mgr = StateManager(str(temp_project_dir))
    controller = ControllerSkill(state_mgr)

    result = controller.init_pipeline(str(sample_config), str(temp_project_dir))

    assert result["status"] == "success"
    assert result["project_id"] == "test-ut-001"
    assert result["participants_count"] == 2
    assert result["tasks_count"] == 1


def test_invalid_config(temp_project_dir: Path) -> None:
    """Test with invalid configuration."""
    controller = ControllerSkill()

    result = controller.init_pipeline("nonexistent.yaml", str(temp_project_dir))

    assert result["status"] == "error"
    assert "not found" in result["error"].lower()


def test_config_validation(temp_project_dir: Path) -> None:
    """Test configuration validation."""
    controller = ControllerSkill()

    # Missing required fields
    invalid_config = {
        "project_id": "test",
        # Missing project_name, participants, tasks
    }

    config_path = temp_project_dir / "invalid.yaml"
    with open(config_path, "w") as f:
        yaml.dump(invalid_config, f)

    result = controller.init_pipeline(str(config_path), str(temp_project_dir))

    assert result["status"] == "error"
    assert "required" in result["error"].lower()
