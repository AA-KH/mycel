"""
Provider Abstractions

External integration abstractions for social media, email, analytics, and SEO.
All follow the same pattern: abstract base → concrete implementation → graceful degradation.

Initial implementations use LocalStorageProvider which stores outputs locally
when no external integration is configured, ensuring the system works
without any paid services.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# Result Models
# ─────────────────────────────────────────────────────────────

class PublishResult(BaseModel):
    """Result of a social media publish operation."""
    success: bool = False
    post_id: Optional[str] = None
    platform: str = ""
    url: Optional[str] = None
    error: Optional[str] = None
    provider: str = "local"
    published_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SendResult(BaseModel):
    """Result of an email send operation."""
    success: bool = False
    campaign_id: Optional[str] = None
    recipients: int = 0
    error: Optional[str] = None
    provider: str = "local"
    sent_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AnalyticsResult(BaseModel):
    """Result of an analytics query."""
    success: bool = False
    metrics: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    provider: str = "local"
    queried_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class KeywordResult(BaseModel):
    """Result of an SEO keyword query."""
    keyword: str = ""
    volume_estimate: str = ""
    difficulty_estimate: str = ""
    related_keywords: List[str] = Field(default_factory=list)
    provider: str = "local"


# ─────────────────────────────────────────────────────────────
# Abstract Providers
# ─────────────────────────────────────────────────────────────

class SocialProvider(ABC):
    """Abstract interface for social media publishing."""

    @abstractmethod
    async def publish(self, platform: str, content: str,
                      media_urls: Optional[List[str]] = None,
                      **kwargs) -> PublishResult:
        pass

    @abstractmethod
    async def schedule(self, platform: str, content: str,
                       scheduled_at: datetime,
                       media_urls: Optional[List[str]] = None,
                       **kwargs) -> PublishResult:
        pass

    @abstractmethod
    async def get_analytics(self, post_id: str,
                            platform: str) -> AnalyticsResult:
        pass


class EmailProvider(ABC):
    """Abstract interface for email campaign sending."""

    @abstractmethod
    async def send_campaign(self, campaign_name: str,
                            recipients: List[str],
                            subject: str, body: str,
                            **kwargs) -> SendResult:
        pass

    @abstractmethod
    async def send_sequence_step(self, sequence_id: str,
                                 step: int,
                                 recipients: List[str],
                                 subject: str, body: str,
                                 **kwargs) -> SendResult:
        pass

    @abstractmethod
    async def get_analytics(self, campaign_id: str) -> AnalyticsResult:
        pass


class AnalyticsProvider(ABC):
    """Abstract interface for marketing analytics."""

    @abstractmethod
    async def get_metrics(self, source: str,
                          date_range: Optional[str] = None,
                          metrics: Optional[List[str]] = None) -> AnalyticsResult:
        pass

    @abstractmethod
    async def get_funnel_data(self, funnel_id: Optional[str] = None) -> AnalyticsResult:
        pass


class SEOProvider(ABC):
    """Abstract interface for SEO data."""

    @abstractmethod
    async def get_keywords(self, topic: str,
                           limit: int = 20) -> List[KeywordResult]:
        pass

    @abstractmethod
    async def get_ranking(self, keyword: str,
                          domain: Optional[str] = None) -> Dict[str, Any]:
        pass


# ─────────────────────────────────────────────────────────────
# Local Storage Implementations (Default — No External APIs)
# ─────────────────────────────────────────────────────────────

class LocalSocialProvider(SocialProvider):
    """
    Local social provider — stores posts locally instead of publishing.
    Used when no external social media API is configured.
    """

    def __init__(self):
        self._posts: List[Dict[str, Any]] = []
        self._post_counter = 0

    async def publish(self, platform: str, content: str,
                      media_urls: Optional[List[str]] = None,
                      **kwargs) -> PublishResult:
        self._post_counter += 1
        post_id = f"local_post_{self._post_counter}"

        self._posts.append({
            "post_id": post_id,
            "platform": platform,
            "content": content,
            "media_urls": media_urls or [],
            "status": "stored_locally",
            "created_at": datetime.now(timezone.utc).isoformat(),
            **kwargs,
        })

        logger.info(f"[LocalSocial] Stored post {post_id} for {platform} "
                     f"({len(content)} chars)")

        return PublishResult(
            success=True,
            post_id=post_id,
            platform=platform,
            provider="local",
        )

    async def schedule(self, platform: str, content: str,
                       scheduled_at: datetime,
                       media_urls: Optional[List[str]] = None,
                       **kwargs) -> PublishResult:
        result = await self.publish(platform, content, media_urls, **kwargs)
        if result.post_id:
            # Mark as scheduled
            for post in self._posts:
                if post["post_id"] == result.post_id:
                    post["scheduled_at"] = scheduled_at.isoformat()
                    post["status"] = "scheduled_locally"
        return result

    async def get_analytics(self, post_id: str,
                            platform: str) -> AnalyticsResult:
        return AnalyticsResult(
            success=True,
            metrics={"note": "Local provider — no real analytics available"},
            provider="local",
        )

    def get_stored_posts(self) -> List[Dict[str, Any]]:
        return self._posts


class LocalEmailProvider(EmailProvider):
    """
    Local email provider — stores campaigns locally instead of sending.
    Used when no external email API is configured.
    """

    def __init__(self):
        self._campaigns: List[Dict[str, Any]] = []
        self._campaign_counter = 0

    async def send_campaign(self, campaign_name: str,
                            recipients: List[str],
                            subject: str, body: str,
                            **kwargs) -> SendResult:
        self._campaign_counter += 1
        campaign_id = f"local_campaign_{self._campaign_counter}"

        self._campaigns.append({
            "campaign_id": campaign_id,
            "name": campaign_name,
            "recipients": recipients,
            "subject": subject,
            "body": body[:500],
            "status": "stored_locally",
            "created_at": datetime.now(timezone.utc).isoformat(),
        })

        logger.info(f"[LocalEmail] Stored campaign {campaign_id}: {subject}")

        return SendResult(
            success=True,
            campaign_id=campaign_id,
            recipients=len(recipients),
            provider="local",
        )

    async def send_sequence_step(self, sequence_id: str,
                                 step: int,
                                 recipients: List[str],
                                 subject: str, body: str,
                                 **kwargs) -> SendResult:
        return await self.send_campaign(
            f"Sequence {sequence_id} Step {step}",
            recipients, subject, body, **kwargs
        )

    async def get_analytics(self, campaign_id: str) -> AnalyticsResult:
        return AnalyticsResult(
            success=True,
            metrics={"note": "Local provider — no real analytics available"},
            provider="local",
        )


class LocalAnalyticsProvider(AnalyticsProvider):
    """Local analytics — returns framework data, not real metrics."""

    async def get_metrics(self, source: str,
                          date_range: Optional[str] = None,
                          metrics: Optional[List[str]] = None) -> AnalyticsResult:
        return AnalyticsResult(
            success=True,
            metrics={
                "source": source,
                "note": "Local provider — no real metrics. All values are UNKNOWN.",
                "data_label": "unknown",
            },
            provider="local",
        )

    async def get_funnel_data(self, funnel_id: Optional[str] = None) -> AnalyticsResult:
        return AnalyticsResult(
            success=True,
            metrics={
                "note": "Local provider — funnel data not available",
                "data_label": "unknown",
            },
            provider="local",
        )


class LocalSEOProvider(SEOProvider):
    """Local SEO — returns framework/estimate data."""

    async def get_keywords(self, topic: str,
                           limit: int = 20) -> List[KeywordResult]:
        # Generate basic keyword ideas from the topic
        words = topic.lower().split()
        keywords = [
            KeywordResult(
                keyword=topic,
                volume_estimate="ESTIMATE: unknown",
                difficulty_estimate="ESTIMATE: unknown",
                related_keywords=[f"{topic} guide", f"best {topic}", f"{topic} for beginners"],
                provider="local",
            )
        ]
        return keywords

    async def get_ranking(self, keyword: str,
                          domain: Optional[str] = None) -> Dict[str, Any]:
        return {
            "keyword": keyword,
            "domain": domain,
            "ranking": "UNKNOWN — local provider",
            "provider": "local",
        }


# ─────────────────────────────────────────────────────────────
# Provider Registry
# ─────────────────────────────────────────────────────────────

class ProviderRegistry:
    """
    Central registry for marketing providers.
    Defaults to local providers; can be swapped for real integrations.
    """

    def __init__(self):
        self._social: SocialProvider = LocalSocialProvider()
        self._email: EmailProvider = LocalEmailProvider()
        self._analytics: AnalyticsProvider = LocalAnalyticsProvider()
        self._seo: SEOProvider = LocalSEOProvider()

    @property
    def social(self) -> SocialProvider:
        return self._social

    @property
    def email(self) -> EmailProvider:
        return self._email

    @property
    def analytics(self) -> AnalyticsProvider:
        return self._analytics

    @property
    def seo(self) -> SEOProvider:
        return self._seo

    def set_social(self, provider: SocialProvider) -> None:
        self._social = provider

    def set_email(self, provider: EmailProvider) -> None:
        self._email = provider

    def set_analytics(self, provider: AnalyticsProvider) -> None:
        self._analytics = provider

    def set_seo(self, provider: SEOProvider) -> None:
        self._seo = provider


# Module-level singleton
provider_registry = ProviderRegistry()
