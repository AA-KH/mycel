"""
Karan — Content Creator

Owns all marketing content production for the Marketing Team.
Produces channel-native content that respects brand voice, positioning,
audience, funnel stage, and platform conventions.

LinkedIn ≠ Instagram ≠ X ≠ email ≠ blog ≠ landing page ≠ advertisement.
Every piece of content must be tailored to its platform and context.

Karan actively detects and avoids generic AI writing patterns.
Content must be specific, brand-consistent, and audience-relevant.
"""

import json
import re
import logging
from typing import Dict, Any, List, Optional

from core.groq_engine import engine_manager
from teams.marketing.models import (
    ContentAsset, ContentType, ContentStatus, ContentVersion,
    ContentCalendar, ContentCalendarEntry, ChannelType, FunnelStage,
    SocialPost, EmailCampaign, EmailSequenceStep,
    ContentQualityCheck, BrandContext, MarketingStrategy,
    MessagingFramework, MarketingTrace, Campaign,
)

logger = logging.getLogger(__name__)

KARAN_SYSTEM_PROMPT = """You are Karan, the Content Creator at Mycel.

You are a senior marketing content specialist who creates compelling, channel-native content.
You think like a copywriter who deeply understands digital marketing, brand voice, and audience psychology.

Your responsibilities:
1. Create platform-specific content (LinkedIn ≠ Instagram ≠ X ≠ email ≠ blog)
2. Maintain brand voice and messaging consistency
3. Write content appropriate for the funnel stage
4. Create engaging hooks, CTAs, and headlines
5. Build content calendars tied to strategy
6. Produce email campaigns and sequences
7. Repurpose content across platforms while maintaining quality

RULES:
1. NEVER write generic AI content — no "revolutionary", "game-changing", "unlock your potential" unless genuinely appropriate
2. Be specific and concrete — specific examples > vague superlatives
3. Platform-native: LinkedIn is professional, X is concise, Instagram is visual, email is personal
4. Every piece needs a clear CTA connected to the marketing objective
5. Never invent testimonials, customer quotes, statistics, or case studies
6. If a claim can't be verified, mark it [UNVERIFIED] or [NEEDS PROOF]
7. Content must serve a funnel stage — don't optimize everything for conversion
8. Respect the brand's tone, vocabulary, and banned phrases

You MUST respond in valid JSON matching the schema provided."""

# Platform-specific guidelines
PLATFORM_GUIDELINES = {
    ChannelType.LINKEDIN: {
        "max_length": 3000,
        "style": "Professional, insightful, story-driven. Use line breaks for readability. Start with a hook. End with a question or CTA.",
        "avoid": "Overly casual, emoji-heavy, clickbait",
        "format": "Short paragraphs, bullet points, personal stories"
    },
    ChannelType.X: {
        "max_length": 280,
        "style": "Concise, punchy, conversational. Can be provocative or contrarian. Thread for longer content.",
        "avoid": "Walls of text, corporate speak",
        "format": "Single thought per tweet, thread structure"
    },
    ChannelType.INSTAGRAM: {
        "max_length": 2200,
        "style": "Visual-first, aspirational, community-focused. Caption supports the visual.",
        "avoid": "Text-heavy without visual context, overly salesy",
        "format": "Hook line, story/value, CTA, hashtags"
    },
    ChannelType.EMAIL: {
        "max_length": 5000,
        "style": "Personal, direct, value-first. Write as if emailing one person.",
        "avoid": "Corporate newsletters, walls of text, multiple CTAs",
        "format": "Subject line, preview text, greeting, value, CTA"
    },
    ChannelType.BLOG: {
        "max_length": 15000,
        "style": "Authoritative, educational, well-structured. SEO-aware but reader-first.",
        "avoid": "Keyword stuffing, thin content, generic summaries",
        "format": "H1, intro, H2 sections, examples, conclusion, CTA"
    },
}


class KaranContentCreator:
    """
    Karan — Content Creator Agent

    Responsibilities:
    - Create platform-native marketing content
    - Build content calendars
    - Produce email campaigns and sequences
    - Repurpose content across platforms
    - Check content quality and brand voice
    """

    def __init__(self, trace: Optional[MarketingTrace] = None):
        self.name = "Karan"
        self.role = "Content Creator"
        self.trace = trace or MarketingTrace()
        self._engine = engine_manager.get_engine("marketing")

    async def create_content(self, content_type: ContentType,
                             platform: Optional[ChannelType],
                             brief: str,
                             brand_context: Optional[BrandContext] = None,
                             strategy: Optional[MarketingStrategy] = None,
                             campaign: Optional[Campaign] = None,
                             funnel_stage: FunnelStage = FunnelStage.AWARENESS) -> ContentAsset:
        """
        Create a single piece of marketing content.
        Channel-native, brand-consistent, funnel-aware.
        """
        self.trace.log(
            agent=self.name,
            action="creating_content",
            details=f"Type: {content_type.value}, Platform: {platform.value if platform else 'none'}, "
                    f"Funnel: {funnel_stage.value}",
            campaign_id=campaign.campaign_id if campaign else None
        )

        # Build context
        brand_info = self._format_brand_context(brand_context)
        platform_info = self._format_platform_guidelines(platform)
        messaging_info = self._format_messaging(strategy)
        funnel_info = self._format_funnel_guidance(funnel_stage)

        prompt = f"""Create a {content_type.value.replace('_', ' ')} for {platform.value if platform else 'general use'}.

BRIEF: {brief}

{brand_info}
{messaging_info}
{platform_info}
{funnel_info}

{f'CAMPAIGN: {campaign.name} — {campaign.objective}' if campaign else ''}
{f'CAMPAIGN MESSAGING: {campaign.messaging}' if campaign and campaign.messaging else ''}

Return JSON:
{{
    "headline": "Attention-grabbing headline/title",
    "hook": "Opening hook that stops the scroll",
    "content": "The full content piece",
    "cta": "Clear call to action",
    "hashtags": ["hashtag1", "hashtag2"],
    "media_requirements": ["Description of visual/media needed"],
    "topic": "Core topic",
    "audience_addressed": "Who this content speaks to"
}}

IMPORTANT:
- Be SPECIFIC — use concrete examples, numbers, scenarios
- Avoid generic AI writing: no "revolutionary", "game-changing", "leverage", "streamline" unless genuinely appropriate
- Match the platform's native format and conventions
- The hook must earn the reader's attention — don't be generic
- CTA must connect to a specific action
- If any claim is unverified, mark it [NEEDS PROOF]"""

        try:
            messages = [
                {"role": "system", "content": KARAN_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
            response = await self._engine.chat_completion(
                model="qwen/qwen3.8-27b",
                messages=messages,
                temperature=0.7,
                max_tokens=3000
            )
            raw = response.choices[0].message.content or ""
            raw = re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL).strip()

            json_match = re.search(r'\{.*\}', raw, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON in content response")

            data = json.loads(json_match.group())

            asset = ContentAsset(
                content_type=content_type,
                platform=platform,
                campaign_id=campaign.campaign_id if campaign else None,
                topic=data.get("topic", ""),
                audience=data.get("audience_addressed", ""),
                funnel_stage=funnel_stage,
                headline=data.get("headline", ""),
                hook=data.get("hook", ""),
                content=data.get("content", ""),
                cta=data.get("cta", ""),
                hashtags=data.get("hashtags", []),
                media_requirements=data.get("media_requirements", []),
                message_source=campaign.messaging if campaign else "",
                status=ContentStatus.DRAFT,
                versions=[ContentVersion(
                    version=1,
                    content=data.get("content", ""),
                    created_by=self.name,
                )],
            )

            self.trace.log(
                agent=self.name,
                action="content_created",
                details=f"Asset {asset.asset_id}: {content_type.value} "
                        f"for {platform.value if platform else 'general'}",
                asset_id=asset.asset_id,
                campaign_id=campaign.campaign_id if campaign else None
            )

            return asset

        except Exception as e:
            logger.error(f"[Karan] Content creation failed: {e}")
            return ContentAsset(
                content_type=content_type,
                platform=platform,
                content=f"Content generation failed: {str(e)[:100]}",
                status=ContentStatus.DRAFT,
            )

    async def create_social_batch(self, platforms: List[ChannelType],
                                  messaging: MessagingFramework,
                                  campaign: Optional[Campaign] = None,
                                  brand_context: Optional[BrandContext] = None,
                                  count_per_platform: int = 3) -> List[ContentAsset]:
        """Create multiple social posts across platforms from a single messaging framework."""
        self.trace.log(
            agent=self.name,
            action="creating_social_batch",
            details=f"Batch: {len(platforms)} platforms × {count_per_platform} posts"
        )

        assets = []
        for platform in platforms:
            for i in range(count_per_platform):
                funnel = [FunnelStage.AWARENESS, FunnelStage.CONSIDERATION, FunnelStage.CONVERSION]
                stage = funnel[i % len(funnel)]

                brief = (
                    f"Create post #{i+1} for {platform.value}. "
                    f"Key message: {messaging.key_messages[i % len(messaging.key_messages)] if messaging.key_messages else messaging.value_proposition}. "
                    f"Funnel stage: {stage.value}. "
                    f"Value proposition: {messaging.value_proposition}"
                )

                asset = await self.create_content(
                    content_type=ContentType.SOCIAL_POST,
                    platform=platform,
                    brief=brief,
                    brand_context=brand_context,
                    campaign=campaign,
                    funnel_stage=stage,
                )
                assets.append(asset)

        self.trace.log(
            agent=self.name,
            action="social_batch_complete",
            details=f"Created {len(assets)} social posts across {len(platforms)} platforms"
        )

        return assets

    async def create_email_campaign(self, campaign_type: str,
                                    audience: str,
                                    messaging: Optional[MessagingFramework] = None,
                                    brand_context: Optional[BrandContext] = None,
                                    num_steps: int = 5) -> EmailCampaign:
        """Create a structured email campaign with sequence steps."""
        self.trace.log(
            agent=self.name,
            action="creating_email_campaign",
            details=f"Email campaign: {campaign_type}, {num_steps} steps"
        )

        messaging_info = ""
        if messaging:
            messaging_info = f"""
Value Proposition: {messaging.value_proposition}
Key Messages: {messaging.key_messages}
Proof Points: {messaging.proof_points}
Tone: {messaging.tone_guidelines}
"""

        brand_info = self._format_brand_context(brand_context)

        prompt = f"""Create a {campaign_type} email campaign with {num_steps} emails.

AUDIENCE: {audience}
TYPE: {campaign_type} (e.g., onboarding, nurture, newsletter, launch, reactivation)

{messaging_info}
{brand_info}

Return JSON:
{{
    "name": "Campaign name",
    "sequence": [
        {{
            "step": 1,
            "delay": "Day 0",
            "subject_line": "Subject line",
            "preview_text": "Preview text",
            "body": "Full email body",
            "cta": "Call to action",
            "objective": "What this email achieves"
        }}
    ],
    "segments": ["segment1"],
    "personalization_fields": ["first_name", "company"]
}}

IMPORTANT:
- Write as if emailing ONE person — not a corporate blast
- Each email should have ONE clear objective and ONE CTA
- Subject lines must earn the open — no clickbait
- Sequence should have logical progression
- Never invent testimonials or statistics"""

        try:
            messages = [
                {"role": "system", "content": KARAN_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
            response = await self._engine.chat_completion(
                model="qwen/qwen3.8-27b",
                messages=messages,
                temperature=0.6,
                max_tokens=5000
            )
            raw = response.choices[0].message.content or ""
            raw = re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL).strip()

            json_match = re.search(r'\{.*\}', raw, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON in email response")

            data = json.loads(json_match.group())

            steps = []
            for s in data.get("sequence", []):
                steps.append(EmailSequenceStep(
                    step=s.get("step", len(steps) + 1),
                    delay=s.get("delay", ""),
                    subject_line=s.get("subject_line", ""),
                    preview_text=s.get("preview_text", ""),
                    body=s.get("body", ""),
                    cta=s.get("cta", ""),
                    objective=s.get("objective", ""),
                ))

            email_campaign = EmailCampaign(
                name=data.get("name", f"{campaign_type.title()} Campaign"),
                type=campaign_type,
                audience=audience,
                segments=data.get("segments", []),
                personalization_fields=data.get("personalization_fields", []),
                sequence=steps,
                status=ContentStatus.DRAFT,
            )

            self.trace.log(
                agent=self.name,
                action="email_campaign_created",
                details=f"Email {email_campaign.email_id}: {len(steps)} steps"
            )

            return email_campaign

        except Exception as e:
            logger.error(f"[Karan] Email campaign creation failed: {e}")
            return EmailCampaign(name=f"{campaign_type} Campaign", type=campaign_type, audience=audience)

    async def create_content_calendar(self, strategy: MarketingStrategy,
                                      campaign: Optional[Campaign] = None,
                                      days: int = 30) -> ContentCalendar:
        """Create a structured content calendar connected to strategy."""
        self.trace.log(
            agent=self.name,
            action="creating_content_calendar",
            details=f"Calendar: {days} days, channels: {[c.value for c in strategy.primary_channels]}"
        )

        channels_info = ""
        for cs in strategy.channel_strategies:
            channels_info += f"\n- {cs.channel.value}: frequency={cs.frequency}, types={[ct.value for ct in cs.content_types]}"

        prompt = f"""Create a {days}-day content calendar.

STRATEGY:
- Objective: {strategy.objective}
- Audience: {strategy.audience}
- Positioning: {strategy.positioning}
- Primary Channels: {[c.value for c in strategy.primary_channels]}
- Channel Details: {channels_info}
- Campaign Themes: {strategy.campaign_themes}

{f'MESSAGING PILLARS: {strategy.messaging_framework.messaging_pillars}' if strategy.messaging_framework else ''}
{f'KEY MESSAGES: {strategy.messaging_framework.key_messages}' if strategy.messaging_framework else ''}

Return JSON:
{{
    "entries": [
        {{
            "date": "Day 1",
            "platform": "linkedin|x|instagram|email|blog",
            "content_type": "social_post|blog_post|newsletter|email_campaign",
            "objective": "What this content achieves",
            "audience": "Target for this piece",
            "topic": "Specific topic",
            "hook": "Opening hook idea",
            "cta": "Call to action",
            "asset_requirement": "What visual/media is needed",
            "funnel_stage": "awareness|consideration|conversion|retention|advocacy"
        }}
    ]
}}

IMPORTANT:
- Connect every entry to the strategy and business objective
- Vary content types and funnel stages
- Don't repeat the same topic/angle consecutively
- Include a mix of funnel stages
- Be specific about topics — not "post about product" but "post about how [specific feature] solves [specific problem]"
- Respect channel frequency from strategy"""

        try:
            messages = [
                {"role": "system", "content": KARAN_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
            response = await self._engine.chat_completion(
                model="qwen/qwen3.8-27b",
                messages=messages,
                temperature=0.5,
                max_tokens=5000
            )
            raw = response.choices[0].message.content or ""
            raw = re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL).strip()

            json_match = re.search(r'\{.*\}', raw, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON in calendar response")

            data = json.loads(json_match.group())

            entries = []
            for e in data.get("entries", []):
                try:
                    platform = ChannelType(e.get("platform", "other"))
                except ValueError:
                    platform = ChannelType.OTHER

                try:
                    content_type = ContentType(e.get("content_type", "social_post"))
                except ValueError:
                    content_type = ContentType.SOCIAL_POST

                try:
                    funnel = FunnelStage(e.get("funnel_stage", "awareness"))
                except ValueError:
                    funnel = FunnelStage.AWARENESS

                entries.append(ContentCalendarEntry(
                    date=e.get("date", ""),
                    platform=platform,
                    content_type=content_type,
                    objective=e.get("objective", ""),
                    audience=e.get("audience", ""),
                    topic=e.get("topic", ""),
                    hook=e.get("hook", ""),
                    cta=e.get("cta", ""),
                    asset_requirement=e.get("asset_requirement", ""),
                    campaign_id=campaign.campaign_id if campaign else None,
                    funnel_stage=funnel,
                ))

            calendar = ContentCalendar(
                strategy_id=strategy.strategy_id,
                campaign_id=campaign.campaign_id if campaign else None,
                entries=entries,
            )

            self.trace.log(
                agent=self.name,
                action="content_calendar_created",
                details=f"Calendar {calendar.calendar_id}: {len(entries)} entries over {days} days"
            )

            return calendar

        except Exception as e:
            logger.error(f"[Karan] Content calendar creation failed: {e}")
            return ContentCalendar(strategy_id=strategy.strategy_id)

    async def check_content_quality(self, content: str,
                                    brand_context: Optional[BrandContext] = None,
                                    content_type: Optional[ContentType] = None,
                                    platform: Optional[ChannelType] = None) -> ContentQualityCheck:
        """Evaluate content quality across multiple dimensions."""
        self.trace.log(
            agent=self.name,
            action="checking_quality",
            details=f"Quality check on {len(content)} char content"
        )

        # AI pattern detection
        ai_patterns = [
            "revolutionary", "game-changing", "unlock your potential",
            "in today's fast-paced world", "dive into", "dive deep",
            "elevate your", "supercharge", "unleash", "seamlessly",
            "cutting-edge", "paradigm shift", "synergy", "best-in-class",
            "world-class", "next-level", "disruptive",
        ]
        detected_patterns = [p for p in ai_patterns if p.lower() in content.lower()]

        # Banned phrase detection
        banned_detected = []
        if brand_context and brand_context.banned_phrases:
            banned_detected = [p for p in brand_context.banned_phrases if p.lower() in content.lower()]

        # Basic quality checks
        has_cta = any(word in content.lower() for word in [
            "sign up", "try", "start", "learn more", "get", "join",
            "subscribe", "download", "register", "book", "schedule",
            "click", "visit", "check out"
        ])

        # Unsupported claims detection
        claim_patterns = [
            r'\d+%\s+(?:increase|growth|improvement|reduction)',
            r'#1\s+',
            r'best\s+in\s+(?:class|market|industry)',
            r'guaranteed',
            r'proven\s+to',
        ]
        unsupported = []
        for pattern in claim_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                unsupported.append(f"Potential unsupported claim: '{re.search(pattern, content, re.IGNORECASE).group()}'")

        # Score calculation
        scores = {
            "brand_consistency": 80.0 - (len(banned_detected) * 20),
            "factual_accuracy": 80.0 - (len(unsupported) * 15),
            "audience_relevance": 70.0,  # Would need audience context for real scoring
            "objective_alignment": 70.0,
            "platform_fit": 75.0,
            "clarity": 75.0,
            "differentiation": 70.0 - (len(detected_patterns) * 5),
            "tone_match": 80.0 - (len(banned_detected) * 10),
            "compliance": 90.0 - (len(unsupported) * 10),
            "originality": 80.0 - (len(detected_patterns) * 8),
        }

        overall = sum(scores.values()) / len(scores)
        pass_gate = overall >= 60.0 and len(unsupported) == 0

        quality = ContentQualityCheck(
            brand_consistency=max(0, scores["brand_consistency"]),
            factual_accuracy=max(0, scores["factual_accuracy"]),
            audience_relevance=scores["audience_relevance"],
            objective_alignment=scores["objective_alignment"],
            platform_fit=scores["platform_fit"],
            clarity=scores["clarity"],
            cta_present=has_cta,
            differentiation=max(0, scores["differentiation"]),
            tone_match=max(0, scores["tone_match"]),
            compliance=max(0, scores["compliance"]),
            unsupported_claims=unsupported,
            grammar_issues=[],
            ai_pattern_flags=detected_patterns,
            originality=max(0, scores["originality"]),
            overall_score=max(0, overall),
            explanation=f"Score: {overall:.0f}/100. "
                        f"AI patterns: {len(detected_patterns)}. "
                        f"Unsupported claims: {len(unsupported)}. "
                        f"CTA: {'Yes' if has_cta else 'Missing'}.",
            pass_gate=pass_gate,
        )

        self.trace.log(
            agent=self.name,
            action="quality_checked",
            details=f"Quality: {overall:.0f}/100, Gate: {'PASS' if pass_gate else 'FAIL'}"
        )

        return quality

    # ─────────────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────────────

    def _format_brand_context(self, brand_context: Optional[BrandContext]) -> str:
        if not brand_context:
            return "BRAND: Not yet established"
        bc = brand_context
        parts = [f"BRAND CONTEXT:"]
        if bc.name:
            parts.append(f"- Name: {bc.name}")
        if bc.tone:
            parts.append(f"- Tone: {bc.tone}")
        if bc.voice:
            parts.append(f"- Voice: {bc.voice}")
        if bc.positioning:
            parts.append(f"- Positioning: {bc.positioning}")
        if bc.value_propositions:
            parts.append(f"- Value Props: {bc.value_propositions[:3]}")
        if bc.banned_phrases:
            parts.append(f"- BANNED phrases: {bc.banned_phrases}")
        if bc.preferred_phrases:
            parts.append(f"- Preferred phrases: {bc.preferred_phrases}")
        return "\n".join(parts)

    def _format_platform_guidelines(self, platform: Optional[ChannelType]) -> str:
        if not platform or platform not in PLATFORM_GUIDELINES:
            return ""
        g = PLATFORM_GUIDELINES[platform]
        return f"""PLATFORM GUIDELINES ({platform.value}):
- Max length: {g['max_length']} chars
- Style: {g['style']}
- Avoid: {g['avoid']}
- Format: {g['format']}"""

    def _format_messaging(self, strategy: Optional[MarketingStrategy]) -> str:
        if not strategy or not strategy.messaging_framework:
            return ""
        mf = strategy.messaging_framework
        return f"""MESSAGING:
- Value Proposition: {mf.value_proposition}
- Key Messages: {mf.key_messages[:3]}
- Pillars: {mf.messaging_pillars[:3]}
- Tone: {mf.tone_guidelines}"""

    def _format_funnel_guidance(self, stage: FunnelStage) -> str:
        guidance = {
            FunnelStage.AWARENESS: "FUNNEL: Awareness — educate, build problem awareness, thought leadership. Don't sell yet.",
            FunnelStage.CONSIDERATION: "FUNNEL: Consideration — compare, provide proof, case studies, explain product value.",
            FunnelStage.CONVERSION: "FUNNEL: Conversion — offer, demo CTA, address objections, create urgency.",
            FunnelStage.RETENTION: "FUNNEL: Retention — educate on features, deepen value, build loyalty.",
            FunnelStage.ADVOCACY: "FUNNEL: Advocacy — encourage sharing, referrals, community, testimonials.",
        }
        return guidance.get(stage, "")
