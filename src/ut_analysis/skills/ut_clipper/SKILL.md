# ut-clipper Skill

## Purpose

The **ut-clipper** skill extracts relevant video/audio clips from usability test recordings based on finding timestamps. It creates short, focused clips that demonstrate key usability issues, user behaviors, and successful interactions for design reviews and stakeholder presentations.

## Key Responsibilities

1. **Clip Extraction**
   - Identify timestamp ranges from findings
   - Extract video/audio segments around key moments
   - Add buffer time before/after for context
   - Maintain audio/video synchronization

2. **Clip Organization**
   - Group clips by finding severity and theme
   - Create playlists for different audiences
   - Generate clip metadata and descriptions
   - Link clips back to source findings

3. **Quality Optimization**
   - Compress clips for web sharing
   - Add text overlays with finding summaries
   - Include participant IDs and timestamps
   - Ensure clips are appropriately sized

4. **Presentation Support**
   - Generate highlight reels for meetings
   - Create before/after comparison clips
   - Support multiple output formats
   - Enable easy clip sharing and embedding

5. **Privacy Protection**
   - Remove sensitive information from clips
   - Blur faces if requested
   - Respect participant consent settings
   - Comply with data protection requirements

## Input Format

```json
{
  "command": "extract_clips",
  "findings_batch_id": "batch_001",
  "clip_batch_id": "clips_001",
  "clip_config": {
    "source_media_dir": "/path/to/recordings",
    "output_dir": "/path/to/clips",
    "clip_duration_seconds": 30,
    "buffer_seconds": 5,
    "include_audio": true,
    "compression_quality": "medium",
    "privacy_filters": ["face_blur"],
    "output_formats": ["mp4", "webm"]
  }
}
```

## Output Format

```json
{
  "clip_batch_id": "clips_001",
  "clips": [
    {
      "clip_id": "CLIP_001",
      "finding_id": "F_001",
      "title": "Checkout Discount Code Confusion",
      "description": "Participant struggles to find discount code field",
      "source_file": "P001_session1.mp4",
      "start_time": "07:40",
      "duration_seconds": 30,
      "severity": "critical",
      "files": {
        "mp4": "/clips/CLIP_001_critical_checkout_discount.mp4",
        "webm": "/clips/CLIP_001_critical_checkout_discount.webm"
      },
      "metadata": {
        "participant_id": "P001",
        "task_id": "TASK-003",
        "theme": "checkout_flow",
        "privacy_processed": true
      },
      "extracted_at": "2026-05-08T14:30:00Z"
    }
  ],
  "playlists": {
    "critical_issues": {
      "name": "Critical Issues Highlights",
      "clips": ["CLIP_001", "CLIP_003", "CLIP_007"],
      "total_duration": "02:30",
      "description": "Key moments showing critical usability issues"
    },
    "design_review": {
      "name": "Design Team Review",
      "clips": ["CLIP_002", "CLIP_004", "CLIP_005"],
      "total_duration": "03:15",
      "description": "Clips for upcoming design review meeting"
    }
  },
  "clip_stats": {
    "total_clips_extracted": 12,
    "total_duration_minutes": 8.5,
    "by_severity": {"critical": 3, "high": 4, "medium": 3, "low": 2},
    "by_theme": {"checkout_flow": 5, "navigation": 3, "error_handling": 4},
    "compression_ratio": 0.3,
    "privacy_compliant": true
  }
}
```

## Clip Extraction Process

### Step 1: Finding Analysis
- Review finding timestamps and descriptions
- Identify key moments requiring visual demonstration
- Prioritize clips by severity and impact
- Group related findings for sequential clips

### Step 2: Time Range Calculation
- Use finding timestamp as center point
- Add buffer time before/after (default 5 seconds)
- Ensure total duration is appropriate (15-60 seconds)
- Handle overlapping clips efficiently

### Step 3: Media Processing
- Extract video/audio segments using FFmpeg
- Apply compression and format conversion
- Add text overlays with finding information
- Apply privacy filters (face blurring, etc.)

### Step 4: Organization and Metadata
- Generate descriptive filenames
- Create comprehensive metadata
- Link to source findings and transcripts
- Organize into logical playlists

## Clip Types

### Issue Demonstration Clips
**Purpose**: Show specific usability problems
**Content**:
- User struggling with interface
- Error occurrences and recovery attempts
- Confusion and frustration moments
- Workarounds and adaptations

### Success Clips
**Purpose**: Demonstrate effective interactions
**Content**:
- Smooth task completion
- Intuitive interface usage
- Positive user feedback moments
- Efficient workflow execution

### Comparison Clips
**Purpose**: Show before/after or alternative approaches
**Content**:
- Side-by-side interface comparisons
- Different user approaches to same task
- Success vs failure examples
- Best practice demonstrations

### Highlight Reel Clips
**Purpose**: Condensed overview for stakeholders
**Content**:
- Key moments from multiple findings
- Thematic groupings
- Severity progression
- Overall study highlights

## Output Formats

### MP4 Format
**Advantages**: Widely compatible, good compression
**Use Cases**: Local playback, email sharing, presentations
**Settings**: H.264 video, AAC audio, optimized bitrate

### WebM Format
**Advantages**: Web-native, smaller file sizes
**Use Cases**: Web embedding, online sharing, streaming
**Settings**: VP9 video, Opus audio, web optimization

### Audio-Only Format
**Advantages**: Smaller files, privacy-friendly
**Use Cases**: Transcription verification, audio analysis
**Settings**: AAC/MP3 format, normalized levels

## Privacy and Ethics

### Consent Verification
- Check participant consent for video usage
- Respect opt-out preferences
- Obtain additional permissions for public sharing

### Content Filtering
- Automatic face blurring for privacy
- Remove sensitive information overlays
- Audio filtering for background noise
- Content warnings for distressing material

### Data Protection
- Secure storage of original recordings
- Encrypted processing of sensitive content
- Audit trails for clip access and sharing
- Compliance with data protection regulations

## Integration Points

- **MCP Tools**: `load_findings`, `extract_media_clips`, `save_clips`
- **State Management**: Persists clip metadata in `data/clips/`
- **External Tools**: FFmpeg for media processing, OpenCV for privacy filters
- **File System**: Organized clip storage with metadata
- **Presentation Tools**: Integration with video players and sharing platforms

## Quality Metrics

- Clip relevance: % clips that clearly demonstrate findings
- Technical quality: Video/audio clarity and synchronization
- Compression efficiency: File size vs quality balance
- Privacy compliance: % clips meeting privacy requirements
- Usage tracking: Clip access and sharing metrics

## Example Usage

```python
from ut_analysis.skills.clipper import ClipperSkill

clipper = ClipperSkill()

# Extract clips from findings
result = clipper.extract_clips(
    findings_batch_id="batch_001",
    clip_batch_id="clips_001",
    clip_config={
        "source_media_dir": "/recordings",
        "output_dir": "/clips",
        "clip_duration_seconds": 30,
        "buffer_seconds": 5,
        "output_formats": ["mp4", "webm"],
        "privacy_filters": ["face_blur"]
    }
)

# Check extracted clips
clips = result["clips"]
critical_clips = [c for c in clips if c["severity"] == "critical"]

print(f"Extracted {len(clips)} clips, {len(critical_clips)} critical")
```

## Validation Rules

- All clips must link to valid findings
- Timestamps must exist in source media
- Privacy filters applied when required
- Output files must be playable and accessible
- Metadata must be complete and accurate

## Error Handling

**Missing Media Files:**
- Skip clips for unavailable recordings
- Log missing files for manual processing
- Continue with available media

**Processing Failures:**
- Fallback to audio-only extraction
- Reduce quality settings if compression fails
- Provide alternative clip formats

**Privacy Issues:**
- Block clip extraction if consent missing
- Apply maximum privacy filters
- Flag clips requiring manual review

## Performance Considerations

- Batch processing: Extract multiple clips in parallel
- Hardware acceleration: Use GPU for video processing
- Incremental extraction: Add clips without reprocessing
- Storage optimization: Compress and deduplicate clips
- Memory management: Process large videos in chunks
