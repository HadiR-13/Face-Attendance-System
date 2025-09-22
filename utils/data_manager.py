import pandas as pd
import os, json
from datetime import datetime

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

# ========================== Database ==========================


def update_attendance_record(student: dict, start_time_str: str, end_time_str: str) -> bool:
    START_TIME = datetime.strptime(start_time_str, "%H:%M").time()
    END_TIME = datetime.strptime(end_time_str, "%H:%M").time()

    last_time_str = student.get('waktu_kehadiran', "")
    last_time = datetime.strptime(last_time_str, "%Y-%m-%d %H:%M:%S") if last_time_str else None
    now = datetime.now()

    if not (START_TIME <= now.time() <= END_TIME):
        return False, now

    if last_time and last_time.date() == now.date():
        return False, now

    student['total_kehadiran'] = str(int(student.get('total_kehadiran', 0)) + 1)
    student['waktu_kehadiran'] = now.strftime("%Y-%m-%d %H:%M:%S")

    save_attendance(student)
    return True, now

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

def load_students():
    df = pd.read_csv(CSV_PATH, encoding='utf-8')
    return {str(row['id']): row.to_dict() for _, row in df.iterrows()}

def save_attendance(student):
    new_row = pd.DataFrame([{
        "id": student['id'],
        "name": student['nama'],
        "timestamp": student['waktu_kehadiran'],
        "status": "Present"
    }])

    new_row.to_csv(ATTENDANCE_PATH, mode='a', index=False, header=False)
    log_message(f"✅ Attendance saved for {student['nama']}")

def save_students(students):
    if not students:
        return
    df = pd.DataFrame(students.values())
    df.to_csv(CSV_PATH, index=False, encoding='utf-8')

def add_student_row(df, entries, get_next_id):
    student_id = get_next_id(df)
    new_row = {
        "id": student_id,
        "nama": entries["Nama"].get(),
        "kelas": entries["Kelas"].get(),
        "total_kehadiran": entries["Total Kehadiran"].get(),
        "email": entries["Email"].get(),
        "nomor_telepon": entries["Nomor Telepon"].get(),
        "waktu_kehadiran": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    return df, student_id