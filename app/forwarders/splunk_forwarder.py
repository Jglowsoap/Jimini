import json
import ssl
import urllib.request
from typing import List, Dict, Any
from app.forwarders.base import ResilientForwarder


class SplunkHECForwarder(ResilientForwarder):
    def __init__(
        self,
        url: str,
        token: str,
        sourcetype: str = "jimini:event",
        verify: bool = True,
    ):
        super().__init__("splunk", max_retries=2, base_delay=0.2)
        self.url = url
        self.token = token
        self.sourcetype = sourcetype
        self.ctx = None if verify else ssl._create_unverified_context()

    def _send_batch(self, events: List[Dict[str, Any]]):
        """Send batch to Splunk HEC endpoint"""
        payload = []
        for e in events:
            payload.append({"event": e, "sourcetype": self.sourcetype})
        data = ("\n".join(json.dumps(x) for x in payload)).encode("utf-8")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Splunk {self.token}",
        }

        req = urllib.request.Request(url=self.url, data=data)
        # Add headers explicitly to avoid urllib's automatic Content-Type setting
        for key, value in headers.items():
            req.add_header(key, value)

        with urllib.request.urlopen(req, context=self.ctx, timeout=10) as _:
            pass
