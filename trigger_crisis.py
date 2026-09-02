import requests
import json
import sys

def trigger_crisis():
    url = "http://localhost:8000/api/v1/monitor/alert"
    
    payload = {
        "alert_id": "ALRT-999-CRISIS",
        "severity": "CRITICAL",
        "title": "USA increases tariffs on India by 25%",
        "description": "The US Trade Representative has announced an immediate 25% tariff increase on all electronics and textile imports from India.",
        "affected_entities": ["india_suppliers", "us_ports"],
        "project_id": "" # Will grab the latest if left empty
    }
    
    print(f"Triggering Crisis Alert to {url}...")
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print("Success! Backend has received the alert and initiated re-architecture.")
        print("Response:", response.json())
    except Exception as e:
        print("Failed to trigger alert:", str(e))

if __name__ == "__main__":
    trigger_crisis()
