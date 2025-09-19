import os
import cv2
import csv
from datetime import datetime

CSV_FILE = "Data/students.csv"
HISTORY_FILE = "Data/attendance_history.csv"
MODEL_FILE = "Data/face_model.yml"
HAAR_CASCADE = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"

students = []
with open(CSV_FILE, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    students = [row for row in reader]

if not os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["id", "name", "timestamp", "status"])

recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read(MODEL_FILE)
face_cascade = cv2.CascadeClassifier(HAAR_CASCADE)

def find_student_by_id(student_id: str):
    return next((s for s in students if s['id'] == str(student_id)), None)

def update_attendance(student_info: dict):
    """Update attendance if 30s passed since last entry."""
    last_time_str = student_info.get('last_attendance_time', "")
    if last_time_str:
        last_time = datetime.strptime(last_time_str, "%Y-%m-%d %H:%M:%S")
    else:
        last_time = datetime.min

    seconds_elapsed = (datetime.now() - last_time).total_seconds()

    if seconds_elapsed > 30:
        student_info['total_attendance'] = str(int(student_info['total_attendance']) + 1)
        student_info['last_attendance_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with open(CSV_FILE, "w", newline='', encoding='utf-8') as f:
            fieldnames = students[0].keys()
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for s in students:
                if s['id'] == student_info['id']:
                    writer.writerow(student_info)
                else:
                    writer.writerow(s)

        with open(HISTORY_FILE, "a", newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                student_info['id'],
                student_info['name'],
                student_info['last_attendance_time'],
                "Present"
            ])
        print(f"✅ Attendance updated for {student_info['name']}")
        return True
    return False

cap = cv2.VideoCapture(0)
cap.set(3, 640)
cap.set(4, 480)

while True:
    success, frame = cap.read()
    if not success:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5)

    for (x, y, w, h) in faces:
        face_roi = gray[y:y+h, x:x+w]
        face_resized = cv2.resize(face_roi, (200, 200))
        id_pred, conf = recognizer.predict(face_resized)

        if conf < 70:
            student = find_student_by_id(str(id_pred))
            if student:
                name = student["name"]
                cv2.putText(frame, f"{name} ({conf:.0f})", (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                update_attendance(student)
            else:
                cv2.putText(frame, "Unknown ID", (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 255), 2)
        else:
            cv2.putText(frame, "Unknown", (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)

    cv2.imshow("Face Attendance - LBPH", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()