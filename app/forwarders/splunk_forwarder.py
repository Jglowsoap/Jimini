# app/forwarders/splunk_forwarder.py
import json
import ssl
import urllib.request
from typing import List, Dict, Any

class SplunkHECForwarder:
    """Splunk HEC (HTTP Event Collector) forwarder."""
    
    def __init__(self, url: str, token: str, sourcetype: str = "jimini:event", verify: bool = True):
        self.url = url
        self.token = token
        self.sourcetype = sourcetype
        self.ctx = None if verify else ssl._create_unverified_context()

    def send_many(self, events: List[Dict[str, Any]]):
        """Send multiple events to Splunk HEC."""
        payload = []
        for e in events:
            payload.append({"event": e, "sourcetype": self.sourcetype})
        data = ("\n".join(json.dumps(x) for x in payload)).encode("utf-8")
        req = urllib.request.Request(
            self.url, data=data,
            headers={"Content-Type": "application/json", "Authorization": f"Splunk {self.token}"}
        )
        with urllib.request.urlopen(req, context=self.ctx, timeout=5) as _:
            pass
