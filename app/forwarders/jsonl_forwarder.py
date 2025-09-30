# app/forwarders/jsonl_forwarder.py
import json
import os
from typing import List, Dict, Any

class JsonlForwarder:
    """JSONL forwarder - appends events to a JSONL file."""
    
    def __init__(self, path: str):
        self.path = path
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

    def send_many(self, events: List[Dict[str, Any]]):
        """Append multiple events to the JSONL file."""
        with open(self.path, "a", encoding="utf-8") as f:
            for e in events:
                f.write(json.dumps(e, ensure_ascii=False) + "\n")
