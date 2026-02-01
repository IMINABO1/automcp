import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
TARGET_URL = os.getenv("TARGET_URL", "https://trello.com") 
COOKIES_FILE = os.path.join(BASE_DIR, "cookies.json")
SESSION_FILE = os.path.join(BASE_DIR, "session.json")
EVENTS_LOG = os.path.join(BASE_DIR, "test_events.json")
GENERATED_TOOLS_FILE = os.path.join(BASE_DIR, "generated_tools.py")
