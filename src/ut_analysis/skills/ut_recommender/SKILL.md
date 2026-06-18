# ut-recommender Skill

## Purpose

The **ut-recommender** skill generates actionable, prioritized recommendations from usability findings. It transforms raw findings into specific, implementable design and development recommendations with clear rationale, impact assessment, and implementation guidance.

## Key Responsibilities

1. **Recommendation Generation**
   - Convert findings into specific recommendations
   - Provide multiple solution options when applicable
   - Include implementation details and effort estimates
   - Link recommendations to design principles and best practices

2. **Prioritization Framework**
   - Impact vs effort matrix for prioritization
   - Business value assessment
   - Technical feasibility evaluation
   - Timeline and resource requirements

3. **Solution Design**
   - Wireframe and mockup suggestions
   - Technical implementation approaches
   - User testing validation methods
   - Success metrics and KPIs

4. **Stakeholder Communication**
   - Executive summaries for leadership
   - Technical specifications for developers
   - Design rationale for design teams
   - Implementation roadmaps for project managers

5. **Validation and Testing**
   - Success criteria for each recommendation
   - A/B testing suggestions
   - User validation methods
   - Performance impact assessment

## Input Format

```json
{
  "command": "generate_recommendations",
  "findings_batch_id": "batch_001",
  "recommendations_batch_id": "recs_001",
  "recommendation_config": {
    "prioritization_method": "impact_effort",
    "include_alternatives": true,
    "target_audiences": ["design", "development", "product"],
    "implementation_focus": "near_term",
    "business_context": {
      "timeline": "3_months",
      "budget": "medium",
      "resources": ["design", "frontend", "backend"]
    }
  }
}
```

## Output Format

```json
{
  "recommendations_batch_id": "recs_001",
  "recommendations": [
    {
      "recommendation_id": "REC_001",
      "finding_id": "F_001",
      "title": "Redesign Checkout Discount Code Flow",
      "description": "Simplify discount code entry with inline validation and clear placement",
      "priority": "critical",
      "impact_score": 8.5,
      "effort_score": 3.2,
      "rationale": "Users struggled to find and apply discount codes, leading to abandoned carts",
      "solutions": [
        {
          "approach": "Inline Discount Field",
          "description": "Add discount code field directly in payment summary with real-time validation",
          "implementation": {
            "frontend": "Add React component with validation",
            "backend": "Update discount API endpoint",
            "design": "Create new wireframes for payment flow"
          },
          "effort_estimate": "2-3 weeks",
          "impact_estimate": "15-20% reduction in cart abandonment"
        },
        {
          "approach": "Modal Discount Overlay",
          "description": "Trigger discount modal from payment summary link",
          "implementation": {
            "frontend": "Create modal component",
            "backend": "Reuse existing discount API",
            "design": "Design modal interface"
          },
          "effort_estimate": "1-2 weeks",
          "impact_estimate": "10-15% reduction in cart abandonment"
        }
      ],
      "success_metrics": [
        "Task completion rate for discount application",
        "Cart abandonment rate",
        "User satisfaction scores"
      ],
      "target_audience": "design_development",
      "timeline": "immediate",
      "dependencies": [],
      "generated_at": "2026-05-08T14:30:00Z"
    }
  ],
  "prioritization_matrix": {
    "high_impact_low_effort": ["REC_001", "REC_003"],
    "high_impact_high_effort": ["REC_002", "REC_007"],
    "low_impact_low_effort": ["REC_004", "REC_005"],
    "low_impact_high_effort": ["REC_006"]
  },
  "implementation_roadmap": {
    "phase_1_immediate": {
      "recommendations": ["REC_001", "REC_003"],
      "duration_weeks": 4,
      "resources_needed": ["design", "frontend"],
      "expected_impact": "25% improvement in key metrics"
    },
    "phase_2_short_term": {
      "recommendations": ["REC_002", "REC_004"],
      "duration_weeks": 8,
      "resources_needed": ["design", "frontend", "backend"],
      "expected_impact": "40% improvement in key metrics"
    }
  },
  "recommendation_stats": {
    "total_recommendations": 12,
    "by_priority": {"critical": 3, "high": 4, "medium": 3, "low": 2},
    "by_audience": {"design": 8, "development": 6, "product": 4},
    "average_impact_score": 7.2,
    "average_effort_score": 4.1,
    "implementation_coverage": 95
  }
}
```

## Recommendation Types

### Design Recommendations
**Focus**: User interface and experience improvements
**Content**:
- Layout and visual design changes
- Information architecture improvements
- Interaction design modifications
- Accessibility enhancements

### Technical Recommendations
**Focus**: System and code-level improvements
**Content**:
- Performance optimizations
- Error handling improvements
- API and data structure changes
- Security enhancements

### Content Recommendations
**Focus**: Information and communication improvements
**Content**:
- Copy and messaging improvements
- Help and documentation updates
- Error message enhancements
- Instructional content additions

### Process Recommendations
**Focus**: Workflow and organizational improvements
**Content**:
- User onboarding improvements
- Support process enhancements
- Training and education updates
- Communication channel improvements

## Prioritization Framework

### Impact Assessment
**User Impact**: How many users affected, severity of problem
**Business Impact**: Revenue, conversion, satisfaction effects
**Technical Impact**: System performance, maintenance costs
**Strategic Impact**: Alignment with business goals

### Effort Assessment
**Design Effort**: UI/UX design and prototyping work
**Development Effort**: Coding, testing, deployment work
**Content Effort**: Writing, translation, review work
**Coordination Effort**: Stakeholder alignment, approvals

### Priority Matrix
- **Quick Wins**: High impact, low effort - implement immediately
- **Strategic Investments**: High impact, high effort - plan for future
- **Low-Hanging Fruit**: Low impact, low effort - implement when resources available
- **Questionable Value**: Low impact, high effort - reconsider or deprioritize

## Solution Generation

### Multiple Approaches
- Primary recommended solution
- Alternative approaches with trade-offs
- Quick vs comprehensive solutions
- Technical vs design-focused solutions

### Implementation Details
- Specific technical requirements
- Design specifications
- Content requirements
- Testing and validation criteria

### Resource Requirements
- Team roles needed (design, development, content)
- Time estimates by phase
- Dependencies and prerequisites
- Risk factors and mitigation

## Success Metrics

### Quantitative Metrics
- Task completion rates
- Error rates and recovery times
- User satisfaction scores
- Conversion and abandonment rates
- Performance metrics (load times, etc.)

### Qualitative Metrics
- User feedback and comments
- Usability testing results
- Stakeholder satisfaction
- Team productivity improvements

### Business Metrics
- Revenue impact
- Customer retention
- Support ticket reduction
- Feature adoption rates

## Implementation Roadmap

### Phase 1: Immediate (1-4 weeks)
- Critical issues with quick fixes
- High-impact, low-effort changes
- Emergency accessibility fixes
- Basic error handling improvements

### Phase 2: Short-term (1-3 months)
- Major design improvements
- System performance enhancements
- Content and communication updates
- Process improvements

### Phase 3: Medium-term (3-6 months)
- Large-scale redesigns
- New feature development
- Advanced technical improvements
- Organizational process changes

### Phase 4: Long-term (6+ months)
- Strategic platform changes
- Major architectural improvements
- Advanced feature development
- Industry-leading enhancements

## Integration Points

- **MCP Tools**: `load_findings`, `generate_recommendations`, `save_recommendations`
- **State Management**: Persists recommendations in `data/recommendations/`
- **ut-evaluator**: Uses evaluation results for prioritization
- **ut-synthesizer**: Incorporates insight patterns
- **External Tools**: Design tools, development trackers, project management systems

## Quality Metrics

- Recommendation specificity: % with clear implementation steps
- Impact accuracy: Validation against business metrics
- Effort estimation accuracy: Comparison with actual implementation time
- Stakeholder acceptance: % recommendations approved and implemented
- User impact: Measured improvement in user experience metrics

## Example Usage

```python
from ut_analysis.skills.recommender import RecommenderSkill

recommender = RecommenderSkill()

# Generate recommendations
result = recommender.generate_recommendations(
    findings_batch_id="batch_001",
    recommendations_batch_id="recs_001",
    recommendation_config={
        "prioritization_method": "impact_effort",
        "target_audiences": ["design", "development"],
        "business_context": {
            "timeline": "3_months",
            "resources": ["design", "frontend"]
        }
    }
)

# Check prioritized recommendations
high_impact = result["prioritization_matrix"]["high_impact_low_effort"]
print(f"Found {len(high_impact)} quick win recommendations")
```

## Validation Rules

- All recommendations must link to specific findings
- Impact and effort scores must be calculated
- Implementation details must be provided
- Success metrics must be defined
- Dependencies must be identified

## Error Handling

**Missing Context:**
- Use default prioritization when business context unavailable
- Generate generic recommendations when specific details missing
- Flag recommendations requiring additional input

**Conflicting Priorities:**
- Apply weighted scoring for multi-criteria decisions
- Provide alternative prioritization views
- Document assumptions and trade-offs

**Implementation Gaps:**
- Identify recommendations requiring additional research
- Suggest phased approaches for complex changes
- Provide fallback solutions for high-risk items

## Performance Considerations

- Batch processing: Generate recommendations for multiple findings together
- Template reuse: Use recommendation patterns for similar issues
- Incremental updates: Add recommendations without full regeneration
- Caching: Store common recommendation templates
- Parallel generation: Process different finding types concurrently
