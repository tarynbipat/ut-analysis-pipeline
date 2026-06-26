"""
Data models for usability test analysis pipeline - moved from models.py for better organization.
"""

from typing import Any, Literal, Optional
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field


class TaskOutcomeType(str, Enum):
    """Task completion outcome types."""

    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"
    SKIPPED = "skipped"
    NEEDED_HELP = "needed_help"


class FindingCategory(str, Enum):
    """Finding categories."""

    USABILITY_ISSUE = "usability_issue"
    TASK_OUTCOME = "task_outcome"
    PAIN_POINT = "pain_point"
    POSITIVE_MOMENT = "positive_moment"
    PARTICIPANT_QUOTE = "participant_quote"


class SeverityLevel(int, Enum):
    """Nielsen's severity scale (0-4)."""

    COSMETIC = 0
    MINOR = 1
    MAJOR = 2
    CRITICAL = 3
    CATASTROPHIC = 4


class EvaluationCheckType(str, Enum):
    """5-check verification types."""

    VERBATIM_MATCH = "verbatim_match"
    MEANING_ACCURACY = "meaning_accuracy"
    TASK_ATTRIBUTION = "task_attribution"
    NO_INTERPRETATION = "no_interpretation"
    JUSTIFIED_SEVERITY = "justified_severity"


class TranscriptTurn(BaseModel):
    """Single turn in a transcript."""

    turn_id: str
    speaker: str
    participant_id: Optional[str] = None
    timestamp: str  # ISO format or MM:SS
    utterance: str
    task_id: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Transcript(BaseModel):
    """Complete transcript with parsed turns."""

    transcript_id: str
    session_date: datetime
    participant_id: str
    duration_seconds: Optional[int] = None
    turns: list[TranscriptTurn]
    source_file: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class ObservationNote(BaseModel):
    """Timestamped researcher observation."""

    note_id: str
    participant_id: str
    timestamp: str
    observation: str
    task_id: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Finding(BaseModel):
    """Extracted usability finding with provenance."""

    finding_id: str
    category: FindingCategory
    title: str
    description: str
    verbatim_quote: str  # Exact text from transcript/notes
    speaker: str
    timestamp: str
    source_transcript_id: str
    task_id: Optional[str] = None
    participant_id: str
    confidence: float = Field(ge=0.0, le=1.0)
    severity: Optional[SeverityLevel] = None
    heuristics: list[str] = Field(default_factory=list)
    extracted_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvaluationResult(BaseModel):
    """Evaluation check result."""

    check_type: EvaluationCheckType
    passed: bool
    feedback: str
    severity: int = 0  # 0-2, where 2 is critical failure


class EvaluatedFinding(BaseModel):
    """Finding after evaluation."""

    finding_id: str
    original_finding: Finding
    evaluation_results: list[EvaluationResult]
    all_passed: bool
    failed_checks: list[EvaluationCheckType] = Field(default_factory=list)
    correction_instructions: Optional[str] = None
    revision_count: int = 0
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)


class SeverityRating(BaseModel):
    """Severity rating with justification."""

    finding_id: str
    severity: SeverityLevel
    justification: str
    frequency_count: int
    affected_participants: list[str]
    impact_on_tasks: list[tuple[str, float]]  # (task_id, impact_score)
    rated_at: datetime = Field(default_factory=datetime.utcnow)


class HeuristicMapping(BaseModel):
    """Heuristic classification for a finding."""

    finding_id: str
    heuristics: list[str]  # Nielsen's 10 heuristics or custom framework
    primary_heuristic: str
    mapping_confidence: float = Field(ge=0.0, le=1.0)
    mapped_at: datetime = Field(default_factory=datetime.utcnow)


class TaskOutcome(BaseModel):
    """Task completion status per participant."""

    task_id: str
    participant_id: str
    outcome: TaskOutcomeType
    time_to_completion: Optional[int] = None  # seconds
    attempts: int = 1
    help_requested: bool = False
    notes: Optional[str] = None


class TaskMatrix(BaseModel):
    """Task completion matrix (participants × tasks × outcome)."""

    outcomes: list[TaskOutcome]
    summary: dict[str, dict[str, int]]  # {task_id: {outcome: count}}


class Theme(BaseModel):
    """Cross-participant theme."""

    theme_id: str
    title: str
    description: str
    finding_ids: list[str]
    participant_count: int
    affected_participants: list[str]
    frequency: int
    primary_heuristic: Optional[str] = None
    severity_distribution: dict[str, int] = Field(default_factory=dict)


class SynthesisReport(BaseModel):
    """Synthesized findings across participants."""

    synthesis_id: str
    project_id: str
    themes_by_task: dict[str, list[Theme]]
    themes_by_severity: dict[str, list[Theme]]
    themes_by_heuristic: dict[str, list[Theme]]
    task_matrix: TaskMatrix
    high_failure_tasks: list[tuple[str, float]]  # (task_id, failure_rate)
    most_violated_heuristics: list[tuple[str, int]]  # (heuristic, violation_count)
    total_participants: int
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ReportType(str, Enum):
    """Report audience types."""

    DESIGN = "design"
    PM = "pm"
    LEADERSHIP = "leadership"


class Report(BaseModel):
    """Generated report for specific audience."""

    report_id: str
    report_type: ReportType
    project_id: str
    title: str
    executive_summary: str
    content: str  # Full report body
    top_issues: list[dict[str, Any]]
    task_success_rates: dict[str, float]
    recommendations: list[str]
    provenance_claims: list[dict[str, Any]]  # Links to sources
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class ProjectConfig(BaseModel):
    """Research project configuration."""

    project_id: str
    project_name: str
    description: str
    participants: list[dict[str, Any]]  # Participant metadata
    tasks: list[dict[str, Any]]  # Task definitions with success criteria
    heuristic_framework: str = "nielsen_10"  # Default or custom
    custom_heuristics: Optional[list[str]] = None
    research_date: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


class PipelineStatus(BaseModel):
    """Current pipeline execution status."""

    project_id: str
    phase: Literal[
        "initialized",
        "ingestion_complete",
        "extraction_complete",
        "evaluation_complete",
        "severity_rating_complete",
        "heuristic_mapping_complete",
        "synthesis_complete",
        "critique_complete",
        "reconciliation_complete",
        "reporting_complete",
        "clipping_complete",
        "recommendations_complete",
        "contradictions_complete",
    ]
    progress_percent: int
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    completed_tasks: dict[str, Any] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)


class MediaClip(BaseModel):
    """Extracted media clip metadata."""

    clip_id: str
    finding_id: str
    title: str
    description: str
    source_file: str
    start_time: str
    duration_seconds: int
    files: dict[str, str]  # {format: filepath}
    metadata: dict[str, Any] = Field(default_factory=dict)
    extracted_at: datetime = Field(default_factory=datetime.utcnow)


class ClipMetadata(BaseModel):
    """Additional metadata for media clips."""

    participant_id: str
    task_id: Optional[str] = None
    theme: str
    severity: str
    privacy_processed: bool = False


class ClipPlaylist(BaseModel):
    """Organized playlist of clips."""

    name: str
    clips: list[str]  # Clip IDs
    total_duration_seconds: int
    description: str


class RecommendationSolution(BaseModel):
    """Specific solution approach for a recommendation."""

    approach: str
    description: str
    implementation: dict[str, Any]  # Technical implementation details
    effort_estimate: str
    impact_estimate: str


class ImplementationDetail(BaseModel):
    """Technical implementation details."""

    frontend: Optional[str] = None
    backend: Optional[str] = None
    design: Optional[str] = None
    content: Optional[str] = None
    testing: Optional[str] = None


class Recommendation(BaseModel):
    """Actionable recommendation from findings."""

    recommendation_id: str
    finding_id: str
    title: str
    description: str
    priority: str
    impact_score: float
    effort_score: float
    rationale: str
    solutions: list[RecommendationSolution]
    success_metrics: list[str]
    target_audience: str
    timeline: str
    dependencies: list[str]
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class Contradiction(BaseModel):
    """Identified contradiction or inconsistency."""

    contradiction_id: str
    type: str
    severity: str
    description: str
    affected_findings: list[str]
    evidence: dict[str, Any]
    analysis: dict[str, Any]
    resolution_suggestions: list[dict[str, Any]]
    detected_at: datetime = Field(default_factory=datetime.utcnow)


class ConsistencyAnalysis(BaseModel):
    """Consistency analysis results."""

    participant_consistency: dict[str, float]
    task_consistency: dict[str, float]
    finding_type_consistency: dict[str, float]


class DataQualityAssessment(BaseModel):
    """Overall data quality assessment."""

    overall_reliability: float
    inter_rater_agreement: float
    temporal_stability: float
    cross_source_consistency: float
    recommendations: list[str]


class ReportSection(BaseModel):
    """Section of a generated report."""

    heading: str
    content: str
    key_metrics: Optional[dict[str, Any]] = None
    insights: Optional[list[dict[str, Any]]] = None


class ReportMetadata(BaseModel):
    """Metadata for generated reports."""

    report_batch_id: str
    report_types: list[str]
    output_formats: list[str]
    insights_covered: int
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# --- Synthesis sub-models (used by ut-synthesizer) ---


class SynthesisEvidence(BaseModel):
    """Evidence backing a synthesis insight."""

    finding_ids: list[str]
    participant_count: int
    task_count: int
    severity_distribution: dict[int, int] = Field(default_factory=dict)


class SynthesisPattern(BaseModel):
    """Patterns identified in a synthesis insight."""

    cross_participant: str
    cross_task: str
    workflow_impact: str


class SynthesisRecommendation(BaseModel):
    """Recommendation produced during synthesis."""

    priority: str
    description: str
    expected_impact: str
    implementation_effort: str
    business_value: str


class SynthesisInsight(BaseModel):
    """A single insight produced by the synthesizer."""

    insight_id: str
    title: str
    theme: str
    severity: str
    description: str
    evidence: SynthesisEvidence
    patterns: SynthesisPattern
    recommendations: list[SynthesisRecommendation] = Field(default_factory=list)
    synthesized_at: datetime = Field(default_factory=datetime.utcnow)


# --- Evidence Critic models (ut-critic agent) ---


class EvidenceCritique(BaseModel):
    """Structured critique of a finding, theme, or recommendation."""

    critique_id: str
    target_type: Literal["finding", "theme", "insight", "recommendation"]
    target_id: str
    critique_summary: str
    evidence_strength: Literal["strong", "moderate", "weak", "insufficient"]
    issues_found: list[str] = Field(default_factory=list)
    unsupported_claims: list[str] = Field(default_factory=list)
    overgeneralizations: list[str] = Field(default_factory=list)
    missing_participant_segments: list[str] = Field(default_factory=list)
    recommended_revision: Optional[str] = None
    confidence_rating: float = Field(ge=0.0, le=1.0)
    requires_human_review: bool = False
    review_reason: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CriticReport(BaseModel):
    """Aggregated output from the evidence critic agent."""

    critic_batch_id: str
    source_synthesis_id: str
    critiques: list[EvidenceCritique]
    summary: dict[str, Any] = Field(default_factory=dict)
    overall_evidence_quality: Literal["high", "acceptable", "concerning", "inadequate"]
    human_review_required: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)


# --- Reconciliation models (ut-reconciler agent) ---


class Reconciliation(BaseModel):
    """Reconciliation of a contradiction into a nuanced interpretation."""

    reconciliation_id: str
    contradiction_id: str
    theme_ids: list[str] = Field(default_factory=list)
    tension_description: str
    participant_groups: dict[str, list[str]] = Field(default_factory=dict)
    possible_explanations: list[str] = Field(default_factory=list)
    design_implication: str
    changes_original_finding: bool = False
    further_research_needed: bool = False
    research_questions: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ReconciliationReport(BaseModel):
    """Aggregated output from the reconciler agent."""

    reconciliation_batch_id: str
    source_contradictions_id: str
    reconciliations: list[Reconciliation]
    unresolved_tensions: list[str] = Field(default_factory=list)
    research_gaps: list[str] = Field(default_factory=list)
    summary: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


# --- Human-in-the-Loop Review Checkpoint ---


class HumanReviewCheckpoint(BaseModel):
    """A checkpoint requiring human review before proceeding."""

    checkpoint_id: str
    stage: str
    reason: str
    related_artifact_id: str
    artifact_type: Literal[
        "finding", "theme", "insight", "recommendation",
        "critique", "reconciliation", "contradiction"
    ]
    severity: Literal["critical", "high", "medium", "low"]
    suggested_reviewer_action: str
    status: Literal["pending", "approved", "rejected", "needs_revision"] = "pending"
    reviewer_notes: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ReviewGate(BaseModel):
    """A review gate aggregating checkpoints before a pipeline phase can advance."""

    gate_id: str
    stage: str
    checkpoints: list[HumanReviewCheckpoint]
    all_approved: bool = False
    blocking_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)


# --- Theme Orchestration models ---


class ThemeLaneHandoffItem(BaseModel):
    """Single finding handoff item for a thematic analysis lane."""

    finding_id: str
    participant_id: str
    task_id: Optional[str] = None
    rationale: str


class ThematicLane(BaseModel):
    """A single thematic lane for parallel specialist analysis."""

    lane_id: str
    lane_name: str
    assigned_agent: str
    finding_ids: list[str]
    participant_ids: list[str] = Field(default_factory=list)
    task_ids: list[str] = Field(default_factory=list)
    rationale: str
    expected_output_path: str = ""
    handoff_items: list[ThemeLaneHandoffItem] = Field(default_factory=list)


class ThemeOrchestrationPlan(BaseModel):
    """Orchestration plan routing findings to parallel thematic lanes."""

    plan_id: str
    findings_batch_id: str
    project_id: str
    run_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    source_artifacts: list[str] = Field(default_factory=list)
    thematic_lanes: list[ThematicLane] = Field(default_factory=list)
    total_findings: int = 0


# --- Thematic Specialist output models ---


class ThemeResult(BaseModel):
    """A single theme identified by a specialist agent."""

    theme_id: str
    theme_title: str
    theme_summary: str
    evidence_count: int
    participant_count: int
    task_coverage: list[str] = Field(default_factory=list)
    representative_quotes: list[str] = Field(default_factory=list)
    contradictions_or_outliers: list[str] = Field(default_factory=list)
    product_implication: str = ""
    confidence: float = Field(ge=0.0, le=1.0)
    limitations: list[str] = Field(default_factory=list)


class ThematicLaneAnalysis(BaseModel):
    """Output from a thematic specialist agent."""

    lane_id: str
    lane_name: str
    agent_name: str
    source_finding_ids: list[str]
    themes: list[ThemeResult] = Field(default_factory=list)
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)


# --- Theme Consolidation models ---


class ConsolidatedTheme(BaseModel):
    """A theme produced by merging results across specialist lanes."""

    consolidated_theme_id: str
    title: str
    summary: str
    contributing_lanes: list[str] = Field(default_factory=list)
    source_theme_ids: list[str] = Field(default_factory=list)
    evidence_strength: Literal["strong", "moderate", "weak", "insufficient"] = "moderate"
    participant_count: int = 0
    key_quotes: list[str] = Field(default_factory=list)
    tensions_or_contradictions: list[str] = Field(default_factory=list)
    product_implications: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)
    open_questions: list[str] = Field(default_factory=list)


class ThemeConsolidation(BaseModel):
    """Full consolidation output merging parallel thematic analyses."""

    consolidation_id: str
    project_id: str
    consolidated_themes: list[ConsolidatedTheme] = Field(default_factory=list)
    cross_lane_relationships: list[dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


# --- Contradiction Reconciliation (enhanced) ---


class EnhancedContradictionReconciliation(BaseModel):
    """Nuanced contradiction reconciliation treating tensions as research signal."""

    reconciliation_id: str
    contradiction_id: str
    tension_description: str
    participant_groups: dict[str, list[str]] = Field(default_factory=dict)
    possible_explanations: list[str] = Field(default_factory=list)
    explanation_factors: list[
        Literal[
            "segment",
            "experience_level",
            "task_context",
            "product_expectation",
            "evidence_limits",
            "other",
        ]
    ] = Field(default_factory=list)
    reconciled_interpretation: str
    design_implications: list[str] = Field(default_factory=list)
    further_research_needed: bool = False
    research_questions: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)
    created_at: datetime = Field(default_factory=datetime.utcnow)


# --- Evaluation Rubric models ---


class RubricScore(BaseModel):
    """Score for a single rubric dimension."""

    dimension: str
    score: float = Field(ge=0.0, le=1.0)
    rationale: str = ""
    passed: bool = True


class EvalResult(BaseModel):
    """Evaluation result for a single artifact."""

    artifact_id: str
    artifact_type: str
    evaluator: str
    scores: list[RubricScore] = Field(default_factory=list)
    pass_fail: Literal["pass", "fail", "warning"] = "pass"
    issues: list[str] = Field(default_factory=list)
    recommended_fixes: list[str] = Field(default_factory=list)
    created_human_review_checkpoint: bool = False
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)


class EvalSummary(BaseModel):
    """Summary of all evaluation results for a pipeline run."""

    run_id: str
    total_artifacts_evaluated: int = 0
    passed: int = 0
    failed: int = 0
    warnings: int = 0
    eval_results: list[EvalResult] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


# --- Research Gap models ---


class ResearchGap(BaseModel):
    """An identified gap in the research evidence."""

    gap_id: str
    gap_title: str
    why_it_matters: str
    related_theme_ids: list[str] = Field(default_factory=list)
    evidence_limitation: str = ""
    recommended_follow_up: str = ""
    priority: Literal["high", "medium", "low"] = "medium"
    suggested_method: str = ""
    suggested_participant_segment: str = ""
    decision_it_would_inform: str = ""


class ResearchGapReport(BaseModel):
    """Full research gap analysis output."""

    project_id: str
    run_id: str
    gaps: list[ResearchGap] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


# --- Next Study Planner models ---


class NextStudyPlan(BaseModel):
    """Recommended next study based on research gaps."""

    plan_id: str
    study_objective: str
    method_recommendation: str
    target_participant_profile: str = ""
    key_research_questions: list[str] = Field(default_factory=list)
    suggested_tasks_or_topics: list[str] = Field(default_factory=list)
    decision_it_would_inform: str = ""
    why_this_method: str = ""
    risks_and_limitations: list[str] = Field(default_factory=list)
    priority: Literal["high", "medium", "low"] = "medium"


class NextStudyPlanReport(BaseModel):
    """Full next-study planning output."""

    project_id: str
    run_id: str
    plans: list[NextStudyPlan] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


# --- Pipeline Run Summary (observability) ---


class PipelineRunSummary(BaseModel):
    """Observable summary of a complete pipeline run."""

    run_id: str
    project_id: str
    stages_completed: list[str] = Field(default_factory=list)
    artifacts_created: list[str] = Field(default_factory=list)
    agents_invoked: list[str] = Field(default_factory=list)
    evals_passed: int = 0
    evals_failed: int = 0
    review_checkpoints_created: int = 0
    unresolved_issues: list[str] = Field(default_factory=list)
    next_suggested_action: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
