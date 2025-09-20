import sys, traceback
from tkinter import messagebox

try:
    from logger import log_message
except ImportError:
    from utils.logger import log_message

log_box = None

def set_log_box(widget):
    global log_box
    log_box = widget

def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    log_message(f"❌ ERROR: {error_msg}")
    messagebox.showerror("Unexpected Error", str(exc_value))