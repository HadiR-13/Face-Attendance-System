import sys
from utils.exceptions import handle_exception
from utils.ui import start_ui

if __name__ == "__main__":
    sys.excepthook = handle_exception
    start_ui()