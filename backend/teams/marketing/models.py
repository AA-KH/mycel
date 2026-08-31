"""
Marketing Team — Domain Models

Core data structures for the autonomous marketing department.
Every marketing output is traceable: Strategy → Campaign → Content → Performance → Learning.

These models are designed for:
1. Structured marketing workflow state
2. Brand context preservation
3. Campaign lifecycle management
4. Content versioning and quality tracking
5. Growth experiment rigor
6. Cross-team artifact consumption
7. Auditability (MarketingTrace)
8. Zero-fabrication design (DataLabel for all metrics)
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import uuid


# ─────────────────────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────────────────────

class MarketingRequestType(str, Enum):
    """Type of marketing request — guides scope determination."""
    BRAND_CREATION = "brand_creation"
    BRAND_STRATEGY = "brand_strategy"
    GTM = "gtm"
    LAUNCH = "launch"
    CONTENT = "content"
    SEO = "seo"
    SOCIAL = "social"
    EMAIL = "email"
    PAID_ACQUISITION = "paid_acquisition"
    GROWTH = "growth"
    PRODUCT_MARKETING = "product_marketing"
    CAMPAIGN = "campaign"
    PR = "pr"
    COMMUNITY = "community"
    INFLUENCER = "influencer"
    CONVERSION_OPTIMIZATION = "conversion_optimization"
    ANALYTICS = "analytics"
    RETENTION = "retention"
    ACQUISITION = "acquisition"
    MARKET_EXPANSION = "market_expansion"
    REBRANDING = "rebranding"
    COMPETITIVE_ANALYSIS = "competitive_analysis"
    CRISIS_COMMUNICATIONS = "crisis_communications"
    GENERAL = "general"


class ContentStatus(str, Enum):
    """Lifecycle state of a content asset."""
    DRAFT = "draft"
    REVIEW = "review"
    REVISION_REQUESTED = "revision_requested"
    APPROVED = "approved"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class CampaignStatus(str, Enum):
    """Lifecycle state of a marketing campaign."""
    PLANNING = "planning"
    RESEARCH = "research"
    STRATEGY = "strategy"
    PRODUCTION = "production"
    REVIEW = "review"
    READY = "ready"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class FunnelStage(str, Enum):
    """Position in the marketing/sales funnel."""
    AWARENESS = "awareness"
    CONSIDERATION = "consideration"
    CONVERSION = "conversion"
    RETENTION = "retention"
    ADVOCACY = "advocacy"


class ChannelType(str, Enum):
    """Marketing channel."""
    LINKEDIN = "linkedin"
    X = "x"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"
    FACEBOOK = "facebook"
    REDDIT = "reddit"
    THREADS = "threads"
    EMAIL = "email"
    BLOG = "blog"
    WEBSITE = "website"
    PAID_SEARCH = "paid_search"
    PAID_SOCIAL = "paid_social"
    SEO = "seo"
    PR = "pr"
    COMMUNITY = "community"
    INFLUENCER = "influencer"
    PODCAST = "podcast"
    NEWSLETTER = "newsletter"
    OTHER = "other"


class ContentType(str, Enum):
    """Type of marketing content."""
    SOCIAL_POST = "social_post"
    BLOG_POST = "blog_post"
    NEWSLETTER = "newsletter"
    EMAIL_CAMPAIGN = "email_campaign"
    LANDING_PAGE_COPY = "landing_page_copy"
    AD_COPY = "ad_copy"
    VIDEO_SCRIPT = "video_script"
    SHORT_FORM_VIDEO_SCRIPT = "short_form_video_script"
    CASE_STUDY = "case_study"
    WHITEPAPER = "whitepaper"
    GUIDE = "guide"
    LEAD_MAGNET = "lead_magnet"
    PRESS_RELEASE = "press_release"
    PRODUCT_COPY = "product_copy"
    THOUGHT_LEADERSHIP = "thought_leadership"
    FOUNDER_CONTENT = "founder_content"
    HEADLINE = "headline"
    HOOK = "hook"
    CTA = "cta"
    TESTIMONIAL_FORMAT = "testimonial_format"
    ANNOUNCEMENT = "announcement"
    COMMUNITY_CONTENT = "community_content"
    PARTNERSHIP_CONTENT = "partnership_content"
    NURTURE_SEQUENCE = "nurture_sequence"
    ONBOARDING_EMAIL = "onboarding_email"
    REACTIVATION_EMAIL = "reactivation_email"
    WEBSITE_COPY = "website_copy"
    ELEVATOR_PITCH = "elevator_pitch"
    OTHER = "other"


class ExperimentStatus(str, Enum):
    """Status of a growth experiment."""
    HYPOTHESIS = "hypothesis"
    PLANNED = "planned"
    RUNNING = "running"
    COMPLETED = "completed"
    INCONCLUSIVE = "inconclusive"
    CANCELLED = "cancelled"


class DataLabel(str, Enum):
    """Classification for any metric value — never merge observed with forecast."""
    OBSERVED = "observed"
    FORECAST = "forecast"
    ESTIMATE = "estimate"
    BENCHMARK = "benchmark"
    UNKNOWN = "unknown"


class ApprovalStatus(str, Enum):
    """Authority gate status."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NOT_REQUIRED = "not_required"


class ExecutionState(str, Enum):
    """State of an external action."""
    PLAN = "plan"
    DRAFT = "draft"
    READY_FOR_APPROVAL = "ready_for_approval"
    APPROVED = "approved"
    EXECUTING = "executing"
    SUCCESS = "success"
    FAILED = "failed"


# ─────────────────────────────────────────────────────────────
# Brand & Positioning
# ─────────────────────────────────────────────────────────────

class Persona(BaseModel):
    """A customer/audience persona."""
    name: str
    description: str = ""
    demographics: Dict[str, str] = Field(default_factory=dict)
    psychographics: List[str] = Field(default_factory=list)
    pain_points: List[str] = Field(default_factory=list)
    goals: List[str] = Field(default_factory=list)
    objections: List[str] = Field(default_factory=list)
    preferred_channels: List[ChannelType] = Field(default_factory=list)
    language_patterns: List[str] = Field(default_factory=list)
    jobs_to_be_done: List[str] = Field(default_factory=list)


class BrandContext(BaseModel):
    """
    Structured brand memory — the marketing team's shared understanding of the brand.
    Integrates with the Mycel MemoryService for persistence.
    """
    brand_id: str = Field(default_factory=lambda: f"BRD-{uuid.uuid4().hex[:8]}")

    # Identity
    name: str = ""
    tagline: str = ""
    identity: str = ""
    mission: str = ""
    vision: str = ""
    values: List[str] = Field(default_factory=list)

    # Audience
    audience_description: str = ""
    icp: str = ""  # Ideal Customer Profile
    personas: List[Persona] = Field(default_factory=list)

    # Positioning
    positioning: str = ""
    differentiators: List[str] = Field(default_factory=list)
    value_propositions: List[str] = Field(default_factory=list)
    competitive_advantages: List[str] = Field(default_factory=list)

    # Messaging
    messaging_pillars: List[str] = Field(default_factory=list)
    key_messages: List[str] = Field(default_factory=list)
    elevator_pitch: str = ""
    tone: str = ""
    voice: str = ""
    vocabulary: List[str] = Field(default_factory=list)
    banned_phrases: List[str] = Field(default_factory=list)
    preferred_phrases: List[str] = Field(default_factory=list)

    # Claims & Proof
    claims: List[str] = Field(default_factory=list)
    approved_proof: List[str] = Field(default_factory=list)

    # Products
    products: List[Dict[str, Any]] = Field(default_factory=list)

    # Competitive landscape
    competitors: List[str] = Field(default_factory=list)

    # Channels & Goals
    active_channels: List[ChannelType] = Field(default_factory=list)
    goals: List[str] = Field(default_factory=list)

    # History
    historical_campaigns: List[str] = Field(default_factory=list)  # campaign_ids
    performance_summary: Dict[str, Any] = Field(default_factory=dict)
    learnings: List[str] = Field(default_factory=list)

    # Metadata
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MessagingFramework(BaseModel):
    """Structured messaging architecture for a brand or campaign."""
    framework_id: str = Field(default_factory=lambda: f"MSG-{uuid.uuid4().hex[:8]}")
    value_proposition: str = ""
    elevator_pitch: str = ""
    tagline: str = ""
    key_messages: List[str] = Field(default_factory=list)
    audience_specific_messages: Dict[str, List[str]] = Field(default_factory=dict)
    messaging_pillars: List[str] = Field(default_factory=list)
    proof_points: List[str] = Field(default_factory=list)
    objection_responses: Dict[str, str] = Field(default_factory=dict)
    tone_guidelines: str = ""
    vocabulary_preferences: List[str] = Field(default_factory=list)


class CompetitorProfile(BaseModel):
    """Structured competitor intelligence."""
    competitor_id: str = Field(default_factory=lambda: f"CMP-{uuid.uuid4().hex[:8]}")
    name: str
    positioning: str = ""
    products: List[str] = Field(default_factory=list)
    pricing: str = ""
    target_audience: str = ""
    messaging: str = ""
    channels: List[ChannelType] = Field(default_factory=list)
    content_strategy: str = ""
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    differentiators: List[str] = Field(default_factory=list)
    recent_changes: List[str] = Field(default_factory=list)
    customer_sentiment: str = ""
    seo_presence: str = ""
    social_presence: Dict[str, str] = Field(default_factory=dict)
    white_space: List[str] = Field(default_factory=list)  # Opportunities they're missing
    data_sources: List[str] = Field(default_factory=list)  # Provenance


# ─────────────────────────────────────────────────────────────
# Marketing Brief & Strategy
# ─────────────────────────────────────────────────────────────

class MarketingBrief(BaseModel):
    """
    Structured brief capturing all inputs for a marketing engagement.
    Can be auto-filled or user-provided.
    """
    brief_id: str = Field(default_factory=lambda: f"MB-{uuid.uuid4().hex[:8]}")

    # Business context
    business: str = ""
    product: str = ""
    objective: str = ""

    # Audience
    target_audience: str = ""
    geography: str = ""
    market: str = ""

    # Constraints
    budget: str = ""
    timeframe: str = ""
    constraints: List[str] = Field(default_factory=list)

    # Brand
    brand_context: Optional[BrandContext] = None

    # Current state
    current_channels: List[ChannelType] = Field(default_factory=list)
    current_performance: Dict[str, Any] = Field(default_factory=dict)

    # Campaign specifics
    campaign_objective: str = ""
    desired_action: str = ""
    funnel_stage: Optional[FunnelStage] = None
    available_assets: List[str] = Field(default_factory=list)
    required_deliverables: List[str] = Field(default_factory=list)

    # Authority
    approval_requirements: List[str] = Field(default_factory=list)

    # Metadata
    request_types: List[MarketingRequestType] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ChannelStrategy(BaseModel):
    """Strategy for a specific marketing channel."""
    channel: ChannelType
    audience: str = ""
    objectives: List[str] = Field(default_factory=list)
    content_types: List[ContentType] = Field(default_factory=list)
    frequency: str = ""
    kpis: Dict[str, str] = Field(default_factory=dict)
    budget: str = ""
    rationale: str = ""
    priority: str = "medium"


class MarketingStrategy(BaseModel):
    """
    Comprehensive marketing strategy — Neha's primary output.
    Connects business objective to actionable marketing plan.
    """
    strategy_id: str = Field(default_factory=lambda: f"MS-{uuid.uuid4().hex[:8]}")

    # Strategic foundation
    objective: str = ""
    situation_analysis: str = ""

    # Audience
    audience: str = ""
    icp: str = ""
    personas: List[Persona] = Field(default_factory=list)

    # Positioning & Messaging
    positioning: str = ""
    messaging_framework: Optional[MessagingFramework] = None

    # Channels
    channel_strategies: List[ChannelStrategy] = Field(default_factory=list)
    primary_channels: List[ChannelType] = Field(default_factory=list)

    # Campaigns
    campaign_themes: List[str] = Field(default_factory=list)

    # KPIs & Measurement
    kpis: Dict[str, str] = Field(default_factory=dict)
    success_criteria: List[str] = Field(default_factory=list)

    # Plan
    timeline: str = ""
    budget_allocation: Dict[str, str] = Field(default_factory=dict)
    priorities: List[str] = Field(default_factory=list)

    # Experiments
    proposed_experiments: List[str] = Field(default_factory=list)

    # Risk & Assumptions
    risks: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)

    # Cross-team needs
    research_needs: List[str] = Field(default_factory=list)
    creative_needs: List[str] = Field(default_factory=list)
    developer_needs: List[str] = Field(default_factory=list)
    finance_needs: List[str] = Field(default_factory=list)
    legal_needs: List[str] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str = "Neha"


# ─────────────────────────────────────────────────────────────
# Campaign
# ─────────────────────────────────────────────────────────────

class CampaignAsset(BaseModel):
    """Reference to a content asset within a campaign."""
    asset_id: str
    content_type: ContentType
    platform: Optional[ChannelType] = None
    status: ContentStatus = ContentStatus.DRAFT


class CampaignDependency(BaseModel):
    """A dependency of the campaign on another team or resource."""
    dependency_id: str = Field(default_factory=lambda: f"DEP-{uuid.uuid4().hex[:8]}")
    type: str  # "research", "creative", "developer", "finance", "legal"
    description: str
    status: str = "pending"  # pending, requested, in_progress, completed, blocked
    artifact_reference: Optional[str] = None


class LabeledMetric(BaseModel):
    """A metric value with explicit data provenance labeling."""
    name: str
    value: Any
    label: DataLabel = DataLabel.UNKNOWN
    source: str = ""
    date: Optional[str] = None


class Campaign(BaseModel):
    """
    A marketing campaign — the central organizing unit for coordinated marketing work.
    Tracks lifecycle from planning through execution to measurement.
    """
    campaign_id: str = Field(default_factory=lambda: f"CMP-{uuid.uuid4().hex[:8]}")

    # Strategy
    name: str = ""
    objective: str = ""
    audience: str = ""
    positioning: str = ""
    messaging: str = ""
    narrative: str = ""

    # Channels
    channels: List[ChannelType] = Field(default_factory=list)

    # Timeline & Budget
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    timeline: str = ""
    budget: str = ""

    # Assets
    assets: List[CampaignAsset] = Field(default_factory=list)

    # Dependencies
    dependencies: List[CampaignDependency] = Field(default_factory=list)

    # Approval
    approval_status: ApprovalStatus = ApprovalStatus.PENDING

    # Execution
    status: CampaignStatus = CampaignStatus.PLANNING
    execution_state: ExecutionState = ExecutionState.PLAN

    # KPIs
    kpis: Dict[str, str] = Field(default_factory=dict)

    # Performance (always labeled)
    performance: List[LabeledMetric] = Field(default_factory=list)

    # Experiments
    experiment_ids: List[str] = Field(default_factory=list)

    # Learning
    learnings: List[str] = Field(default_factory=list)
    next_actions: List[str] = Field(default_factory=list)

    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str = "Neha"


# ─────────────────────────────────────────────────────────────
# Content
# ─────────────────────────────────────────────────────────────

class ContentVersion(BaseModel):
    """A single version of a content asset."""
    version: int = 1
    content: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str = "Karan"
    review_notes: str = ""
    status: ContentStatus = ContentStatus.DRAFT


class ContentAsset(BaseModel):
    """
    A single piece of marketing content with full lifecycle tracking.
    Supports versioning, quality scoring, and performance linkage.
    """
    asset_id: str = Field(default_factory=lambda: f"CA-{uuid.uuid4().hex[:8]}")

    # Identity
    content_type: ContentType
    platform: Optional[ChannelType] = None
    campaign_id: Optional[str] = None

    # Context
    topic: str = ""
    audience: str = ""
    funnel_stage: FunnelStage = FunnelStage.AWARENESS

    # Content
    headline: str = ""
    hook: str = ""
    content: str = ""
    cta: str = ""
    hashtags: List[str] = Field(default_factory=list)
    media_requirements: List[str] = Field(default_factory=list)

    # Source
    message_source: str = ""  # Which campaign message/pillar this derives from
    source_asset_id: Optional[str] = None  # For repurposed content

    # Quality
    brand_voice_score: Optional[float] = None
    quality_check: Optional[Dict[str, Any]] = None

    # Lifecycle
    status: ContentStatus = ContentStatus.DRAFT
    versions: List[ContentVersion] = Field(default_factory=list)

    # Performance (always labeled)
    performance: List[LabeledMetric] = Field(default_factory=list)

    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str = "Karan"


class ContentCalendarEntry(BaseModel):
    """A single entry in a content calendar."""
    entry_id: str = Field(default_factory=lambda: f"CCE-{uuid.uuid4().hex[:8]}")
    date: str = ""
    platform: Optional[ChannelType] = None
    content_type: ContentType = ContentType.SOCIAL_POST
    objective: str = ""
    audience: str = ""
    topic: str = ""
    hook: str = ""
    cta: str = ""
    asset_requirement: str = ""
    campaign_id: Optional[str] = None
    funnel_stage: FunnelStage = FunnelStage.AWARENESS
    status: ContentStatus = ContentStatus.DRAFT
    asset_id: Optional[str] = None  # Linked to actual ContentAsset when created


class ContentCalendar(BaseModel):
    """Structured content calendar linked to strategy."""
    calendar_id: str = Field(default_factory=lambda: f"CC-{uuid.uuid4().hex[:8]}")
    strategy_id: Optional[str] = None
    campaign_id: Optional[str] = None
    entries: List[ContentCalendarEntry] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str = "Karan"


# ─────────────────────────────────────────────────────────────
# Creative Brief (for Creative Team handoff)
# ─────────────────────────────────────────────────────────────

class CreativeBrief(BaseModel):
    """
    Marketing → Creative Team handoff document.
    Marketing owns the message. Creative owns the visual execution.
    """
    brief_id: str = Field(default_factory=lambda: f"CB-{uuid.uuid4().hex[:8]}")
    campaign_id: Optional[str] = None

    # What
    objective: str = ""
    message: str = ""
    cta: str = ""

    # Who
    audience: str = ""

    # Where
    channel: Optional[ChannelType] = None
    platform_specs: Dict[str, Any] = Field(default_factory=dict)  # Dimensions, format, etc.

    # Creative direction
    required_assets: List[str] = Field(default_factory=list)
    visual_direction: str = ""
    brand_guidelines: str = ""
    tone: str = ""
    reference_examples: List[str] = Field(default_factory=list)

    # Constraints
    deadline: Optional[str] = None
    constraints: List[str] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str = "Neha"


# ─────────────────────────────────────────────────────────────
# Growth & Experimentation
# ─────────────────────────────────────────────────────────────

class GrowthExperiment(BaseModel):
    """
    A rigorous growth experiment — not merely a random change.
    Requires hypothesis, metric, baseline, expected result.
    """
    experiment_id: str = Field(default_factory=lambda: f"EXP-{uuid.uuid4().hex[:8]}")

    # Hypothesis
    hypothesis: str = ""
    problem: str = ""
    intervention: str = ""

    # Targeting
    target_audience: str = ""

    # Measurement
    primary_metric: str = ""
    secondary_metrics: List[str] = Field(default_factory=list)
    baseline: Optional[LabeledMetric] = None
    expected_result: str = ""
    minimum_sample_size: Optional[int] = None

    # Execution
    duration: str = ""
    dependencies: List[str] = Field(default_factory=list)
    status: ExperimentStatus = ExperimentStatus.HYPOTHESIS

    # Results
    result: Optional[LabeledMetric] = None
    interpretation: str = ""
    statistical_significance: Optional[str] = None
    next_action: str = ""

    # Metadata
    campaign_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str = "Simran"


class GrowthPlan(BaseModel):
    """Comprehensive growth plan with funnel, loops, and experiments."""
    plan_id: str = Field(default_factory=lambda: f"GP-{uuid.uuid4().hex[:8]}")

    # Funnel
    funnel_analysis: str = ""
    bottleneck: str = ""

    # Loops
    growth_loops: List[str] = Field(default_factory=list)
    acquisition_channels: List[str] = Field(default_factory=list)
    retention_strategies: List[str] = Field(default_factory=list)
    referral_mechanisms: List[str] = Field(default_factory=list)

    # Economics
    cac_analysis: str = ""
    ltv_analysis: str = ""

    # Experiments
    experiments: List[GrowthExperiment] = Field(default_factory=list)

    # Priorities
    priorities: List[str] = Field(default_factory=list)
    quick_wins: List[str] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str = "Simran"


# ─────────────────────────────────────────────────────────────
# SEO
# ─────────────────────────────────────────────────────────────

class TopicCluster(BaseModel):
    """A topic cluster for SEO content strategy."""
    pillar_topic: str
    subtopics: List[str] = Field(default_factory=list)
    search_intents: List[str] = Field(default_factory=list)
    target_keywords: List[str] = Field(default_factory=list)
    content_types: List[ContentType] = Field(default_factory=list)


class SEOPlan(BaseModel):
    """SEO strategy aligned with marketing objectives."""
    seo_id: str = Field(default_factory=lambda: f"SEO-{uuid.uuid4().hex[:8]}")
    audience: str = ""
    search_intents: List[str] = Field(default_factory=list)
    topic_clusters: List[TopicCluster] = Field(default_factory=list)
    keyword_targets: List[Dict[str, str]] = Field(default_factory=list)  # [{keyword, intent, volume_label, difficulty_label}]
    content_strategy: str = ""
    technical_requirements: List[str] = Field(default_factory=list)
    internal_linking_plan: str = ""
    aeo_geo_considerations: str = ""  # AI-search / AEO / GEO visibility
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str = "Dev"


# ─────────────────────────────────────────────────────────────
# Email
# ─────────────────────────────────────────────────────────────

class EmailSequenceStep(BaseModel):
    """A single step in an email sequence."""
    step: int
    delay: str = ""  # e.g., "Day 0", "Day 3", "1 week after signup"
    subject_line: str = ""
    preview_text: str = ""
    body: str = ""
    cta: str = ""
    objective: str = ""
    segment: str = ""


class EmailCampaign(BaseModel):
    """Structured email campaign or sequence."""
    email_id: str = Field(default_factory=lambda: f"EM-{uuid.uuid4().hex[:8]}")
    campaign_id: Optional[str] = None
    name: str = ""
    type: str = ""  # newsletter, onboarding, nurture, lifecycle, reactivation, announcement
    audience: str = ""
    segments: List[str] = Field(default_factory=list)
    personalization_fields: List[str] = Field(default_factory=list)
    sequence: List[EmailSequenceStep] = Field(default_factory=list)
    status: ContentStatus = ContentStatus.DRAFT
    execution_state: ExecutionState = ExecutionState.PLAN
    performance: List[LabeledMetric] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str = "Karan"


# ─────────────────────────────────────────────────────────────
# Social
# ─────────────────────────────────────────────────────────────

class SocialPost(BaseModel):
    """A social media post for a specific platform."""
    post_id: str = Field(default_factory=lambda: f"SP-{uuid.uuid4().hex[:8]}")
    platform: ChannelType
    campaign_id: Optional[str] = None
    content: str = ""
    hashtags: List[str] = Field(default_factory=list)
    media_requirements: List[str] = Field(default_factory=list)
    cta: str = ""
    audience: str = ""
    funnel_stage: FunnelStage = FunnelStage.AWARENESS
    scheduled_at: Optional[str] = None
    status: ContentStatus = ContentStatus.DRAFT
    execution_state: ExecutionState = ExecutionState.PLAN
    performance: List[LabeledMetric] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str = "Karan"


# ─────────────────────────────────────────────────────────────
# Analytics
# ─────────────────────────────────────────────────────────────

class AnalyticsReport(BaseModel):
    """Marketing analytics report with labeled metrics."""
    report_id: str = Field(default_factory=lambda: f"AR-{uuid.uuid4().hex[:8]}")
    campaign_id: Optional[str] = None
    channel: Optional[ChannelType] = None
    platform: Optional[str] = None
    date_range: str = ""

    # Metrics — always labeled
    metrics: List[LabeledMetric] = Field(default_factory=list)

    # Insights
    insights: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    anomalies: List[str] = Field(default_factory=list)

    # Funnel
    funnel_analysis: str = ""

    # Attribution
    attribution_model: str = ""
    attribution_notes: str = ""

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str = "Dev"


# ─────────────────────────────────────────────────────────────
# Quality Assessment
# ─────────────────────────────────────────────────────────────

class ContentQualityCheck(BaseModel):
    """Multi-dimensional quality evaluation for a content asset."""
    brand_consistency: float = Field(ge=0.0, le=100.0, default=0.0)
    factual_accuracy: float = Field(ge=0.0, le=100.0, default=0.0)
    audience_relevance: float = Field(ge=0.0, le=100.0, default=0.0)
    objective_alignment: float = Field(ge=0.0, le=100.0, default=0.0)
    platform_fit: float = Field(ge=0.0, le=100.0, default=0.0)
    clarity: float = Field(ge=0.0, le=100.0, default=0.0)
    cta_present: bool = False
    differentiation: float = Field(ge=0.0, le=100.0, default=0.0)
    tone_match: float = Field(ge=0.0, le=100.0, default=0.0)
    compliance: float = Field(ge=0.0, le=100.0, default=0.0)
    unsupported_claims: List[str] = Field(default_factory=list)
    grammar_issues: List[str] = Field(default_factory=list)
    ai_pattern_flags: List[str] = Field(default_factory=list)  # Detected generic AI language
    originality: float = Field(ge=0.0, le=100.0, default=0.0)
    overall_score: float = Field(ge=0.0, le=100.0, default=0.0)
    explanation: str = ""
    pass_gate: bool = False


class MarketingQualityScore(BaseModel):
    """Multi-dimensional quality assessment of the overall marketing output."""
    overall_score: float = Field(ge=0.0, le=100.0, default=0.0)

    # Dimension scores
    strategic_coherence: float = 0.0
    factual_accuracy: float = 0.0
    brand_consistency: float = 0.0
    audience_relevance: float = 0.0
    channel_fit: float = 0.0
    content_quality: float = 0.0
    conversion_orientation: float = 0.0
    research_grounding: float = 0.0
    analytics_correctness: float = 0.0
    actionability: float = 0.0
    cross_team_integration: float = 0.0

    # Issues
    quality_issues: List[str] = Field(default_factory=list)
    missing_elements: List[str] = Field(default_factory=list)

    explanation: str = ""


# ─────────────────────────────────────────────────────────────
# Audit Trail
# ─────────────────────────────────────────────────────────────

class MarketingAction(BaseModel):
    """A single auditable action in the marketing process."""
    action_id: str = Field(default_factory=lambda: f"MA-{uuid.uuid4().hex[:8]}")
    agent: str                         # "Neha", "Dev", "Karan", "Simran"
    action: str                        # e.g., "created_campaign", "generated_content", "requested_research"
    details: str = ""                  # Human-readable description

    # References
    campaign_id: Optional[str] = None
    asset_id: Optional[str] = None
    experiment_id: Optional[str] = None
    strategy_id: Optional[str] = None
    brief_id: Optional[str] = None

    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Context
    task_id: Optional[str] = None
    tool_used: Optional[str] = None
    input_summary: Optional[str] = None
    output_summary: Optional[str] = None
    authority: Optional[str] = None  # Under whose decision this action was taken


class MarketingTrace(BaseModel):
    """Complete audit trail of the marketing process."""
    actions: List[MarketingAction] = Field(default_factory=list)

    def log(self, agent: str, action: str, details: str = "", **kwargs) -> MarketingAction:
        entry = MarketingAction(agent=agent, action=action, details=details, **kwargs)
        self.actions.append(entry)
        return entry

    def get_agent_actions(self, agent: str) -> List[MarketingAction]:
        return [a for a in self.actions if a.agent == agent]

    def get_campaign_actions(self, campaign_id: str) -> List[MarketingAction]:
        return [a for a in self.actions if a.campaign_id == campaign_id]


# ─────────────────────────────────────────────────────────────
# Marketing Artifact — The Final Output
# ─────────────────────────────────────────────────────────────

class MarketingArtifact(BaseModel):
    """
    The complete output of the Marketing Team.

    This is NOT just text — it's a structured, traceable, auditable
    marketing package that can be consumed by other teams and the user.
    """
    marketing_id: str = Field(default_factory=lambda: f"MKT-{uuid.uuid4().hex[:8]}")

    # Request
    original_request: str = ""
    interpreted_objective: str = ""
    request_types: List[MarketingRequestType] = Field(default_factory=list)

    # Brief
    brief: Optional[MarketingBrief] = None

    # Brand
    brand_context: Optional[BrandContext] = None

    # Research
    research_reference_id: Optional[str] = None  # Reference to ResearchArtifact
    competitor_profiles: List[CompetitorProfile] = Field(default_factory=list)

    # Strategy
    strategy: Optional[MarketingStrategy] = None
    messaging_framework: Optional[MessagingFramework] = None

    # Campaigns
    campaigns: List[Campaign] = Field(default_factory=list)

    # Content
    content_assets: List[ContentAsset] = Field(default_factory=list)
    content_calendar: Optional[ContentCalendar] = None
    email_campaigns: List[EmailCampaign] = Field(default_factory=list)
    social_posts: List[SocialPost] = Field(default_factory=list)

    # Creative
    creative_briefs: List[CreativeBrief] = Field(default_factory=list)

    # SEO
    seo_plan: Optional[SEOPlan] = None

    # Growth
    growth_plan: Optional[GrowthPlan] = None
    experiments: List[GrowthExperiment] = Field(default_factory=list)

    # Analytics
    analytics_reports: List[AnalyticsReport] = Field(default_factory=list)

    # Cross-team
    developer_requirements: List[str] = Field(default_factory=list)
    finance_requirements: List[str] = Field(default_factory=list)
    legal_requirements: List[str] = Field(default_factory=list)

    # Quality
    quality_score: MarketingQualityScore = Field(default_factory=MarketingQualityScore)

    # Risks & Assumptions
    risks: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    dependencies_summary: List[str] = Field(default_factory=list)

    # Execution
    execution_state: ExecutionState = ExecutionState.PLAN
    approvals: Dict[str, ApprovalStatus] = Field(default_factory=dict)

    # Learning
    learnings: List[str] = Field(default_factory=list)
    next_actions: List[str] = Field(default_factory=list)

    # User-facing report (Neha's synthesized output)
    user_report: str = ""
    executive_summary: str = ""

    # Audit
    trace: MarketingTrace = Field(default_factory=MarketingTrace)

    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None

    # Helpers
    def get_campaign(self, campaign_id: str) -> Optional[Campaign]:
        return next((c for c in self.campaigns if c.campaign_id == campaign_id), None)

    def get_asset(self, asset_id: str) -> Optional[ContentAsset]:
        return next((a for a in self.content_assets if a.asset_id == asset_id), None)

    def get_experiment(self, experiment_id: str) -> Optional[GrowthExperiment]:
        return next((e for e in self.experiments if e.experiment_id == experiment_id), None)

    def get_approved_content(self) -> List[ContentAsset]:
        return [a for a in self.content_assets if a.status == ContentStatus.APPROVED]

    def get_draft_content(self) -> List[ContentAsset]:
        return [a for a in self.content_assets if a.status == ContentStatus.DRAFT]
