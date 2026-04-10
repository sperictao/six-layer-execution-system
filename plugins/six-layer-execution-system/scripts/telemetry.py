import json
import os
import time
from pathlib import Path

WORKSPACE = Path("/workspace")
TELEMETRY_FILE = WORKSPACE / ".trae" / "telemetry.jsonl"

def record_event(event_type: str, payload: dict):
    TELEMETRY_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    event = {
        "timestamp": time.time(),
        "event_type": event_type,
        "payload": payload
    }
    
    with open(TELEMETRY_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")
