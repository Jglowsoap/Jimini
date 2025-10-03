import json
import os
from typing import List, Dict, Any
from pathlib import Path
from app.forwarders.base import ResilientForwarder


class JsonlForwarder(ResilientForwarder):
    def __init__(self, path: str):
        super().__init__("jsonl", max_retries=1)  # File operations rarely benefit from retries
        self.path = path
        # Ensure directory exists
        Path(os.path.dirname(path)).mkdir(parents=True, exist_ok=True)

    def _send_batch(self, events: List[Dict[str, Any]]):
        """Write events to JSONL file"""
        with open(self.path, "a", encoding="utf-8") as f:
            for e in events:
                f.write(json.dumps(e, ensure_ascii=False) + "\n")
