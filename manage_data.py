import sys
from utils.exceptions import handle_exception
from utils.ui import StudentManagerApp

if __name__ == "__main__":
    sys.excepthook = handle_exception
    app = StudentManagerApp()
    app.run()