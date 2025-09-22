import os
import cv2
from datetime import datetime
from utils.config import CSV_PATH, LOGS_DIR, MODEL_PATH
from utils.data_manager import save_attendance
import pandas as pd

def load_students():
    df = pd.read_csv(CSV_PATH, encoding='utf-8')
    return {str(row['id']): row.to_dict() for _, row in df.iterrows()}

students = load_students()

def save_students():
    if not students:
        return
    df = pd.DataFrame(students.values())
    df.to_csv(CSV_PATH, index=False, encoding='utf-8')

def update_attendance(student: dict, frame, face_coords):
    last_time_str = student.get('waktu_kehadiran', "")
    last_time = datetime.strptime(last_time_str, "%Y-%m-%d %H:%M:%S") if last_time_str else datetime.min
    now = datetime.now()

    if (now - last_time).total_seconds() <= 30:
        return False

    student['total_kehadiran'] = str(int(student.get('total_kehadiran', 0)) + 1)
    student['waktu_kehadiran'] = now.strftime("%Y-%m-%d %H:%M:%S")

    save_attendance(student)

    (x, y, w, h) = face_coords
    margin = 200
    x1, y1 = max(0, x - margin), max(0, y - margin)
    x2, y2 = min(frame.shape[1], x + w + margin), min(frame.shape[0], y + h + margin)
    face_img = frame[y1:y2, x1:x2]

    filename = f"{student['id']}-{now.strftime('%Y%m%d%H%M%S')}.png"
    filepath = os.path.join(LOGS_DIR, filename)
    cv2.imwrite(filepath, face_img)

    print(f"✅ Attendance updated for {student['nama']}, snapshot saved: {filepath}")
    return True


recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read(MODEL_PATH)
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

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
                    name = student["nama"]
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