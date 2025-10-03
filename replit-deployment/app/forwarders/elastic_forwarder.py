import json
import ssl
import urllib.request
import base64
from typing import List, Dict, Any, Tuple, Optional
from app.forwarders.base import ResilientForwarder


class ElasticForwarder(ResilientForwarder):
    def __init__(self, url: str, auth: Optional[Tuple[str, str]] = None, verify: bool = True):
        super().__init__("elastic", max_retries=2, base_delay=0.2)
        self.url = url
        self.auth = auth
        self.ctx = None if verify else ssl._create_unverified_context()

    def _send_batch(self, events: List[Dict[str, Any]]):
        """Send batch to Elasticsearch - one document at a time for now"""
        # TODO: Implement bulk API for better performance
        for e in events:
            data = json.dumps(e).encode("utf-8")

            headers = {"Content-Type": "application/json"}
            if self.auth and self.auth[0] and self.auth[1]:
                token = base64.b64encode(
                    f"{self.auth[0]}:{self.auth[1]}".encode()
                ).decode()
                headers["Authorization"] = f"Basic {token}"

            req = urllib.request.Request(url=self.url, data=data)
            # Add headers explicitly to avoid urllib's automatic Content-Type setting
            for key, value in headers.items():
                req.add_header(key, value)

            with urllib.request.urlopen(req, context=self.ctx, timeout=10) as _:
                pass
