import json
import ssl
import urllib.request
import base64
from typing import List, Dict, Any, Tuple


class ElasticForwarder:
    def __init__(self, url: str, auth: Tuple[str, str] = None, verify: bool = True):
        self.url = url
        self.auth = auth
        self.ctx = None if verify else ssl._create_unverified_context()

    def send_many(self, events: List[Dict[str, Any]]):
        # Bulk index (one-at-a-time is fine to start; Phase 4: bulk API)
        for e in events:
            data = json.dumps(e).encode("utf-8")
            
            headers = {"Content-Type": "application/json"}
            if self.auth and self.auth[0] and self.auth[1]:
                token = base64.b64encode(f"{self.auth[0]}:{self.auth[1]}".encode()).decode()
                headers["Authorization"] = f"Basic {token}"
                
            req = urllib.request.Request(
                url=self.url,
                data=data,
                headers=headers
            )
            with urllib.request.urlopen(req, context=self.ctx, timeout=5) as _:
                pass  # Ensuring proper indentation here
