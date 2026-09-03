"""
End-to-end check of the monitor -> main backend alert pipeline.

Boots a stub "main backend" on :8000 that records whatever is POSTed to
/api/v1/monitor/alert, boots the monitor on :8100 with NO profile loaded,
then pushes a CMD-style tariff JSON to the monitor's tradewatch webhook and
asserts the alert was forwarded.

Run from the repo root:
    python scripts/check_monitor_alert_pipeline.py
"""
import asyncio
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx
import uvicorn
from fastapi import FastAPI, Request

received: list[dict] = []

stub = FastAPI()


@stub.post("/api/v1/monitor/alert")
async def alert(req: Request):
    body = await req.json()
    received.append({"headers": dict(req.headers), "body": body})
    return {"status": "success", "project_id": body.get("project_id") or "latest"}


async def main() -> int:
    stub_srv = uvicorn.Server(uvicorn.Config(stub, host="127.0.0.1", port=8000, log_level="warning"))

    from monitor.api.app import create_app
    from monitor.config import load_config

    cfg = load_config()
    cfg.db_path = os.path.join(tempfile.gettempdir(), "monitor_e2e_test.db")
    mon_srv = uvicorn.Server(uvicorn.Config(create_app(cfg), host="127.0.0.1", port=8100, log_level="warning"))

    t1 = asyncio.create_task(stub_srv.serve())
    t2 = asyncio.create_task(mon_srv.serve())
    await asyncio.sleep(2)

    payload = {
        "imposingCountry": "US", "imposingCountryName": "United States",
        "targetCountry": "CN", "targetCountryName": "China",
        "sector": "Semiconductors", "previousRatePercent": 10, "newRatePercent": 45,
        "delta": 35, "unit": "percent", "effectiveDate": "2026-10-01",
        "legalBasis": "Section 301", "notes": "CMD test",
    }
    ok = True
    try:
        async with httpx.AsyncClient(timeout=30) as c:
            h = await c.get("http://127.0.0.1:8100/api/monitor/health")
            print("HEALTH:", json.dumps(h.json())[:300])
            r = await c.post("http://127.0.0.1:8100/api/monitor/tradewatch/webhook", json=payload)
            print("WEBHOOK STATUS:", r.status_code)
            print(json.dumps(r.json(), indent=1))
            ok = r.status_code == 200 and r.json().get("forwarded_to_main_backend", 0) >= 1

        print("\nMAIN BACKEND RECEIVED", len(received), "alert(s)")
        for rcv in received:
            b = rcv["body"]
            print(" idempotency-key:", rcv["headers"].get("x-idempotency-key"))
            print(" ", {k: b.get(k) for k in ("alert_id", "severity", "title", "affected_entities", "project_id")})
        ok = ok and len(received) >= 1
    finally:
        stub_srv.should_exit = True
        mon_srv.should_exit = True
        await asyncio.gather(t1, t2)

    print("\nRESULT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
