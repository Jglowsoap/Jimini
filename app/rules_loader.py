import yaml, re
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from app.models import Rule

class RulesHandler(FileSystemEventHandler):
    def __init__(self, path, store):
        self.path = path
        self.store = store
        self._observer = Observer()
        self.load_rules()
        self._observer.schedule(self, self.path, recursive=False)
        self._observer.daemon = True
        self._observer.start()

    def load_rules(self):
        with open(self.path) as f:
            data = yaml.safe_load(f)
        self.store.clear()
        for item in data.get('rules', []):
            rule = Rule(**item)
            self.store[rule.id] = (rule, re.compile(rule.pattern))
        print(f"Loaded {len(self.store)} rules.")

    def on_modified(self, event):
        if event.src_path.endswith(self.path):
            self.load_rules()
