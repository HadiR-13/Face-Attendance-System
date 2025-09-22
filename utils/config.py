import os

IMAGES_DIR = "Images"
DATA_DIR = "Data"
LOGS_DIR = os.path.join(DATA_DIR, "Logs")
CACHE_DIR = os.path.join(DATA_DIR, "Cache")

CSV_PATH = os.path.join(DATA_DIR, "students.csv")
MODEL_PATH = os.path.join(DATA_DIR, "face_model.yml")
ATTENDANCE_PATH = os.path.join(DATA_DIR, "attendance_history.csv")
LOG_PATH = os.path.join(CACHE_DIR, "system.txt")
CONFIG_PATH = os.path.join(DATA_DIR, "config.json")

for d in [IMAGES_DIR, DATA_DIR, LOGS_DIR, CACHE_DIR]:
    os.makedirs(d, exist_ok=True)