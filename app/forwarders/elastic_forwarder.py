# app/forwarders/elastic_forwarder.py
import json
import ssl
import urllib.request
import base64
from typing import List, Dict, Any, Optional, Tuple

class ElasticForwarder:
    """Elasticsearch forwarder - sends events to Elastic."""
    
    def __init__(self, url: str, auth: Optional[Tuple[str, str]] = None, verify: bool = True):
        self.url = url
        self.auth = auth
        self.ctx = None if verify else ssl._create_unverified_context()

    def send_many(self, events: List[Dict[str, Any]]):
        """Send multiple events to Elasticsearch (one at a time for Phase 3)."""
        for e in events:
            data = json.dumps(e).encode("utf-8")
            req = urllib.request.Request(self.url, data=data, headers={"Content-Type": "application/json"})
            if self.auth:
                token = base64.b64encode(f"{self.auth[0]}:{self.auth[1]}".encode()).decode()
                req.add_header("Authorization", f"Basic {token}")
            with urllib.request.urlopen(req, context=self.ctx, timeout=5) as _:
                pass
