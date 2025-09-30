# app/notifier.py
import json
import urllib.request
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.config import NotifiersConfig

class Notifier:
    """Phase 3 notifier supporting Slack and Teams webhooks."""
    
    def __init__(self, cfg_notifiers: 'NotifiersConfig'):
        self.slack = cfg_notifiers.slack
        self.teams = cfg_notifiers.teams

    def notify(self, evt):
        """Send notification to enabled channels for BLOCK/FLAG events."""
        text = self._fmt_text(evt)
        
        if getattr(self.slack, "enabled", False) and self.slack.webhook_url:
            self._post_json(self.slack.webhook_url, {"text": text})
        
        if getattr(self.teams, "enabled", False) and self.teams.webhook_url:
            # Teams expects "text" field
            self._post_json(self.teams.webhook_url, {"text": text})

    def _fmt_text(self, evt):
        """Format telemetry event as alert text."""
        rules = ", ".join(evt.rule_ids or [])
        return (
            f"*Jimini Alert* — {evt.decision}\n"
            f"Endpoint: `{evt.endpoint}` | Shadow: `{evt.shadow_mode}`\n"
            f"Rules: {rules}\n"
            f"Request: `{evt.request_id or 'n/a'}` | Latency: {evt.latency_ms or 'n/a'} ms"
        )

    @staticmethod
    def _post_json(url, obj):
        """POST JSON payload to webhook URL."""
        data = json.dumps(obj).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as _:
            pass


# Legacy compatibility function
def notify_block(agent_id: str, decision: str, rule_ids: list, endpoint: str | None, excerpt: str):
    """Legacy notification function - kept for backward compatibility."""
    import os
    WEBHOOK_URL = os.getenv("WEBHOOK_URL")
    if not WEBHOOK_URL or decision != "block":
        return
    text = f":rotating_light: Jimini BLOCK\nagent={agent_id}\nendpoint={endpoint}\nrules={','.join(rule_ids) or '-'}\nexcerpt={excerpt[:200]}"
    payload = {"text": text}
    try:
        import requests
        requests.post(WEBHOOK_URL, data=json.dumps(payload), headers={"Content-Type": "application/json"}, timeout=5)
    except Exception:
        pass
