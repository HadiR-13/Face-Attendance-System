import pandas as pd
import os, datetime

try:
    from config import CSV_PATH, ATTENDANCE_PATH
    from logger import log_message
except ImportError:
    from utils.config import CSV_PATH, ATTENDANCE_PATH
    from utils.logger import log_message


def load_data():
    if os.path.exists(CSV_PATH):
        df = pd.read_csv(CSV_PATH)
    else:
        df = pd.DataFrame(columns=["id","name","major","starting_year","total_attendance","year","last_attendance_time"])
    return df

def load_attendance():
    if os.path.exists(ATTENDANCE_PATH):
        return pd.read_csv(ATTENDANCE_PATH)
    return pd.DataFrame(columns=["id","name","date","status"])

def save_data(df):
    df.to_csv(CSV_PATH, index=False)
    log_message("✅ Data saved")

def save_attendance(attendance_df):
    attendance_df.to_csv(ATTENDANCE_PATH, index=False)
    log_message("✅ Attendance saved")

def add_student_row(df, entries, get_next_id):
    student_id = get_next_id(df)
    new_row = {
        "id": student_id,
        "name": entries["Name"].get(),
        "major": entries["Major"].get(),
        "starting_year": entries["Starting Year"].get(),
        "total_attendance": entries["Total Attendance"].get(),
        "year": entries["Year"].get(),
        "last_attendance_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    return df, student_id