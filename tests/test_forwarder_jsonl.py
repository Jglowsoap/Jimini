import json
import os
import tempfile
from app.forwarders.jsonl_forwarder import JsonlForwarder


def test_jsonl_writes_one_line_per_event():
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "events.jsonl")
        fwd = JsonlForwarder(p)
        batch = [{"a": 1}, {"b": 2}]
        fwd.send_many(batch)

        with open(p, "r", encoding="utf-8") as fh:
            lines = [json.loads(x) for x in fh]

        assert lines == batch


def test_jsonl_appends_to_existing_file():
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "events.jsonl")

        # First batch
        fwd = JsonlForwarder(p)
        batch1 = [{"a": 1}]
        fwd.send_many(batch1)

        # Second batch
        batch2 = [{"b": 2}]
        fwd.send_many(batch2)

        with open(p, "r", encoding="utf-8") as fh:
            lines = [json.loads(x) for x in fh]

        assert lines == batch1 + batch2


def test_jsonl_creates_directory_if_not_exists():
    with tempfile.TemporaryDirectory() as d:
        nested_dir = os.path.join(d, "nested", "dir")
        p = os.path.join(nested_dir, "events.jsonl")

        fwd = JsonlForwarder(p)
        batch = [{"a": 1}]
        fwd.send_many(batch)

        assert os.path.exists(p)
        with open(p, "r", encoding="utf-8") as fh:
            lines = [json.loads(x) for x in fh]

        assert lines == batch
