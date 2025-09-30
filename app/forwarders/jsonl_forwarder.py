import json
import os
from typing import List, Dict, Any
from pathlib import Path


class JsonlForwarder:
    def __init__(self, path: str):
        self.path = path
        # Ensure directory exists
        Path(os.path.dirname(path)).mkdir(parents=True, exist_ok=True)

    def send_many(self, events: List[Dict[str, Any]]):
        with open(self.path, "a", encoding="utf-8") as f:
            for e in events:
                f.write(json.dumps(e, ensure_ascii=False) + "\n")
