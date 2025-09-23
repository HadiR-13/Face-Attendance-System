import threading
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import cv2

from utils.data_manager import load_students, save_students, update_attendance_record
from utils.face_utils import predict_student, save_face_snapshot


class AttendanceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Face Attendance System")
        self.root.geometry("950x550")

        self.start_time = "09:00"
        self.end_time = "23:59"

        menubar = tk.Menu(root)
        root.config(menu=menubar)

        settings_menu = tk.Menu(menubar, tearoff=0)
        settings_menu.add_command(label="Set Time Range", command=self.set_time_range)
        menubar.add_cascade(label="Settings", menu=settings_menu)

        self.frame_main = ttk.Frame(root)
        self.frame_main.pack(fill="both", expand=True, padx=10, pady=10)

        self.lbl_video = tk.Label(self.frame_main)
        self.lbl_video.grid(row=0, column=0, padx=10, pady=10)

        self.info_frame = ttk.Frame(self.frame_main)
        self.info_frame.grid(row=0, column=1, sticky="n")

        self.lbl_status = ttk.Label(self.info_frame, text="Click 'Start' to begin", font=("Arial", 12))
        self.lbl_status.pack(pady=10)

        self.lbl_name = ttk.Label(self.info_frame, text="", font=("Arial", 14, "bold"))
        self.lbl_name.pack(pady=10)

        self.lbl_conf = ttk.Label(self.info_frame, text="", font=("Arial", 12))
        self.lbl_conf.pack(pady=5)

        self.lbl_timerange = ttk.Label(self.info_frame, text=f"Allowed Time: {self.start_time} - {self.end_time}", font=("Arial", 11))
        self.lbl_timerange.pack(pady=20)

        self.start_btn = ttk.Button(root, text="Start Attendance", command=self.start_system)
        self.start_btn.pack(pady=10)

        self.cap = None
        self.students = None
        self.running = False

    def set_time_range(self):
        """Dialog for selecting start & end time"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Set Attendance Time Range")
        dialog.geometry("300x150")
        dialog.resizable(False, False)

        def make_time_selector(parent, row, label_text, default):
            ttk.Label(parent, text=label_text).grid(row=row, column=0, padx=5, pady=5)
            h, m = map(int, default.split(":"))
            spin_h = ttk.Spinbox(parent, from_=0, to=23, width=5, format="%02.0f")
            spin_h.set(f"{h:02d}")
            spin_h.grid(row=row, column=1, padx=2)
            ttk.Label(parent, text=":").grid(row=row, column=2)
            spin_m = ttk.Spinbox(parent, from_=0, to=59, width=5, format="%02.0f")
            spin_m.set(f"{m:02d}")
            spin_m.grid(row=row, column=3, padx=2)
            return spin_h, spin_m

        start_h, start_m = make_time_selector(dialog, 0, "Start Time", self.start_time)
        end_h, end_m = make_time_selector(dialog, 1, "End Time", self.end_time)

        def save_time():
            self.start_time = f"{int(start_h.get()):02d}:{int(start_m.get()):02d}"
            self.end_time = f"{int(end_h.get()):02d}:{int(end_m.get()):02d}"
            self.lbl_timerange.config(text=f"Allowed Time: {self.start_time} - {self.end_time}")
            dialog.destroy()

        ttk.Button(dialog, text="Save", command=save_time).grid(row=2, column=0, columnspan=4, pady=10)

    def start_system(self):
        self.start_btn.config(state="disabled")
        self.lbl_status.config(text="Loading model and students data...")
        threading.Thread(target=self.load_and_run, daemon=True).start()

    def load_and_run(self):
        try:
            self.students = load_students()
            self.lbl_status.config(text="Model loaded. Starting camera...")

            self.cap = cv2.VideoCapture(0)
            self.running = True
            self.update_frame()
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.start_btn.config(state="normal")

    def update_frame(self):
        if not self.running:
            return

        ret, frame = self.cap.read()
        if not ret:
            self.lbl_status.config(text="Failed to access camera")
            return

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5)

        detected_name, detected_conf = None, None

        for (x, y, w, h) in faces:
            student, conf = predict_student(gray[y:y+h, x:x+w], self.students)

            if student:
                detected_name = student['nama']
                detected_conf = conf
                color = (0, 255, 0)
                cv2.putText(frame, f"{student['nama']} ({conf:.0f})", (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
                cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)

                updated, now = update_attendance_record(student, self.start_time, self.end_time)
                if updated:
                    save_face_snapshot(student, frame, (x, y, w, h), now)
                    save_students(self.students)
            else:
                detected_name = "Unknown"
                detected_conf = conf
                color = (0, 0, 255)
                cv2.putText(frame, "Unknown", (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
                cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)

        if detected_name:
            self.lbl_name.config(text=f"Name: {detected_name}")
            self.lbl_conf.config(text=f"Confidence: {detected_conf:.0f}" if detected_conf else "")
            self.lbl_status.config(text="Detected")
        else:
            self.lbl_name.config(text="")
            self.lbl_conf.config(text="")
            self.lbl_status.config(text="No face detected")

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        imgtk = ImageTk.PhotoImage(image=img)
        self.lbl_video.imgtk = imgtk
        self.lbl_video.configure(image=imgtk)

        self.root.after(10, self.update_frame)

    def on_close(self):
        self.running = False
        if self.cap:
            self.cap.release()
        save_students(self.students) if self.students else None
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = AttendanceApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()