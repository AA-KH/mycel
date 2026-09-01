"""
Signal type taxonomy.

Every source produces one or more signal types. Downstream processing
operates on signal types, never on source identity. This abstraction
makes adding future sources trivial.
"""

from enum import Enum


class SignalType(str, Enum):
    """Categories of disruption signals the monitor can detect."""

    SUPPLIER_DISRUPTION = "supplier_disruption"
    WEATHER_HAZARD = "weather_hazard"
    NATURAL_DISASTER = "natural_disaster"
    EARTHQUAKE = "earthquake"
    PORT_DISRUPTION = "port_disruption"
    ROAD_DISRUPTION = "road_disruption"
    TRADE_POLICY = "trade_policy"
    COMMODITY_PRICE = "commodity_price"
    GEOPOLITICAL = "geopolitical"
    REGULATORY = "regulatory"
    INFRASTRUCTURE_DAMAGE = "infrastructure_damage"
    LABOR_ACTION = "labor_action"
    FINANCIAL_DISTRESS = "financial_distress"


# Which signal types each source can produce.
# Used by the profile compiler to determine source activation.
SOURCE_SIGNAL_CAPABILITIES: dict[str, list[SignalType]] = {
    "gdelt": [
        SignalType.SUPPLIER_DISRUPTION,
        SignalType.PORT_DISRUPTION,
        SignalType.ROAD_DISRUPTION,
        SignalType.TRADE_POLICY,
        SignalType.GEOPOLITICAL,
        SignalType.REGULATORY,
        SignalType.LABOR_ACTION,
        SignalType.FINANCIAL_DISTRESS,
        SignalType.INFRASTRUCTURE_DAMAGE,
    ],
    "gdacs": [
        SignalType.NATURAL_DISASTER,
    ],
    "usgs": [
        SignalType.EARTHQUAKE,
    ],
    "openmeteo": [
        SignalType.WEATHER_HAZARD,
    ],
    "changedetection": [
        SignalType.SUPPLIER_DISRUPTION,
    ],
}


def sources_for_signal(signal: SignalType) -> list[str]:
    """Return source names that can produce the given signal type."""
    return [
        source
        for source, signals in SOURCE_SIGNAL_CAPABILITIES.items()
        if signal in signals
    ]
