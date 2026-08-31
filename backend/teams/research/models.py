"""
Research Team — Domain Models

Core data structures for the evidence-based research pipeline.
Every factual claim is traceable: Claim → Evidence → Source → Verification.

These models are designed for:
1. Structured evidence tracking
2. Source provenance
3. Claim verification
4. Zero-hallucination design (claims must have evidence)
5. Downstream agent consumption
6. User-facing report generation
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import uuid


# ─────────────────────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────────────────────

class SourceTier(str, Enum):
    """Source quality hierarchy."""
    PRIMARY = "primary"               # Official websites, docs, filings, source code
    HIGH_QUALITY_SECONDARY = "secondary"  # Reputable journalism, research orgs
    COMMUNITY = "community"           # Reddit, HN, forums, reviews
    LOW_CONFIDENCE = "low_confidence"  # SEO pages, content farms, unattributed

class SourceType(str, Enum):
    """Type of information source."""
    OFFICIAL_WEBSITE = "official_website"
    DOCUMENTATION = "documentation"
    PRICING_PAGE = "pricing_page"
    NEWS_ARTICLE = "news_article"
    BLOG_POST = "blog_post"
    ACADEMIC_PAPER = "academic_paper"
    GITHUB_REPOSITORY = "github_repository"
    FORUM_POST = "forum_post"
    REVIEW_SITE = "review_site"
    SOCIAL_MEDIA = "social_media"
    GOVERNMENT_SITE = "government_site"
    PRESS_RELEASE = "press_release"
    JOB_POSTING = "job_posting"
    DATABASE_RECORD = "database_record"
    OTHER = "other"

class ClaimConfidence(str, Enum):
    """Confidence level for a claim."""
    HIGH = "high"           # Multiple independent sources confirm
    MEDIUM = "medium"       # Single reliable source or multiple low-tier
    LOW = "low"             # Single source, unverified
    DISPUTED = "disputed"   # Sources conflict
    UNVERIFIED = "unverified"  # Not yet checked

class VerificationStatus(str, Enum):
    """Status of fact-checking for a claim."""
    VERIFIED = "verified"               # Independently confirmed
    PARTIALLY_VERIFIED = "partially_verified"  # Some aspects confirmed
    DISPUTED = "disputed"               # Sources conflict
    UNVERIFIED = "unverified"           # Not yet checked
    REFUTED = "refuted"                 # Evidence contradicts
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"  # Cannot determine

class ResearchQuestionPriority(str, Enum):
    """Priority of a research question."""
    CRITICAL = "critical"   # Must answer
    HIGH = "high"           # Should answer
    MEDIUM = "medium"       # Nice to answer
    LOW = "low"             # If time permits

class ResearchRequestType(str, Enum):
    """Type of research request — guides planning."""
    COMPETITOR_ANALYSIS = "competitor_analysis"
    MARKET_RESEARCH = "market_research"
    TECHNICAL_RESEARCH = "technical_research"
    PRODUCT_RESEARCH = "product_research"
    PRICING_RESEARCH = "pricing_research"
    ACADEMIC_RESEARCH = "academic_research"
    COMPANY_RESEARCH = "company_research"
    CUSTOMER_RESEARCH = "customer_research"
    TREND_RESEARCH = "trend_research"
    REGULATORY_RESEARCH = "regulatory_research"
    TECHNOLOGY_EVALUATION = "technology_evaluation"
    OPEN_SOURCE_EVALUATION = "open_source_evaluation"
    COMPARATIVE_ANALYSIS = "comparative_analysis"
    FACT_VERIFICATION = "fact_verification"
    GENERAL = "general"


# ─────────────────────────────────────────────────────────────
# Source & Evidence
# ─────────────────────────────────────────────────────────────

class Source(BaseModel):
    """A single information source with full provenance."""
    source_id: str = Field(default_factory=lambda: f"S-{uuid.uuid4().hex[:8]}")
    url: str
    title: str = ""
    source_type: SourceType = SourceType.OTHER
    tier: SourceTier = SourceTier.LOW_CONFIDENCE
    
    # Temporal metadata
    published_date: Optional[str] = None
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Content metadata
    author: Optional[str] = None
    domain: str = ""
    description: Optional[str] = None
    
    # Reliability
    is_accessible: bool = True
    access_error: Optional[str] = None
    content_hash: Optional[str] = None  # For deduplication
    
    def __hash__(self):
        return hash(self.url)


class Evidence(BaseModel):
    """A specific piece of evidence extracted from a source."""
    evidence_id: str = Field(default_factory=lambda: f"E-{uuid.uuid4().hex[:8]}")
    source_id: str                     # Reference to Source
    
    text: str                          # The actual evidence text/snippet
    context: str = ""                  # Surrounding context
    location: Optional[str] = None     # Where in the source (section, heading, etc.)
    
    extracted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    extracted_by: str = ""             # Agent who extracted (e.g., "Aarav")
    
    relevance_score: float = 0.0       # How relevant to the question (0-1)


class Claim(BaseModel):
    """A factual assertion derived from evidence."""
    claim_id: str = Field(default_factory=lambda: f"C-{uuid.uuid4().hex[:8]}")
    text: str                          # The claim itself
    
    # Evidence chain
    evidence_ids: List[str] = Field(default_factory=list)
    source_ids: List[str] = Field(default_factory=list)
    
    # Verification
    confidence: ClaimConfidence = ClaimConfidence.UNVERIFIED
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED
    verified_by: Optional[str] = None  # "Aditya" or None
    verification_notes: str = ""
    
    # Conflict tracking
    conflicting_claim_ids: List[str] = Field(default_factory=list)
    conflicts_description: Optional[str] = None
    
    # Metadata
    category: str = ""                 # e.g., "pricing", "features", "sentiment"
    is_time_sensitive: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ─────────────────────────────────────────────────────────────
# Research Planning
# ─────────────────────────────────────────────────────────────

class SearchStrategy(BaseModel):
    """A set of queries for investigating a research question."""
    queries: List[str] = Field(default_factory=list)
    source_types_needed: List[SourceType] = Field(default_factory=list)
    rationale: str = ""


class ResearchQuestion(BaseModel):
    """A specific question to investigate."""
    question_id: str = Field(default_factory=lambda: f"Q-{uuid.uuid4().hex[:8]}")
    text: str
    priority: ResearchQuestionPriority = ResearchQuestionPriority.MEDIUM
    category: str = ""                 # e.g., "pricing", "technical", "competitive"
    
    # Dependencies
    depends_on: List[str] = Field(default_factory=list)  # question_ids
    
    # Search strategy
    search_strategy: SearchStrategy = Field(default_factory=SearchStrategy)
    
    # Requirements
    requires_current_info: bool = False
    requires_primary_sources: bool = False
    requires_quantitative_data: bool = False
    minimum_source_count: int = 2
    
    # Status
    is_answered: bool = False
    answer_summary: str = ""
    claim_ids: List[str] = Field(default_factory=list)


class ResearchPlan(BaseModel):
    """Meera's research plan — the decomposed research strategy."""
    plan_id: str = Field(default_factory=lambda: f"RP-{uuid.uuid4().hex[:8]}")
    
    original_request: str
    interpreted_objective: str
    research_type: ResearchRequestType = ResearchRequestType.GENERAL
    
    questions: List[ResearchQuestion] = Field(default_factory=list)
    
    # Scope & criteria
    scope_description: str = ""
    acceptance_criteria: List[str] = Field(default_factory=list)
    stopping_criteria: List[str] = Field(default_factory=list)
    
    # Expected entities/domains
    key_entities: List[str] = Field(default_factory=list)
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str = "Meera"


# ─────────────────────────────────────────────────────────────
# Research Findings & Comparisons
# ─────────────────────────────────────────────────────────────

class ResearchFinding(BaseModel):
    """A synthesized finding — conclusion drawn from verified claims."""
    finding_id: str = Field(default_factory=lambda: f"F-{uuid.uuid4().hex[:8]}")
    title: str
    summary: str
    
    claim_ids: List[str] = Field(default_factory=list)
    confidence: ClaimConfidence = ClaimConfidence.MEDIUM
    
    implications: List[str] = Field(default_factory=list)
    category: str = ""
    
    is_actionable: bool = False
    recommended_actions: List[str] = Field(default_factory=list)


class ComparisonEntry(BaseModel):
    """A single cell in a comparison matrix."""
    entity: str
    criterion: str
    value: str
    source_ids: List[str] = Field(default_factory=list)
    confidence: ClaimConfidence = ClaimConfidence.MEDIUM
    notes: str = ""


class ComparisonMatrix(BaseModel):
    """Structured comparison for comparative research."""
    entities: List[str] = Field(default_factory=list)
    criteria: List[str] = Field(default_factory=list)
    entries: List[ComparisonEntry] = Field(default_factory=list)
    
    def get_entry(self, entity: str, criterion: str) -> Optional[ComparisonEntry]:
        for entry in self.entries:
            if entry.entity == entity and entry.criterion == criterion:
                return entry
        return None


# ─────────────────────────────────────────────────────────────
# Quality Assessment
# ─────────────────────────────────────────────────────────────

class ResearchQualityScore(BaseModel):
    """Explainable quality assessment of the research output."""
    overall_score: float = Field(ge=0.0, le=100.0, default=0.0)
    
    # Dimension scores
    question_coverage_pct: float = 0.0        # % of questions answered
    source_quality_avg: float = 0.0           # Average source tier score
    source_diversity_score: float = 0.0       # Variety of source types
    evidence_density: float = 0.0             # Claims per question
    verification_coverage_pct: float = 0.0    # % of claims verified
    recency_score: float = 0.0               # How current are sources
    contradiction_count: int = 0
    unresolved_questions: int = 0
    
    explanation: str = ""  # Human-readable explanation


# ─────────────────────────────────────────────────────────────
# Audit Trail
# ─────────────────────────────────────────────────────────────

class ResearchAction(BaseModel):
    """A single auditable action in the research process."""
    action_id: str = Field(default_factory=lambda: f"A-{uuid.uuid4().hex[:8]}")
    agent: str                         # "Meera", "Aarav", "Aditya", "Nisha"
    action: str                        # e.g., "created_research_question", "executed_search", "verified_claim"
    details: str = ""                  # Human-readable description
    
    # References
    question_id: Optional[str] = None
    source_id: Optional[str] = None
    claim_id: Optional[str] = None
    evidence_id: Optional[str] = None
    
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Context
    task_id: Optional[str] = None
    tool_used: Optional[str] = None
    input_summary: Optional[str] = None
    output_summary: Optional[str] = None


class ResearchTrace(BaseModel):
    """Complete audit trail of the research process."""
    actions: List[ResearchAction] = Field(default_factory=list)
    
    def log(self, agent: str, action: str, details: str = "", **kwargs) -> ResearchAction:
        entry = ResearchAction(agent=agent, action=action, details=details, **kwargs)
        self.actions.append(entry)
        return entry
    
    def get_agent_actions(self, agent: str) -> List[ResearchAction]:
        return [a for a in self.actions if a.agent == agent]
    
    def get_question_actions(self, question_id: str) -> List[ResearchAction]:
        return [a for a in self.actions if a.question_id == question_id]


# ─────────────────────────────────────────────────────────────
# Research Artifact — The Final Output
# ─────────────────────────────────────────────────────────────

class DownstreamContext(BaseModel):
    """Machine-consumable context for other teams."""
    objective: str
    key_facts: List[str] = Field(default_factory=list)
    important_entities: List[str] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)
    market_conditions: List[str] = Field(default_factory=list)
    technical_findings: List[str] = Field(default_factory=list)
    
    implications: Dict[str, List[str]] = Field(default_factory=dict)  # team_name → implications
    open_questions: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    recommended_next_actions: List[str] = Field(default_factory=list)


class ResearchArtifact(BaseModel):
    """
    The complete output of the Research Team.
    
    This is NOT just a text answer — it's a structured, traceable,
    verifiable research package that other teams can consume.
    """
    research_id: str = Field(default_factory=lambda: f"R-{uuid.uuid4().hex[:8]}")
    
    # Request
    original_request: str
    interpreted_objective: str
    research_type: ResearchRequestType = ResearchRequestType.GENERAL
    
    # Plan
    research_plan: Optional[ResearchPlan] = None
    
    # Evidence chain
    sources: List[Source] = Field(default_factory=list)
    evidence: List[Evidence] = Field(default_factory=list)
    claims: List[Claim] = Field(default_factory=list)
    
    # Categorized claims
    verified_claims: List[str] = Field(default_factory=list)     # claim_ids
    disputed_claims: List[str] = Field(default_factory=list)     # claim_ids
    unverified_claims: List[str] = Field(default_factory=list)   # claim_ids
    
    # Synthesis
    findings: List[ResearchFinding] = Field(default_factory=list)
    comparison: Optional[ComparisonMatrix] = None
    
    # Unanswered
    unanswered_questions: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    
    # Quality
    quality_score: ResearchQualityScore = Field(default_factory=ResearchQualityScore)
    
    # Downstream
    downstream_context: Optional[DownstreamContext] = None
    
    # User-facing report (Nisha's output)
    user_report: str = ""
    executive_summary: str = ""
    
    # Audit
    trace: ResearchTrace = Field(default_factory=ResearchTrace)
    
    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    total_sources_consulted: int = 0
    total_searches_performed: int = 0
    
    # Helpers
    def get_source(self, source_id: str) -> Optional[Source]:
        return next((s for s in self.sources if s.source_id == source_id), None)
    
    def get_claim(self, claim_id: str) -> Optional[Claim]:
        return next((c for c in self.claims if c.claim_id == claim_id), None)
    
    def get_evidence(self, evidence_id: str) -> Optional[Evidence]:
        return next((e for e in self.evidence if e.evidence_id == evidence_id), None)
    
    def get_verified_claims(self) -> List[Claim]:
        return [c for c in self.claims if c.verification_status == VerificationStatus.VERIFIED]
    
    def get_disputed_claims(self) -> List[Claim]:
        return [c for c in self.claims if c.verification_status == VerificationStatus.DISPUTED]
