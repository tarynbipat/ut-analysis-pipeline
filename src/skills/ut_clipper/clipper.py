"""Clipper skill implementation for extracting video/audio clips from findings."""

import logging
from typing import Any, Optional, Dict, List
from datetime import datetime
from pathlib import Path
import json
import re

from ut_analysis.models import (
    Finding,
    MediaClip,
    ClipMetadata,
    ClipPlaylist,
)
from ut_analysis.state_management import (
    StateManager,
    FindingsManager,
    ClipManager,
)

logger = logging.getLogger(__name__)


class ClipperSkill:
    """Extracts video/audio clips from usability test recordings."""

    def __init__(
        self,
        state_manager: StateManager,
        findings_manager: FindingsManager | None = None,
        clip_manager: ClipManager | None = None,
    ) -> None:
        self.state_manager = state_manager
        self.findings_manager = findings_manager or FindingsManager(
            state_manager.project_dir / "data"
        )
        self.clip_manager = clip_manager or ClipManager(
            state_manager.project_dir / "data"
        )

    def extract_clips(
        self,
        findings_batch_id: str,
        clip_batch_id: str = "clips_default",
        clip_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Extract clips from findings."""
        try:
            # Load findings
            findings_data = self.findings_manager.load_findings(findings_batch_id)
            findings = [Finding(**f) for f in findings_data.get("findings", [])]

            # Default clip config
            if clip_config is None:
                clip_config = {
                    "source_media_dir": str(self.state_manager.project_dir / "recordings"),
                    "output_dir": str(self.state_manager.project_dir / "clips"),
                    "clip_duration_seconds": 30,
                    "buffer_seconds": 5,
                    "include_audio": True,
                    "compression_quality": "medium",
                    "privacy_filters": ["face_blur"],
                    "output_formats": ["mp4", "webm"],
                }

            # Filter findings that have timestamps and could benefit from clips
            clippable_findings = self._filter_clippable_findings(findings)

            # Extract clips (simulated)
            clips = []
            for i, finding in enumerate(clippable_findings):
                clip = self._extract_clip(finding, i + 1, clip_config)
                clips.append(clip)

            # Create playlists
            playlists = self._create_playlists(clips)

            # Calculate statistics
            stats = self._calculate_clip_stats(clips)

            # Prepare result
            result = {
                "clip_batch_id": clip_batch_id,
                "clips": [clip.model_dump() for clip in clips],
                "playlists": {name: playlist.model_dump() for name, playlist in playlists.items()},
                "clip_stats": stats,
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Save clip metadata
            self.clip_manager.save_clips(clip_batch_id, result)

            # Update state
            self.state_manager.add_finding(f"{clip_batch_id}_clips", {
                "total_clips": len(clips),
                "playlists_created": len(playlists),
                "critical_clips": sum(1 for c in clips if c.metadata.severity == "critical"),
            })

            logger.info(f"Extracted {len(clips)} clips in batch {clip_batch_id}")

            return result

        except Exception as e:
            logger.error(f"Clip extraction failed: {e}")
            return {"status": "error", "error": str(e)}

    def _filter_clippable_findings(self, findings: List[Finding]) -> List[Finding]:
        """Filter findings that would benefit from video clips."""
        clippable = []

        for finding in findings:
            # Must have timestamp
            if not finding.timestamp:
                continue

            # Must have sufficient severity to warrant a clip
            if finding.severity and finding.severity >= 2:  # Major or higher
                clippable.append(finding)
            # Or contains behavioral keywords
            elif any(keyword in finding.description.lower() for keyword in [
                "struggled", "confused", "frustrated", "searched", "clicked",
                "typed", "looked", "paused", "hesitated", "repeated"
            ]):
                clippable.append(finding)

        return clippable

    def _extract_clip(
        self, finding: Finding, clip_number: int, config: Dict[str, Any]
    ) -> MediaClip:
        """Extract a single clip (simulated)."""
        # Parse timestamp
        start_time_seconds = self._timestamp_to_seconds(finding.timestamp)

        # Calculate clip range
        buffer = config["buffer_seconds"]
        duration = config["clip_duration_seconds"]
        clip_start = max(0, start_time_seconds - buffer)
        clip_end = clip_start + duration

        # Generate clip title
        title = self._generate_clip_title(finding)

        # Determine severity label
        severity_label = self._severity_to_label(finding.severity or 0)

        # Simulate file paths
        base_filename = f"CLIP_{clip_number:03d}_{severity_label}_{finding.finding_id}"
        files = {}

        for fmt in config["output_formats"]:
            filename = f"{base_filename}.{fmt}"
            filepath = Path(config["output_dir"]) / filename
            files[fmt] = str(filepath)

        # Create metadata
        metadata = ClipMetadata(
            participant_id=finding.participant_id,
            task_id=finding.task_id,
            theme=self._determine_clip_theme(finding),
            severity=severity_label,
            privacy_processed=len(config.get("privacy_filters", [])) > 0,
            source_file=self._simulate_source_file(finding),
        )

        # Create clip
        clip = MediaClip(
            clip_id=f"CLIP_{clip_number:03d}",
            finding_id=finding.finding_id,
            title=title,
            description=finding.description,
            source_file=metadata.source_file,
            start_time=finding.timestamp,
            duration_seconds=duration,
            files=files,
            metadata=metadata,
            extracted_at=datetime.utcnow(),
        )

        return clip

    def _timestamp_to_seconds(self, timestamp: str) -> float:
        """Convert timestamp string to seconds."""
        # Handle various timestamp formats (MM:SS, HH:MM:SS, etc.)
        parts = timestamp.split(":")
        if len(parts) == 2:  # MM:SS
            minutes, seconds = map(int, parts)
            return minutes * 60 + seconds
        elif len(parts) == 3:  # HH:MM:SS
            hours, minutes, seconds = map(int, parts)
            return hours * 3600 + minutes * 60 + seconds
        else:
            # Default to 0 if parsing fails
            return 0.0

    def _generate_clip_title(self, finding: Finding) -> str:
        """Generate a descriptive title for the clip."""
        # Extract key words from description
        description = finding.description.lower()
        keywords = []

        # Look for action words
        actions = ["struggle", "confusion", "frustration", "search", "difficulty", "problem"]
        for action in actions:
            if action in description:
                keywords.append(action.title())
                break

        # Add task context
        if finding.task_id:
            keywords.append(f"Task {finding.task_id}")

        # Add participant
        if finding.participant_id:
            keywords.append(f"P{finding.participant_id}")

        if keywords:
            return " ".join(keywords)
        else:
            return f"Finding {finding.finding_id}"

    def _severity_to_label(self, severity: float) -> str:
        """Convert severity score to label."""
        if severity >= 3:
            return "critical"
        elif severity >= 2:
            return "high"
        elif severity >= 1:
            return "medium"
        else:
            return "low"

    def _determine_clip_theme(self, finding: Finding) -> str:
        """Determine thematic category for clip."""
        text = finding.description.lower()

        themes = {
            "checkout_flow": ["checkout", "payment", "purchase", "buy"],
            "navigation": ["find", "navigate", "menu", "search"],
            "error_handling": ["error", "mistake", "wrong", "failed"],
            "content_discovery": ["content", "information", "discover"],
            "user_input": ["enter", "input", "form", "field"],
        }

        for theme, keywords in themes.items():
            if any(keyword in text for keyword in keywords):
                return theme

        return "general_usability"

    def _simulate_source_file(self, finding: Finding) -> str:
        """Simulate source media file path."""
        participant = finding.participant_id or "unknown"
        return f"{participant}_session.mp4"

    def _create_playlists(self, clips: List[MediaClip]) -> Dict[str, ClipPlaylist]:
        """Create organized playlists from clips."""
        playlists = {}

        # Critical issues playlist
        critical_clips = [c.clip_id for c in clips if c.metadata.severity == "critical"]
        if critical_clips:
            playlists["critical_issues"] = ClipPlaylist(
                name="Critical Issues Highlights",
                clips=critical_clips,
                total_duration_seconds=sum(c.duration_seconds for c in clips if c.clip_id in critical_clips),
                description="Key moments showing critical usability issues requiring immediate attention",
            )

        # Design review playlist
        design_clips = [c.clip_id for c in clips if c.metadata.severity in ["critical", "high"]][:5]
        if design_clips:
            playlists["design_review"] = ClipPlaylist(
                name="Design Team Review",
                clips=design_clips,
                total_duration_seconds=sum(c.duration_seconds for c in clips if c.clip_id in design_clips),
                description="Curated clips for upcoming design review meeting",
            )

        # Thematic playlists
        themes = {}
        for clip in clips:
            theme = clip.metadata.theme
            if theme not in themes:
                themes[theme] = []
            themes[theme].append(clip.clip_id)

        for theme, theme_clips in themes.items():
            if len(theme_clips) >= 2:
                playlists[f"theme_{theme}"] = ClipPlaylist(
                    name=f"{theme.replace('_', ' ').title()} Issues",
                    clips=theme_clips,
                    total_duration_seconds=sum(c.duration_seconds for c in clips if c.clip_id in theme_clips),
                    description=f"Clips demonstrating {theme.replace('_', ' ')} usability issues",
                )

        return playlists

    def _calculate_clip_stats(self, clips: List[MediaClip]) -> Dict[str, Any]:
        """Calculate clip extraction statistics."""
        total_clips = len(clips)
        total_duration = sum(c.duration_seconds for c in clips)

        # Count by severity
        severity_counts = {}
        for clip in clips:
            severity = clip.metadata.severity
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        # Count by theme
        theme_counts = {}
        for clip in clips:
            theme = clip.metadata.theme
            theme_counts[theme] = theme_counts.get(theme, 0) + 1

        # Privacy compliance
        privacy_compliant = all(c.metadata.privacy_processed for c in clips)

        return {
            "total_clips_extracted": total_clips,
            "total_duration_minutes": round(total_duration / 60, 1),
            "by_severity": severity_counts,
            "by_theme": theme_counts,
            "compression_ratio": 0.3,  # Simulated
            "privacy_compliant": privacy_compliant,
        }
