import datetime

try:
    from config import LOG_PATH
except ImportError:
    from utils.config import LOG_PATH

def log_message(msg: str, log_box=None):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {msg}"

    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(log_entry + "\n")

    if log_box:
        try:
            log_box.insert("end", log_entry + "\n")
            log_box.see("end")
        except Exception:
            pass