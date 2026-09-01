import asyncio
import json
from datetime import datetime, timezone
import time

from monitor.config import MonitorConfig
from monitor.scheduling.orchestrator import Orchestrator
from monitor.models.events import CanonicalEvent
from monitor.models.signals import SignalType

async def run_simulation():
    print("🟢 [API INIT] Initializing Monitoring System Backend API...")
    config = MonitorConfig(db_path=":memory:")
    orch = Orchestrator(config)
    orch.initialize()
    
    print("🟢 [API CONFIG] Loading Supply Chain Architecture Profile...")
    with open("monitor/fixtures/sample_network.json", "r") as f:
        arch_data = json.load(f)
        
    profile = await orch.load_profile_from_architecture(arch_data)
    print(f"   => Profile Loaded: {profile.total_entities} entities, {profile.total_locations} locations actively monitored.\n")
    
    print("⏳ [MONITORING FEED] Simulating normal activity (Noise)...")
    noise_event = CanonicalEvent(
        event_id="event_noise_1",
        source="gdelt",
        event_time=datetime.now(timezone.utc),
        signal_type=SignalType.SUPPLIER_DISRUPTION,
        title="Unrelated factory shutdown reported in Toronto, Canada",
        description="A completely unrelated plant closed due to local issues.",
        countries=["CAN"],
        confidence=0.8,
        source_trust=0.9
    )
    situation1 = await orch.process_event(noise_event)
    print(f"   => Event processed: 'Unrelated factory shutdown in Canada'")
    print(f"   => Is relevant to our network? {'Yes' if situation1 else 'No'}\n")
    
    time.sleep(2)
    
    print("⚠️  [MONITORING FEED] DISRUPTION DETECTED!")
    print("   => Event: Massive industrial fire reported by news sources.")
    disruption_event = CanonicalEvent(
        event_id="event_disruption_1",
        source="gdelt",
        event_time=datetime.now(timezone.utc),
        signal_type=SignalType.SUPPLIER_DISRUPTION,
        title="Massive industrial fire halts operations at Gujarat Graphite Works plant in Ahmedabad",
        description="Operations suspended indefinitely following massive blaze at the Gujarat Graphite Works manufacturing facility.",
        countries=["IND"],
        raw_entities=["Gujarat Graphite Works", "Ahmedabad"],
        confidence=0.9,
        source_trust=0.9
    )
    
    situation2 = await orch.process_event(disruption_event)
    print(f"   => Event processed: '{disruption_event.title}'")
    print(f"   => Is relevant to our network? {'Yes' if situation2 else 'No'}\n")
    
    time.sleep(1)
    
    print("🚨 [API ALERT] Polling /api/monitor/alerts/latest ...")
    latest_alert = orch.alert_manager.latest_alert()
    
    if latest_alert:
        print("\n==================================================")
        print(f"💥 ALERT NOTIFICATION: {latest_alert.severity.value.upper()} SEVERITY")
        print("==================================================")
        print(f"TITLE: {latest_alert.title}")
        print(f"SITUATION ID: {latest_alert.situation_id}")
        print(f"DESCRIPTION: {latest_alert.description}")
        print("==================================================\n")
    else:
        print("   => No alerts triggered.")

if __name__ == "__main__":
    asyncio.run(run_simulation())
