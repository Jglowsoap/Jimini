# app/notifier.py
import os, json
from typing import List, Optional
import requests

WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # put in .env

def notify_block(agent_id: str, decision: str, rule_ids: List[str], endpoint: Optional[str], excerpt: str):
    if not WEBHOOK_URL or decision != "block":
        return
    text = f":rotating_light: Jimini BLOCK\nagent={agent_id}\nendpoint={endpoint}\nrules={','.join(rule_ids) or '-'}\nexcerpt={excerpt[:200]}"
    payload = {"text": text}
    try:
        requests.post(WEBHOOK_URL, data=json.dumps(payload), headers={"Content-Type": "application/json"}, timeout=5)
    except Exception:
        # best-effort: don't break the request path
        pass
