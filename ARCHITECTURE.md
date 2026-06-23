"""
Comprehensive architecture and setup documentation for UT Analysis Pipeline.
A multi-agent Research Intelligence System for usability test analysis.
"""

# Research Intelligence System — Multi-Agent Architecture

## Overview

This system uses a **controller-orchestrated, multi-agent architecture** to transform raw usability test data into validated, defensible research findings. Each agent is a specialized, inspectable step in an assembly-line pipeline — not a single monolithic prompt.

### Design Principles

1. **Assembly-line decomposition** — Each agent has a single responsibility with clear inputs/outputs
2. **Evidence verification** — Findings are grounded in verbatim data with provenance chains
3. **Human-in-the-loop** — Review checkpoints prevent unvalidated claims from reaching reports
4. **Contradiction as signal** — Disagreements are reconciled, not averaged away
5. **Trust through transparency** — Every claim traces back to source material
6. **Critique before reporting** — An independent evidence critic challenges findings before delivery

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
│        Agent Layer                │     State Management Layer       │
│  (Domain Logic & Reasoning)       │    (Persistence & Coordination) │
├──────────────────────────────────┼──────────────────────────────────┤
│ • ut-controller (orchestrator)   │ • StateManager                   │
│ • ut-ingestor                    │ • TranscriptManager              │
│ • ut-extractor                   │ • NotesManager                   │
│ • ut-evaluator (verifier)        │ • FindingsManager                │
│ • ut-severity-rater              │ • EvaluationManager              │
│ • ut-heuristic-mapper            │ • HeuristicManager               │
│ • ut-synthesizer                 │ • SynthesisManager               │
│ • ut-critic (evidence challenger)│ • CriticManager                  │
│ • ut-reconciler (contradiction)  │ • ReconciliationManager          │
│ • ut-contradiction (detector)    │ • ContradictionsManager          │
│ • ut-reporter                    │ • ReviewCheckpointManager        │
│ • ut-clipper                     │ • ReportManager                  │
│ • ut-recommender                 │ • Data Models (Pydantic)         │
└──────────────────────────────────┴──────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────┐
│                 Human Review Checkpoint Layer                        │
│  • Pending/Approved/Rejected/Needs-Revision status tracking         │
│  • Blocks pipeline advancement until critical items reviewed        │
│  • Triggered by low confidence, weak evidence, unresolved tension   │
└─────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    Data Storage Layer (JSON Files)                   │
│  ┌────────────┬──────────────┬──────────────┬──────────────────┐   │
│  │ Transcripts│ Findings     │ Critiques    │ Reconciliations  │   │
│  │ Notes      │ Evaluations  │ Checkpoints  │ Reports          │   │
│  └────────────┴──────────────┴──────────────┴──────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

## Multi-Agent Pipeline Flow

```
1. INGESTION (ut-ingestor)
   ├─ Load transcripts (.docx/.md)
   ├─ Load observation notes
   └─ Store with provenance metadata

2. EXTRACTION (ut-extractor)
   ├─ Extract findings with verbatim quotes
   ├─ Categorize: issues, outcomes, pain points, positives, quotes
   └─ Assign provenance (transcript ID, timestamp, speaker)

3. EVALUATION (ut-evaluator — Revelation Loop, max 3 iterations)
   ├─ 5-check verification per finding:
   │  ├─ Verbatim quote match
   │  ├─ Meaning accuracy
   │  ├─ Task attribution
   │  ├─ No researcher interpretation
   │  └─ Severity justification
   └─ Failed findings → re-extraction with corrections

4. SEVERITY RATING (ut-severity-rater)
   ├─ Nielsen scale (0-4)
   └─ Justified with frequency, task impact, persistence

5. HEURISTIC MAPPING (ut-heuristic-mapper)
   ├─ Map to Nielsen's 10 or custom framework
   └─ Primary + secondary heuristic assignment

6. SYNTHESIS (ut-synthesizer)
   ├─ Cross-participant theme identification
   ├─ Pattern recognition
   └─ Prioritized insight generation

7. CONTRADICTION DETECTION (ut-contradiction)
   ├─ Participant disagreement analysis
   ├─ Temporal inconsistency detection
   └─ Cross-task contradiction identification

8. RECONCILIATION (ut-reconciler) ← NEW
   ├─ Segment participants into meaningful groups
   ├─ Generate contextual explanations (not averages)
   ├─ Produce design implications honoring both sides
   ├─ Surface research gaps and follow-up questions
   └─ Generate review checkpoints for uncertain reconciliations

9. EVIDENCE CRITIQUE (ut-critic) ← NEW
   ├─ Challenge evidence strength per insight
   ├─ Detect overgeneralizations and absolute language
   ├─ Flag claims with insufficient participant support
   ├─ Generate revision recommendations
   └─ Create review checkpoints for weak/insufficient evidence

10. HUMAN REVIEW GATE ← NEW
    ├─ Collect pending checkpoints from critic + reconciler
    ├─ Require approval before reporting phase
    └─ Track reviewer decisions with audit trail

11. REPORTING (ut-reporter)
    ├─ Audience-specific reports (design, PM, leadership)
    ├─ Include reconciliation nuances
    ├─ Reference critique findings in provenance
    └─ Full claim-to-source tracing
```

## New Agents

### ut-critic — Evidence Challenge Agent

**Purpose**: Reviews synthesis outputs and challenges whether evidence is strong enough.

**Position**: After synthesis, before reporting.

**Checks for**:
- Claims based on too few participants
- Themes that conflate different issues
- Absolute language not supported by data ("all users", "always")
- High severity from single participant
- Inconsistent severity distribution within a single insight

**Output**: `EvidenceCritique` objects with strength rating, issues, and revision recommendations.

### ut-reconciler — Contradiction Reconciliation Agent

**Purpose**: Takes contradictions and produces nuanced interpretations instead of bland averages.

**Position**: After contradiction detection, before critique.

**Strategy**:
1. Accept the tension — both sides are real
2. Explain the divergence — what contextual factors predict which group?
3. Design for both — produce recommendations serving all segments
4. Flag uncertainty — be explicit about what we don't know

**Output**: `Reconciliation` objects with participant groups, explanations, design implications, and research questions.

### Human Review Checkpoints

**Purpose**: Ensure no unvalidated claims reach final reports.

**Triggered when**:
- Evidence confidence is low
- Quotes cannot be verified
- Issue is severe but based on limited evidence
- Critic flags unsupported claims
- Contradictions remain unresolved
- Recommendation confidence is low
- Source provenance is missing
- Participant count is too small for a broad claim

**Model**: `HumanReviewCheckpoint` with status workflow: pending → approved/rejected/needs_revision

## Pipeline Phases (Updated)

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
  ↓ (evidence challenge)        ← NEW
CRITIQUE_COMPLETE
  ↓ (reconcile contradictions)  ← NEW
RECONCILIATION_COMPLETE
  ↓ (human review gate)         ← NEW (via ReviewCheckpointManager)
  ↓ (generate reports)
REPORTING_COMPLETE
```

## File Organization

```
project_dir/
├── project_state.json
│
└── data/
    ├── transcripts/          (parsed turns)
    ├── notes/                (parsed observations)
    ├── findings/             (extracted findings)
    ├── evaluations/          (5-check results)
    ├── heuristics/           (heuristic mappings)
    ├── synthesis/            (insights + reports)
    ├── contradictions/       (detected contradictions)
    ├── reconciliations/      (reconciled interpretations) ← NEW
    ├── critiques/            (evidence critiques)         ← NEW
    ├── review_checkpoints/   (human review gates)         ← NEW
    ├── recommendations/      (actionable recommendations)
    ├── clips/                (media clip metadata)
    └── reports/              (final reports)
```

## Key Data Models (New)

### EvidenceCritique
```python
critique_id: str
target_type: Literal["finding", "theme", "insight", "recommendation"]
target_id: str
critique_summary: str
evidence_strength: Literal["strong", "moderate", "weak", "insufficient"]
issues_found: list[str]
unsupported_claims: list[str]
overgeneralizations: list[str]
recommended_revision: Optional[str]
confidence_rating: float  # 0.0-1.0
requires_human_review: bool
```

### Reconciliation
```python
reconciliation_id: str
contradiction_id: str
theme_ids: list[str]
tension_description: str
participant_groups: dict[str, list[str]]
possible_explanations: list[str]
design_implication: str
changes_original_finding: bool
further_research_needed: bool
research_questions: list[str]
confidence: float  # 0.0-1.0
```

### HumanReviewCheckpoint
```python
checkpoint_id: str
stage: str
reason: str
related_artifact_id: str
artifact_type: Literal["finding", "theme", "insight", ...]
severity: Literal["critical", "high", "medium", "low"]
suggested_reviewer_action: str
status: Literal["pending", "approved", "rejected", "needs_revision"]
reviewer_notes: Optional[str]
reviewed_by: Optional[str]
reviewed_at: Optional[datetime]
```

## Quality Gates (Updated)

Before advancing phases:
1. **Ingestion** — At least 1 transcript loaded
2. **Extraction** — At least 1 finding extracted
3. **Evaluation** — All findings must pass 5-check (with revelation loop)
4. **Severity Rating** — Each finding must have justification
5. **Heuristic Mapping** — All findings must map to heuristics
6. **Synthesis** — Data from at least N-1 participants
7. **Critique** — All insights reviewed by evidence critic
8. **Reconciliation** — All contradictions reconciled or marked unresolved
9. **Human Review** — All critical/high checkpoints approved or addressed
10. **Reporting** — Critique and reconciliation must be complete

## Provenance & Trust

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

Every critique traces to its source:
```json
{
  "critique_id": "CRIT_001",
  "target_id": "I_001",
  "evidence_strength": "weak",
  "issues_found": ["insufficient_participant_count"],
  "requires_human_review": true
}
```

Reports include critic findings in their provenance chain, so stakeholders can see which claims were challenged and how they were resolved.

---

Full architecture designed for extensibility, auditability, research rigor, and integration with GitHub Copilot CLI for intelligent reasoning at every step.
