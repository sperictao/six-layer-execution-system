import json
import os
import time
from functools import wraps
from pathlib import Path
from typing import Callable, Any, Optional

def get_telemetry_file() -> Path:
    env_path = os.environ.get("TELEMETRY_FILE_PATH")
    if env_path:
        return Path(env_path)
    return Path("/workspace/.trae/telemetry.jsonl")

def record_event(event_type: str, payload: dict):
    telemetry_file = get_telemetry_file()
    telemetry_file.parent.mkdir(parents=True, exist_ok=True)
    
    event = {
        "timestamp": time.time(),
        "event_type": event_type,
        "payload": payload
    }
    
    with open(telemetry_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")

def with_telemetry(event_type: str, payload_builder: Optional[Callable[[Any], dict]] = None) -> Callable:
    """
    Decorator to record telemetry events for function executions.
    
    :param event_type: The type of the telemetry event.
    :param payload_builder: Optional function to build a payload from the decorated function's result.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time
                
                payload = {}
                if payload_builder:
                    payload = payload_builder(result)
                    
                payload["elapsed_seconds"] = elapsed
                record_event(event_type, payload)
                
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                record_event(event_type, {
                    "elapsed_seconds": elapsed,
                    "status": "error",
                    "error": type(e).__name__
                })
                raise e
        return wrapper
    return decorator
