import pandas as pd
import os, datetime, json

try:
    from config import CSV_PATH, ATTENDANCE_PATH, CONFIG_PATH
    from logger import log_message
except ImportError:
    from utils.config import CSV_PATH, ATTENDANCE_PATH, CONFIG_PATH
    from utils.logger import log_message


def save_api_key(api_key: str):
    with open(CONFIG_PATH, "w") as f:
        json.dump({"api_key": api_key}, f)

def load_api_key():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                data = json.load(f)
                return data.get("api_key")
        except (json.JSONDecodeError, ValueError):
            return None
    return None

def load_data():
    if os.path.exists(CSV_PATH):
        df = pd.read_csv(CSV_PATH)
    else:
        df = pd.DataFrame(columns=["id","name","kelas", "total_kehadiran", "email", "nomor_telepon","waktu_kehadiran"])
    return df

def load_attendance():
    if os.path.exists(ATTENDANCE_PATH):
        return pd.read_csv(ATTENDANCE_PATH)
    return pd.DataFrame(columns=["id","name","date","status"])

def save_data(df):
    df.to_csv(CSV_PATH, index=False)
    log_message("✅ Data saved")

def save_attendance(student):
    new_row = pd.DataFrame([{
        "id": student['id'],
        "name": student['nama'],
        "timestamp": student['waktu_kehadiran'],
        "status": "Present"
    }])

    new_row.to_csv(ATTENDANCE_PATH, mode='a', index=False, header=False)
    log_message("✅ Attendance saved")

def add_student_row(df, entries, get_next_id):
    student_id = get_next_id(df)
    new_row = {
        "id": student_id,
        "nama": entries["Nama"].get(),
        "kelas": entries["Kelas"].get(),
        "total_kehadiran": entries["Total Kehadiran"].get(),
        "email": entries["Email"].get(),
        "nomor_telepon": entries["Nomor Telepon"].get(),
        "waktu_kehadiran": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    return df, student_id