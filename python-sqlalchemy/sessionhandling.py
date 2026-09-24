
from datetime import datetime, timedelta, timezone
from logging.handlers import RotatingFileHandler
import logging
import threading
import time

# --- Logging setup ---
LOG_FILE = "server.log"
handler = RotatingFileHandler(LOG_FILE, maxBytes=5*1024*1024, backupCount=5)  # 5 MB max, keep 5 files
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[handler, logging.StreamHandler()]
)
logger = logging.getLogger(__name__)
# --- session settings ---
sessions = {}
SESSION_TIMEOUT = timedelta(minutes=10)
MAX_HISTORY = 10
MAX_REQUESTS = 4
domain_limits = {}
MAX_DOMAIN_REQUESTS = 500
MAX_MESSAGE_LENGTH = 3000
MAX_SESSION_ID_LENGTH = 100

# --- idle pruning
def prune_idle_sessions():
    now = datetime.now(timezone.utc)
    to_delete = [sid for sid, s in sessions.items() if now - s["last_active"] > SESSION_TIMEOUT]
    for sid in to_delete:
        logger.info(f"Pruned idle session: {sid}")
        del sessions[sid]
# shedule idle pruning every 2 minutes
def session_cleanup_loop():
    while True:
        prune_idle_sessions()
        time.sleep(120)  

threading.Thread(target=session_cleanup_loop, daemon=True).start()

# --- Rate limiting ---
def is_rate_limited(session):
    now = datetime.now(timezone.utc)
    if "requests" not in session:
        session["requests"] = []
    session["requests"] = [ts for ts in session["requests"] if (now - ts).total_seconds() < 60]
    if len(session["requests"]) >= MAX_REQUESTS:
        return True
    session["requests"].append(now)
    return False

def is_domain_rate_limited(domain: str):
    now = datetime.now(timezone.utc)
    if domain not in domain_limits:
        domain_limits[domain] = []
    domain_limits[domain] = [ts for ts in domain_limits[domain] if (now - ts).total_seconds() < 86400]
    if len(domain_limits[domain]) >= MAX_DOMAIN_REQUESTS:
        return True
    domain_limits[domain].append(now)
    return False
