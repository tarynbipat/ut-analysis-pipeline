# UT Analysis Pipeline

**A multi-agent research intelligence system for usability research.**

UT Analysis Pipeline helps researchers move from raw transcripts and notes to evidence-grounded findings, thematic synthesis, contradiction-aware interpretation, research gaps, next-study planning, and stakeholder-ready reporting.

## How This Differs From a Transcript Summarizer

This system is **not** a transcript summarizer. It supports the full research sensemaking workflow:

- **Thematic analysis** across multiple specialist agents working in parallel
- **Contradiction reconciliation** that treats tensions as research signal, not errors
- **Research gap identification** that says what we still don't know
- **Next-study planning** that turns gaps into actionable follow-up research
- **Evaluation rubrics** that catch overclaiming, weak evidence, and missing provenance
- **Human review checkpoints** that prevent unvalidated claims from reaching stakeholders
- **Observable intermediate artifacts** that make the pipeline inspectable at every step

## Agentic Patterns Demonstrated

| Pattern | Implementation |
|---------|---------------|
| Sequential pipeline decomposition | Controller advances through phases with prerequisites |
| Parallel thematic specialist agents | 6 specialists analyze lanes concurrently |
| Controller/orchestrator pattern | Theme orchestrator routes findings to lanes |
| Structured JSON handoffs | Every agent produces typed JSON + markdown |
| Evaluation/rubric checks | 9-dimension quality rubric with pass/fail |
| Human-in-the-loop review checkpoints | Auto-triggered when confidence or evidence is low |
| Contradiction reconciliation | Tensions preserved as signal, not averaged away |
| Research gap detection | Identifies unanswered questions from evidence limits |
| Next-study planning | Converts gaps into practical research recommendations |
| Observable intermediate artifacts | Run summary shows all stages, agents, and artifacts |

## Architecture

```
src/
├── skills/                    # Domain logic agents
│   ├── ut_controller/         # Pipeline orchestration
│   ├── ut_ingestor/           # Transcript/notes parsing
│   ├── ut_extractor/          # Finding extraction
│   ├── ut_evaluator/          # 5-check verification
│   ├── ut_severity_rater/     # Nielsen severity scale
│   ├── ut_heuristic_mapper/   # Heuristic classification
│   ├── ut_synthesizer/        # Cross-participant synthesis
│   ├── ut_contradiction/      # Contradiction detection
│   ├── ut_reconciler/         # Basic reconciliation
│   ├── ut_critic/             # Evidence challenger
│   ├── ut_theme_orchestrator/ # Routes findings → parallel lanes
│   ├── ut_pain_point_analyst/ # Pain point specialist
│   ├── ut_needs_analyst/      # User needs specialist
│   ├── ut_behavior_analyst/   # Behavioral patterns specialist
│   ├── ut_mental_model_analyst/ # Mental model specialist
│   ├── ut_trust_analyst/      # Trust/confidence specialist
│   ├── ut_workflow_analyst/   # Workflow breakdown specialist
│   ├── ut_theme_consolidator/ # Merges parallel lane outputs
│   ├── ut_contradiction_reconciler/ # Enhanced reconciliation
│   ├── ut_eval_rubric/        # Quality evaluation rubric
│   ├── ut_research_gap_finder/ # Research gap identification
│   ├── ut_next_study_planner/ # Follow-up study planning
│   ├── ut_run_summary/        # Pipeline observability
│   ├── ut_reporter/           # Audience-tailored reports
│   ├── ut_recommender/        # Design recommendations
│   └── ut_clipper/            # Video clip annotation
├── ut_analysis/
│   ├── models/                # Pydantic data models
│   ├── cli.py                 # Click CLI interface
│   ├── mcp_server.py          # MCP server
│   └── state_management.py    # JSON persistence managers
└── mcp_tools/                 # MCP server tools
```

## Quick Start

### Installation

```bash
git clone <repo>
cd ut-analysis-pipeline
uv sync
```

### Show-and-Tell Walkthrough

```bash
# 1. Initialize project
uv run ut-analysis init-project --config research_config.yaml --project-dir ./project_data

# 2. Ingest transcript
uv run ut-analysis ingest-transcript --file sample_transcript.md --transcript-id T_001 --participant-id P001 --project-dir ./project_data

# 3. Extract findings
uv run ut-analysis extract --project-dir ./project_data

# 4. Evaluate findings (5-check verification)
uv run ut-analysis evaluate --project-dir ./project_data

# 5. Run thematic orchestration
uv run ut-analysis orchestrate-themes --project-dir ./project_data --run-id run_001

# 6. Run parallel theme specialist agents
uv run ut-analysis run-theme-agents --project-dir ./project_data --run-id run_001

# 7. Consolidate themes across lanes
uv run ut-analysis consolidate-themes --project-dir ./project_data --run-id run_001

# 8. Run evaluation rubrics
uv run ut-analysis run-evals --project-dir ./project_data --run-id run_001

# 9. Find research gaps
uv run ut-analysis find-research-gaps --project-dir ./project_data --run-id run_001

# 10. Plan next study
uv run ut-analysis plan-next-study --project-dir ./project_data --run-id run_001

# 11. List review checkpoints
uv run ut-analysis list-review-checkpoints --project-dir ./project_data

# 12. Generate pipeline run summary
uv run ut-analysis run-summary --project-dir ./project_data --run-id run_001
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `init-project` | Initialize from research config |
| `ingest-transcript` | Parse and store transcript |
| `ingest-notes` | Parse observation notes |
| `extract` | Extract findings from transcripts |
| `evaluate` | 5-check verification of findings |
| `status` | Show pipeline status |
| `orchestrate-themes` | Route findings to thematic lanes |
| `run-theme-agents` | Run parallel specialist analysis |
| `consolidate-themes` | Merge themes across lanes |
| `run-evals` | Quality rubric evaluation |
| `find-research-gaps` | Identify unanswered questions |
| `plan-next-study` | Generate follow-up research plans |
| `list-review-checkpoints` | Show pending human reviews |
| `run-summary` | Generate observable run summary |

## Skills (Agents)

1. **ut-controller** — Pipeline orchestration and phase management
2. **ut-ingestor** — Multi-source transcript/notes parsing
3. **ut-extractor** — Structured finding extraction with provenance
4. **ut-evaluator** — 5-check verification with revelation loops
5. **ut-severity-rater** — Nielsen severity scale rating
6. **ut-heuristic-mapper** — Heuristic classification
7. **ut-synthesizer** — Cross-participant theme synthesis
8. **ut-contradiction** — Contradiction detection
9. **ut-reconciler** — Basic contradiction reconciliation
10. **ut-critic** — Evidence strength challenger
11. **ut-theme-orchestrator** — Routes findings to parallel thematic lanes
12. **ut-pain-point-analyst** — Pain point and frustration analysis
13. **ut-needs-analyst** — User needs and expectations analysis
14. **ut-behavior-analyst** — Behavioral pattern identification
15. **ut-mental-model-analyst** — Mental model and conceptual gap analysis
16. **ut-trust-analyst** — Trust and confidence signal analysis
17. **ut-workflow-analyst** — Workflow breakdown analysis
18. **ut-theme-consolidator** — Cross-lane theme merging
19. **ut-contradiction-reconciler** — Enhanced nuanced reconciliation
20. **ut-eval-rubric** — 9-dimension quality evaluation
21. **ut-research-gap-finder** — Research gap identification
22. **ut-next-study-planner** — Follow-up study planning
23. **ut-run-summary** — Pipeline observability
24. **ut-reporter** — Audience-tailored report generation
25. **ut-recommender** — Design recommendation generation
26. **ut-clipper** — Video clip annotation

## Development

```bash
# Run tests
uv run pytest

# Run linting
uv run ruff check src/

# Format code
uv run black src/
```

## Configuration

See `research_config.yaml` for task definitions, participant metadata, heuristic frameworks, and report preferences.

---

# 📽️ Class Presentation: Agentic AI for Research — Show-and-Tell

## The Problem This Repo Solves

### The researcher's dilemma

A UX researcher finishes a usability study with 5 participants. They have hours of transcripts, dozens of observations, and a week before stakeholders want a report. The actual work isn't *transcription* — it's **sensemaking**:

- Which findings are real vs. artifacts of a single confused participant?
- Are two pain points actually the same theme, or do they need separate design responses?
- When participants disagreed, what explains the disagreement?
- What did we *not* learn that we needed to?
- What should we study next?

**Current tools solve the wrong layer.** AI transcript summarizers give you a bullet list. But a bullet list isn't research. Research is interpretation, triangulation, evidence-weighting, gap awareness, and recommendation — with explicit confidence about what you know and don't know.

### What this system does instead

UT Analysis Pipeline is a **multi-agent research intelligence system** that decomposes the full sensemaking workflow into observable, auditable steps:

```
Raw Data → Structured Findings → Verified Findings → Themed Analysis →
Cross-Lane Consolidation → Contradiction Reconciliation → Quality Evaluation →
Research Gaps → Next-Study Plans → Stakeholder Report
```

Each step is handled by a specialist agent. Each handoff is a structured JSON artifact. Each output is inspectable. The human researcher stays in control at review checkpoints rather than blindly trusting a black-box summary.

---

## End-to-End Architecture

### System layers

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           HUMAN RESEARCHER                                   │
│  • Configures study, reviews checkpoints, approves/rejects, shares report   │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                        CLI / MCP Interface Layer                              │
│  14 commands │ MCP server with 19+ tools │ GitHub Copilot skills             │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                         AGENT ORCHESTRATION LAYER                             │
│                                                                              │
│  ┌─────────────┐    ┌──────────────────┐    ┌────────────────────────────┐  │
│  │ ut-controller│───▶│ Sequential Phase │───▶│ ut-theme-orchestrator      │  │
│  │ (pipeline    │    │ Management       │    │ (parallel fan-out)         │  │
│  │  governor)   │    └──────────────────┘    └────────────────────────────┘  │
│  └─────────────┘                                                             │
│                                                                              │
│  Phase Flow:                                                                 │
│  init → ingest → extract → evaluate → severity → heuristic → synthesize     │
│    → orchestrate → [parallel specialists] → consolidate → reconcile          │
│    → eval-rubric → gaps → next-study → report → run-summary                 │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                         SPECIALIST AGENT LAYER                                │
│                                                                              │
│  Sequential agents:                                                          │
│  ┌────────────┬────────────┬────────────┬──────────────┬──────────────┐     │
│  │ Ingestor   │ Extractor  │ Evaluator  │ Severity     │ Heuristic    │     │
│  │            │            │ (5-check)  │ Rater        │ Mapper       │     │
│  └────────────┴────────────┴────────────┴──────────────┴──────────────┘     │
│                                                                              │
│  Parallel thematic specialists (fan-out from orchestrator):                  │
│  ┌──────────────┬──────────────┬──────────────┐                             │
│  │ Pain Points  │ User Needs   │ Behaviors    │                             │
│  ├──────────────┼──────────────┼──────────────┤                             │
│  │ Mental Models│ Trust/Confid.│ Workflow     │                             │
│  └──────────────┴──────────────┴──────────────┘                             │
│                                                                              │
│  Post-analysis agents:                                                       │
│  ┌────────────────┬────────────────────┬──────────────┬──────────────┐      │
│  │ Consolidator   │ Contradiction      │ Eval Rubric  │ Gap Finder   │      │
│  │                │ Reconciler         │ (9-dim)      │              │      │
│  ├────────────────┼────────────────────┼──────────────┼──────────────┤      │
│  │ Next-Study     │ Critic             │ Reporter     │ Run Summary  │      │
│  │ Planner        │ (evidence checker) │              │              │      │
│  └────────────────┴────────────────────┴──────────────┴──────────────┘      │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                     QUALITY & GOVERNANCE LAYER                                │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ Evaluation Rubric (9 dimensions)                                      │   │
│  │ • Evidence groundedness  • Specificity    • Research usefulness       │   │
│  │ • Actionability          • Confidence     • Provenance completeness   │   │
│  │ • Contradiction handling • No overclaiming • Format validity          │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ Human Review Checkpoints                                              │   │
│  │ Auto-triggered: low confidence │ weak evidence │ unresolved tension   │   │
│  │ Status: pending → approved / rejected / needs_revision                │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                        DATA & PERSISTENCE LAYER                               │
│                                                                              │
│  Pydantic models (typed) → JSON files (inspectable) → Markdown (readable)    │
│                                                                              │
│  project_dir/data/                                                           │
│  ├── transcripts/        ├── findings/           ├── evaluations/            │
│  ├── theme_orchestration/├── themes/             ├── research_gaps/          │
│  ├── next_study/         ├── reconciliations/    ├── evals/                  │
│  ├── review_checkpoints/ ├── runs/               └── reports/                │
└─────────────────────────────────────────────────────────────────────────────┘
```

### What makes this "agentic" vs. a regular pipeline

| Property | Traditional pipeline | This system |
|----------|---------------------|-------------|
| Routing | Fixed linear order | Orchestrator decides which lanes to activate |
| Parallelism | None | 6 specialists run on the same data simultaneously |
| Quality control | Post-hoc | Eval rubric runs inline; checkpoints block advancement |
| Error handling | Stop or skip | Revelation loops re-extract; reconciler explains tensions |
| Observability | Logs | Structured run summary artifact + intermediate JSONs |
| Human role | End consumer | Active reviewer at checkpoints |

---

## How I Built It (Build Flow & Design Decisions)

### Phase 1: Foundation (existing before this upgrade)

Started with a sequential usability analysis pipeline:

1. **Ingestor** — Parse .docx and .md transcripts into structured turns
2. **Extractor** — Pull findings with verbatim quotes and provenance
3. **Evaluator** — 5-check verification with revelation loops (re-extraction on failure)
4. **Severity Rater** — Nielsen's 0–4 scale with evidence justification
5. **Heuristic Mapper** — Map to Nielsen's 10 usability heuristics
6. **Synthesizer** — Cross-participant theme identification
7. **Contradiction Detector** — Find participant disagreements
8. **Reconciler** — Basic contradiction handling
9. **Critic** — Evidence strength challenge agent
10. **Reporter** — Audience-tailored outputs (design, PM, leadership)

This was already functional but behaved like a single-threaded "summarizer with extra steps."

### Phase 2: Multi-agent upgrade (this session)

The upgrade decomposed the monolithic synthesis into a **multi-agent orchestrated system**:

1. **Theme Orchestrator** — Reads all findings, decides which thematic lanes are relevant, routes subsets to specialist agents. This is the "controller pattern" from class.

2. **6 Parallel Specialists** — Each analyzes findings through a different research lens (pain points, needs, behaviors, mental models, trust, workflow). This is the "parallel fan-out" pattern.

3. **Theme Consolidator** — Merges overlapping themes across lanes without flattening nuance. This is the "fan-in / reduce" step.

4. **Enhanced Contradiction Reconciler** — Treats tensions as signal. Segments participants, explains divergence, produces reconciled interpretations with explicit confidence bounds.

5. **Eval Rubric** — 9-dimension quality check that auto-creates human review checkpoints on failure. This is the "eval gate" pattern from class.

6. **Research Gap Finder** — Scans consolidated themes, reconciliations, and eval results to identify what we still don't know. This is a differentiator — most tools only tell you what they found.

7. **Next Study Planner** — Converts gaps into practical follow-up study recommendations with method, participant profile, and research questions.

8. **Run Summary** — Generates an observable artifact showing all stages, agents invoked, evals passed/failed, and next actions. This is the "observability" requirement.

### Key design decisions

| Decision | Rationale |
|----------|-----------|
| Keyword-based lane routing (not LLM) | Deterministic, testable, fast. LLM routing is a future enhancement. |
| Findings can appear in multiple lanes | A frustration can be both a pain point and a workflow breakdown. |
| JSON + Markdown dual output | JSON for machine consumption; Markdown for human inspection. |
| Confidence bounds on everything | Forces the system to say "I'm not sure" rather than overclaiming. |
| Eval rubric creates checkpoints automatically | Removes need for human to manually find quality problems. |
| Research gaps as a first-class output | Most pipelines stop at "here's what we found." This one says "here's what we still need." |

---

## Observed Problems & Reflections

### Things that worked well

**1. Structured handoffs prevent hallucination drift.**
When Agent A produces typed JSON that Agent B consumes, there's no room for meaning to drift between steps. The finding IDs, participant IDs, and quotes travel intact through the pipeline. This is much better than passing prose summaries between agents.

**2. The fan-out/fan-in pattern produces richer analysis.**
Running 6 specialists in parallel — each with a different analytical lens — catches things a single synthesizer misses. A "trust issue" looks different to the trust analyst vs. the workflow analyst, and the consolidator can see both perspectives.

**3. Eval rubrics catch real problems.**
The overclaiming detector ("all users always…") and the confidence-vs-evidence checker (high confidence + 1 participant) surface actual quality issues. In testing, artifacts that looked reasonable on first read failed the rubric for legitimate reasons.

**4. Research gaps change the conversation with stakeholders.**
Instead of ending with "here's our recommendations," ending with "here's what we still don't know and what to study next" positions the researcher as a strategic partner, not a service provider.

### Things that are hard

**1. Theme similarity without embeddings is brittle.**
The keyword-overlap approach for grouping findings into themes works for clear cases but misses semantic similarity. "User couldn't find the button" and "Navigation was unclear" are the same theme, but keyword overlap is low. A production system would use embeddings or an LLM classification step here.

**2. Lane routing is imperfect.**
A finding like "I hesitated because I wasn't sure it would deploy to the right environment" could belong in trust, mental models, AND workflow. The current system puts it in all three, but the consolidator then has to deduplicate. This creates some noise.

**3. Confidence calibration is hand-tuned.**
The formula `confidence = 0.4 + (findings * 0.1) + (participants * 0.1)` is reasonable but arbitrary. Proper calibration would require ground-truth data from expert researchers rating the same findings.

**4. The pipeline is only as good as extraction.**
If the extractor misses a finding or misattributes a quote, every downstream agent inherits that error. The evaluator catches some of this (verbatim match check), but extraction quality remains the critical dependency.

**5. Human review checkpoints add friction in demos.**
For a live demo, pending checkpoints that "block" the pipeline feel awkward. In production this is the right behavior (don't ship unvalidated claims), but for a show-and-tell you want the pipeline to flow end-to-end. The system handles this by making checkpoints non-blocking by default — they flag, they don't stop.

### What I'd add with more time

- **LLM-powered lane routing** — Use a fast model to classify findings into lanes instead of keywords
- **Embedding-based theme clustering** — Replace word-overlap similarity with vector similarity
- **Interactive checkpoint UI** — A web interface for reviewing and approving checkpoints
- **Longitudinal tracking** — Compare research gaps across multiple studies over time
- **Confidence calibration** — Train confidence scoring against expert-labeled data
- **Full MCP tool coverage** — Register all new agents as MCP tools for Copilot integration
- **Report generation update** — Final report that includes all new sections (gaps, next study, reconciliations)

### Reflection on the agentic approach

The biggest insight from building this: **the value of agents isn't speed — it's decomposition.**

A single prompt that says "analyze these transcripts and give me a report" can produce surprisingly good output. But you can't inspect it, you can't challenge specific claims, you can't tell where it's uncertain, and you can't rerun just the part that failed.

Decomposing into agents forces you to:
- Define explicit inputs and outputs for each step
- Make quality checkable at each boundary
- Allow humans to intervene at the right moments
- Produce artifacts that are individually useful (not just one final blob)
- Track provenance from claim back to source evidence

The cost is complexity. 26 agents is a lot of code. But the benefit is that when a stakeholder asks "how do you know that?" — you can trace the claim through consolidation → theme analysis → finding → verbatim quote → transcript turn → timestamp. That traceability is what turns an AI summary into defensible research.

---

## Demo Script (5-minute walkthrough)

For a live class demo, here's the fastest path through the system:

```bash
# Setup (do before demo)
cd ut-analysis-pipeline
uv sync

# 1. Show the config (30 sec)
cat research_config.yaml
# → "Here's my study: 3 participants, 4 tasks, success criteria defined"

# 2. Show extraction output exists (or run it)
uv run ut-analysis status --project-dir ./project_data
# → "Pipeline is at extraction_complete with 12 findings"

# 3. Run the new multi-agent pipeline (live, ~2 sec)
uv run ut-analysis orchestrate-themes --project-dir ./project_data --run-id demo
# → "6 lanes created: pain points, needs, behavior, mental models, trust, workflow"

uv run ut-analysis run-theme-agents --project-dir ./project_data --run-id demo
# → "Each specialist found 2-4 themes in their lane"

uv run ut-analysis consolidate-themes --project-dir ./project_data --run-id demo
# → "8 consolidated themes from 6 lanes"

# 4. Show quality checks (live)
uv run ut-analysis run-evals --project-dir ./project_data --run-id demo
# → "Evaluated 8 artifacts: 6 passed, 2 warnings, 0 failed"

# 5. Show what we DON'T know
uv run ut-analysis find-research-gaps --project-dir ./project_data --run-id demo
# → "3 research gaps identified"

uv run ut-analysis plan-next-study --project-dir ./project_data --run-id demo
# → "2 follow-up studies recommended"

# 6. Show observability
uv run ut-analysis run-summary --project-dir ./project_data --run-id demo
# → "Run summary: 6 stages, 12 artifacts, 8 agents, next action: share report"

# 7. Inspect an intermediate artifact (show it's not a black box)
cat project_data/data/research_gaps/demo_research_gaps.json | python -m json.tool | head -30
```

### Key talking points during demo

1. **"This isn't a summarizer"** — Show that findings route to DIFFERENT specialists who analyze through different lenses
2. **"The system knows what it doesn't know"** — Show research_gaps.json with explicit uncertainty
3. **"Quality is checked, not assumed"** — Show eval results with pass/fail and the specific dimensions checked
4. **"Every claim traces to evidence"** — Show finding_ids → verbatim_quote → transcript
5. **"Humans stay in control"** — Show review checkpoints and what triggers them

---

## File Organization for Reviewers

```
ut-analysis-pipeline/
├── README.md                    ← You are here (includes this presentation)
├── ARCHITECTURE.md              ← Detailed technical architecture
├── research_config.yaml         ← Sample study configuration
├── sample_transcript.md         ← Sample input data
├── src/
│   ├── skills/                  ← 26 agent implementations
│   │   └── ut_*/               ← Each agent: SKILL.md + __init__.py + implementation.py
│   └── ut_analysis/
│       ├── models/__init__.py   ← All Pydantic models (30+ types)
│       ├── state_management.py  ← 15 persistence managers
│       └── cli.py               ← 14 Click commands
├── tests/                       ← 72 passing tests
│   ├── test_controller.py
│   ├── test_new_agents.py       ← Tests for multi-agent upgrade
│   ├── test_thematic_analysts.py
│   ├── test_theme_orchestrator.py
│   ├── test_contradiction_reconciler.py
│   ├── test_run_summary.py
│   └── test_review_checkpoints.py
└── project_data/                ← Runtime output directory
    └── data/                    ← All intermediate artifacts (JSON + MD)
```
