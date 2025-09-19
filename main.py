import os
import cv2
import csv
from datetime import datetime

DATA_DIR = "Data"
CSV_FILE = os.path.join(DATA_DIR, "students.csv")
HISTORY_FILE = os.path.join(DATA_DIR, "attendance_history.csv")
MODEL_FILE = os.path.join(DATA_DIR, "face_model.yml")
HAAR_CASCADE = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
LOG_DIR = os.path.join(DATA_DIR, "Logs")

os.makedirs(LOG_DIR, exist_ok=True)

students = {}
with open(CSV_FILE, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        students[row['id']] = row

if not os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["id", "name", "timestamp", "status"])

recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read(MODEL_FILE)
face_cascade = cv2.CascadeClassifier(HAAR_CASCADE)


def save_students():
    """Save updated student data back to CSV."""
    if not students:
        return
    fieldnames = list(next(iter(students.values())).keys())
    with open(CSV_FILE, "w", newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(students.values())


def update_attendance(student: dict, frame, face_coords):
    """Update attendance if 30s passed since last entry and save snapshot."""
    last_time_str = student.get('last_attendance_time', "")
    last_time = datetime.strptime(last_time_str, "%Y-%m-%d %H:%M:%S") if last_time_str else datetime.min
    now = datetime.now()

    if (now - last_time).total_seconds() <= 30:
        return False

    student['total_attendance'] = str(int(student.get('total_attendance', 0)) + 1)
    student['last_attendance_time'] = now.strftime("%Y-%m-%d %H:%M:%S")

    with open(HISTORY_FILE, "a", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([student['id'], student['name'], student['last_attendance_time'], "Present"])

    (x, y, w, h) = face_coords
    margin = 40
    x1, y1 = max(0, x - margin), max(0, y - margin)
    x2, y2 = min(frame.shape[1], x + w + margin), min(frame.shape[0], y + h + margin)
    face_img = frame[y1:y2, x1:x2]

    filename = f"{student['id']}-{now.strftime('%Y%m%d%H%M%S')}.png"
    filepath = os.path.join(LOG_DIR, filename)
    cv2.imwrite(filepath, face_img)

    print(f"✅ Attendance updated for {student['name']}, snapshot saved: {filepath}")
    return True


cap = cv2.VideoCapture(0)
cap.set(3, 640)
cap.set(4, 480)

try:
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
                student = students.get(str(id_pred))
                if student:
                    name = student["name"]
                    cv2.putText(frame, f"{name} ({conf:.0f})", (x, y - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                    if update_attendance(student, frame, (x, y, w, h)):
                        save_students()
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

finally:
    cap.release()
    cv2.destroyAllWindows()
    save_students()