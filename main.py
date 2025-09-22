import cv2

from utils.data_manager import load_students, save_students, update_attendance_record
from utils.face_utils import predict_student, save_face_snapshot

START_TIME = "00:00"
END_TIME   = "01:00"

def draw_label(frame, text, coords, color):
    x, y, w, h = coords
    cv2.putText(frame, text, (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
    cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)


def init_camera(width=640, height=480):
    cap = cv2.VideoCapture(0)
    cap.set(3, width)
    cap.set(4, height)
    return cap


def run_attendance_system():
    students = load_students()
    cap = init_camera()

    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

    try:
        while True:
            success, frame = cap.read()
            if not success:
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5)

            for (x, y, w, h) in faces:
                student, conf = predict_student(gray[y:y+h, x:x+w], students)

                if student:
                    draw_label(frame, f"{student['nama']} ({conf:.0f})", (x, y, w, h), (0, 255, 0))
                    updated, now = update_attendance_record(student, START_TIME, END_TIME)
                    if updated:
                        save_face_snapshot(student, frame, (x, y, w, h), now)
                        save_students(students)
                    else:
                        print("❌ Not allowed")
                else:
                    label = "Unknown" if conf is not None else "No Face"
                    draw_label(frame, label, (x, y, w, h), (0, 0, 255))

            cv2.imshow("Face Attendance - LBPH", frame)

            if cv2.waitKey(1) & 0xFF == 27:
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()
        save_students(students)

if __name__ == "__main__":
    run_attendance_system()