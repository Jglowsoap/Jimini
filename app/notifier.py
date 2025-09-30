# app/notifier.py
import json
import os
import urllib.request
from typing import Dict, List, Optional

import requests

from app.util import redact

WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # put in .env


class Notifier:
    def __init__(self, cfg_notifiers):
        self.slack = cfg_notifiers.slack
        self.teams = cfg_notifiers.teams

    def notify(self, evt):
        text = self._fmt_text(evt)
        if getattr(self.slack, "enabled", False) and self.slack.webhook_url:
            self._post_json(self.slack.webhook_url, {"text": text})
        if getattr(self.teams, "enabled", False) and self.teams.webhook_url:
            # Teams expects "text"
            self._post_json(self.teams.webhook_url, {"text": text})

    def _fmt_text(self, evt):
        rules = ", ".join(evt.rule_ids or [])
        return (
            f"*Jimini Alert* — {evt.decision}\n"
            f"Endpoint: `{evt.endpoint}` | Shadow: `{evt.shadow_mode}`\n"
            f"Rules: {rules}\n"
            f"Request: `{evt.request_id or 'n/a'}` | Latency: {evt.latency_ms or 'n/a'} ms"
        )

    @staticmethod
    def _post_json(url, obj):
        data = json.dumps(obj).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        req = urllib.request.Request(url=url, data=data, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=5) as _:
                pass  # Ensuring proper indentation here
        except Exception:
            # Don't let webhook failures impact the main flow
            pass


def notify_block(
    agent_id: str,
    decision: str,
    rule_ids: List[str],
    endpoint: Optional[str],
    excerpt: str,
):
    if not WEBHOOK_URL or decision != "block":
        return
    text = f":rotating_light: Jimini BLOCK\nagent={agent_id}\nendpoint={endpoint}\nrules={','.join(rule_ids) or '-'}\nexcerpt={excerpt[:200]}"
    payload = {"text": text}
    try:
        requests.post(
            WEBHOOK_URL,
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
            timeout=5,
        )
    except Exception:
        # best-effort: don't break the request path
        pass
