import json
from pathlib import Path

LOG_DIR = Path('logs')
LOG_DIR.mkdir(exist_ok=True)

def append_audit(record):
    date = record.timestamp.split('T')[0]
    log_file = LOG_DIR / f"audit-{date}.jsonl"
    with open(log_file, 'a') as f:
        f.write(record.json() + '\\n')
