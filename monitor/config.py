"""
Configuration for the Mycel monitoring subsystem.

All external dependencies (API keys, URLs, models) are configured through
environment variables. Never hard-code secrets.
"""

from __future__ import annotations

from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class MonitorConfig(BaseSettings):
    """Monitoring subsystem configuration. Loaded from environment variables."""

    model_config = {"env_prefix": "MYCEL_MONITOR_", "env_file": ".env", "extra": "ignore"}

    # ── Application ──
    app_name: str = "Mycel Monitor"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8100

    # ── Database ──
    db_path: str = "monitor_data.db"

    # ── LLM ──
    llm_provider: str = "groq"  # groq, openai, google
    llm_model: str = "openai/gpt-oss-120b"
    llm_api_key: Optional[str] = Field(default=None, alias="GROQ_API_KEY")
    llm_api_key_fallback: Optional[str] = Field(default=None, alias="GROQ_API_KEY_2")
    llm_max_tokens: int = 1024
    llm_temperature: float = 0.1

    # ── Alert Dispatch ──
    alert_webhook_url: Optional[str] = None
    alert_webhook_timeout: int = 10
    alert_webhook_max_retries: int = 3

    # ── Source: GDELT ──
    gdelt_enabled: bool = True
    gdelt_base_url: str = "https://api.gdeltproject.org/api/v2/doc/doc"
    gdelt_min_request_interval: float = 6.0  # seconds between requests
    gdelt_max_records: int = 75
    gdelt_timeout: int = 30

    # ── Source: GDACS ──
    gdacs_enabled: bool = True
    gdacs_base_url: str = "https://www.gdacs.org/gdacsapi/api"
    gdacs_timeout: int = 30

    # ── Source: USGS ──
    usgs_enabled: bool = True
    usgs_feed_url: str = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary"
    usgs_query_url: str = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    usgs_min_magnitude: float = 4.0
    usgs_timeout: int = 20

    # ── Source: Open-Meteo ──
    openmeteo_enabled: bool = True
    openmeteo_base_url: str = "https://api.open-meteo.com/v1/forecast"
    openmeteo_batch_size: int = 50  # Locations per request (conservative)
    openmeteo_timeout: int = 20

    # ── Source: changedetection.io ──
    changedetection_enabled: bool = False
    changedetection_url: Optional[str] = None
    changedetection_api_key: Optional[str] = None
    changedetection_timeout: int = 15

    # ── Source: WTO Timeseries API ──
    wto_enabled: bool = True
    wto_api_key: Optional[str] = Field(default=None, alias="WTO_API_KEY")
    wto_base_url: str = "https://api.wto.org/timeseries/v1"
    wto_timeout: int = 30
    wto_min_request_interval: float = 1.1  # Rate limit: 1 req/sec

    # ── Source: Global Trade Alert ──
    global_trade_alert_enabled: bool = True
    gta_api_url: Optional[str] = Field(default=None, alias="GTA_API_URL")
    gta_api_key: Optional[str] = Field(default=None, alias="GTA_API_KEY")
    gta_timeout: int = 30

    # ── Source: WITS / World Bank ──
    wits_enabled: bool = True
    wits_base_url: str = "https://wits.worldbank.org/API/V1/SDMX/V21/rest/data"
    wits_timeout: int = 30

    # ── Scheduling ──
    default_poll_interval: int = 3600  # 1 hour
    gdelt_poll_interval: int = 900  # 15 min
    gdacs_poll_interval: int = 600  # 10 min
    usgs_poll_interval: int = 300  # 5 min
    openmeteo_poll_interval: int = 1800  # 30 min
    wto_poll_interval: int = 86400  # 24h — periodic state observer
    gta_poll_interval: int = 86400  # 24h
    wits_poll_interval: int = 86400  # 24h — periodic state observer

    # ── Severity Thresholds ──
    # Impact score thresholds for severity classification
    severity_critical_threshold: float = 0.75
    severity_warning_threshold: float = 0.50
    severity_watch_threshold: float = 0.25

    # Confidence thresholds
    confidence_high: float = 0.7
    confidence_medium: float = 0.4

    # ── Deduplication ──
    dedup_time_window_hours: int = 48
    dedup_simhash_threshold: int = 3  # Max bit difference for near-duplicate

    # ── Alert Fatigue ──
    alert_cooldown_minutes: int = 30
    max_alerts_per_situation_per_hour: int = 2


def load_config() -> MonitorConfig:
    """Load configuration from environment."""
    return MonitorConfig()
