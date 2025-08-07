import os
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv("JIMINI_API_KEY", "changeme")
RULES_PATH = os.getenv("JIMINI_RULES_PATH", "policy_rules.yaml")
