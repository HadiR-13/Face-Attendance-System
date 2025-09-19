import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import cv2
import os
import numpy as np
import datetime

IMAGES_DIR = "Images"
DATA_DIR = "Data"
os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

CSV_PATH = os.path.join(DATA_DIR, "students.csv")
MODEL_PATH = os.path.join(DATA_DIR, "face_model.yml")

df = pd.read_csv(CSV_PATH) if os.path.exists(CSV_PATH) else pd.DataFrame(
    columns=["id", "name", "major", "starting_year", "total_attendance", "year", "last_attendance_time"]
)

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

CACHE_DIR = os.path.join(DATA_DIR, "Cache")
os.makedirs(CACHE_DIR, exist_ok=True)

LOG_PATH = os.path.join(CACHE_DIR, "system_log.txt")

def log_message(msg: str):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {msg}"

    log_box.insert(tk.END, log_entry + "\n")
    log_box.see(tk.END)

    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(log_entry + "\n")

def save_data():
    df.to_csv(CSV_PATH, index=False)
    log_message("✅ Data saved")

def refresh_table():
    tree.delete(*tree.get_children())
    for _, row in df.iterrows():
        tree.insert("", "end", values=row.tolist())

def clear_entries():
    for e in entries.values():
        e.delete(0, tk.END)

def set_entries(values):
    clear_entries()
    keys = list(entries.keys())
    for key, v in zip(keys, values[1:]):
        entries[key].insert(0, v)

def get_next_id():
    return 100000 if df.empty else int(df["id"].max()) + 1

def search_table():
    query = search_entry.get().strip().lower()
    tree.delete(*tree.get_children())

    if not query:
        refresh_table()
        return

    filtered = df[df.apply(lambda row: row.astype(str).str.lower().str.contains(query).any(), axis=1)]

    for _, row in filtered.iterrows():
        tree.insert("", "end", values=row.tolist())

    log_message(f"🔍 Found {len(filtered)} result(s) for '{query}'")

def preprocess_face(img):
    faces = face_cascade.detectMultiScale(img, scaleFactor=1.2, minNeighbors=5)
    if len(faces) == 0:
        return None
    x, y, w, h = faces[0]
    return cv2.resize(img[y:y+h, x:x+w], (200, 200))

def add_student():
    global df
    selected = tree.selection()
    if selected:
        student_id = tree.item(selected)["values"][0]
        student_folder = os.path.join(IMAGES_DIR, str(student_id))
        os.makedirs(student_folder, exist_ok=True)

        existing_files = [f for f in os.listdir(student_folder) if f.endswith((".jpg", ".png", ".jpeg"))]
        start_index = len(existing_files) + 1  

        photo_paths = filedialog.askopenfilenames(filetypes=[("Images", "*.jpg *.png *.jpeg")])
        if not photo_paths:
            return

        count = 0
        for i, photo_path in enumerate(photo_paths, start=start_index):
            img = cv2.imread(photo_path, cv2.IMREAD_GRAYSCALE)
            if img is None:
                log_message(f"⚠️ Invalid file {photo_path}")
                continue

            face = preprocess_face(img)
            if face is None:
                log_message(f"⚠️ No face in {photo_path}")
                continue

            save_path = os.path.join(student_folder, f"{student_id}_{i}.jpg")
            cv2.imwrite(save_path, face)
            count += 1
            log_message(f"✅ Added face: {save_path}")

        if count > 0:
            log_message(f"🎉 Added {count} new image(s) to student ID={student_id}")
        else:
            messagebox.showerror("Error", "No valid faces found")

    else:
        new_id = get_next_id()

        photo_paths = filedialog.askopenfilenames(filetypes=[("Images", "*.jpg *.png *.jpeg")])
        if not photo_paths:
            return

        student_folder = os.path.join(IMAGES_DIR, str(new_id))
        os.makedirs(student_folder, exist_ok=True)

        count = 0
        for i, photo_path in enumerate(photo_paths, start=1):
            img = cv2.imread(photo_path, cv2.IMREAD_GRAYSCALE)
            if img is None:
                log_message(f"⚠️ Invalid file {photo_path}")
                continue

            face = preprocess_face(img)
            if face is None:
                log_message(f"⚠️ No face in {photo_path}")
                continue

            save_path = os.path.join(student_folder, f"{new_id}_{i}.jpg")
            cv2.imwrite(save_path, face)
            count += 1
            log_message(f"✅ Saved face: {save_path}")

        if count == 0:
            messagebox.showerror("Error", "No valid faces found")
            return

        new_row = {
            "id": new_id,
            "name": entry_name.get(),
            "major": entry_major.get(),
            "starting_year": entry_start.get(),
            "total_attendance": entry_att.get(),
            "year": entry_year.get(),
            "last_attendance_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

        refresh_table()
        save_data()
        log_message(f"🎉 Added {new_row['name']} (ID={new_id}) with {count} images")

def edit_student():
    global df
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("Warning", "Select a student first!")
        return

    student_id = tree.item(selected)["values"][0]
    idx = df.index[df["id"] == student_id][0]

    type_map = {
        "starting_year": int,
        "total_attendance": int,
        "year": int,
        "last_attendance_time": str,
    }

    updated = {
        "name": entry_name.get(),
        "major": entry_major.get(),
        "starting_year": entry_start.get(),
        "total_attendance": entry_att.get(),
        "year": entry_year.get(),
        "last_attendance_time": entry_time.get()
    }

    for col, val in updated.items():
        if col in type_map and val != "":
            try:
                df.at[idx, col] = type_map[col](val)
            except ValueError:
                df.at[idx, col] = val
        else:
            df.at[idx, col] = val

    refresh_table()
    save_data()
    log_message(f"✏️ Edited student {student_id}")

def delete_student():
    global df
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("Warning", "Select a student first!")
        return

    student_id = tree.item(selected)["values"][0]
    df = df[df["id"] != student_id]

    student_folder = os.path.join(IMAGES_DIR, str(student_id))
    if os.path.exists(student_folder):
        for f in os.listdir(student_folder):
            os.remove(os.path.join(student_folder, f))
        os.rmdir(student_folder)

    refresh_table()
    save_data()
    log_message(f"🗑️ Deleted student {student_id}")

def train_model():
    faces, labels = [], []
    log_message("🔄 Collecting faces for training...")

    for student_id in os.listdir(IMAGES_DIR):
        folder = os.path.join(IMAGES_DIR, student_id)
        if not os.path.isdir(folder):
            continue

        for img_name in os.listdir(folder):
            img_path = os.path.join(folder, img_name)
            img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
            if img is None:
                log_message(f"⚠️ Could not read {img_path}")
                continue

            face = preprocess_face(img)
            if face is None:
                log_message(f"⚠️ No detectable face in {img_name}")
                continue

            face = cv2.equalizeHist(face)

            faces.append(face)
            labels.append(int(student_id))

    if faces:
        recognizer = cv2.face.LBPHFaceRecognizer_create(
            radius=2, neighbors=8, grid_x=8, grid_y=8
        )
        recognizer.train(faces, np.array(labels))
        recognizer.save(MODEL_PATH)

        log_message(f"✅ Model trained with {len(faces)} samples and {len(set(labels))} students")
    else:
        log_message("❌ No valid images found, training aborted")

def main():
    global root, log_box, entries, entry_name, entry_major, entry_start, entry_att, entry_year, entry_time, tree, search_entry

    root = tk.Tk()
    root.title("Student Data Manager with Face Recognition")
    root.geometry("1200x700")
    root.configure(bg="#f5f6fa")

    form_frame = tk.LabelFrame(root, text="Student Information", padx=15, pady=15, bg="#f5f6fa", font=("Arial", 12, "bold"))
    form_frame.place(x=20, y=20, width=400, height=350)

    labels = ["Name", "Major", "Starting Year", "Total Attendance", "Year", "Last Attendance Time"]
    entries = {}
    for i, text in enumerate(labels):
        tk.Label(form_frame, text=text + ":", anchor="w", bg="#f5f6fa", font=("Arial", 10)).grid(row=i, column=0, sticky="w", pady=5)
        e = tk.Entry(form_frame, width=30, font=("Arial", 10))
        e.grid(row=i, column=1, pady=5, padx=10, sticky="w")
        entries[text] = e

    entry_name = entries["Name"]
    entry_major = entries["Major"]
    entry_start = entries["Starting Year"]
    entry_att = entries["Total Attendance"]
    entry_year = entries["Year"]
    entry_time = entries["Last Attendance Time"]

    btn_frame = tk.LabelFrame(root, text="Actions", padx=10, pady=10, bg="#f5f6fa", font=("Arial", 12, "bold"))
    btn_frame.place(x=20, y=380, width=400, height=150)

    buttons = [
        ("➕ Add (Select Photos)", add_student),
        ("✏️ Edit", edit_student),
        ("🗑 Delete", delete_student),
        ("🧠 Train Model", train_model)
    ]

    for i, (txt, cmd) in enumerate(buttons):
        color = "#27ae60" if "Train" in txt else "#3498db" if "Add" in txt else "#f39c12" if "Edit" in txt else "#e74c3c"
        tk.Button(btn_frame, text=txt, command=cmd, bg=color, fg="white", font=("Arial", 10, "bold"), relief="flat", padx=10, pady=5).grid(row=i // 2, column=i % 2, padx=10, pady=8, sticky="ew")

    search_frame = tk.LabelFrame(root, text="Search Student", padx=10, pady=10, bg="#f5f6fa", font=("Arial", 12, "bold"))
    search_frame.place(x=450, y=20, width=720, height=80)

    tk.Label(search_frame, text="Search:", font=("Arial", 10), bg="#f5f6fa").pack(side="left", padx=5)
    search_entry = tk.Entry(search_frame, width=40, font=("Arial", 10))
    search_entry.pack(side="left", padx=5)

    tk.Button(search_frame, text="🔍 Search", command=search_table, 
              bg="#2980b9", fg="white", font=("Arial", 9, "bold"), relief="flat", padx=10, pady=5).pack(side="left", padx=5)

    tk.Button(search_frame, text="✖ Clear", command=refresh_table, 
              bg="#7f8c8d", fg="white", font=("Arial", 9, "bold"), relief="flat", padx=10, pady=5).pack(side="left", padx=5)

    table_frame = tk.LabelFrame(root, text="Student Records", padx=5, pady=5, bg="#f5f6fa", font=("Arial", 12, "bold"))
    table_frame.place(x=450, y=120, width=720, height=350)

    cols = ["ID", "Name", "Major", "Starting Year", "Total Attendance", "Year", "Last Attendance Time"]
    tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=12)

    for col in cols:
        tree.heading(col, text=col)
        tree.column(col, width=100, anchor="center")

    tree.pack(fill="both", expand=True)

    def on_select(event):
        selected = tree.selection()
        if selected:
            values = tree.item(selected)["values"]
            set_entries(values)

    tree.bind("<<TreeviewSelect>>", on_select)

    log_frame = tk.LabelFrame(root, text="System Log", padx=5, pady=5, bg="#f5f6fa", font=("Arial", 12, "bold"))
    log_frame.place(x=20, y=540, width=1150, height=140)

    log_box = tk.Text(log_frame, height=6, wrap="word", bg="black", fg="lime", font=("Consolas", 10))
    log_box.pack(fill="both", expand=True)

    refresh_table()

    log_message("🚀 Program started")
    root.protocol("WM_DELETE_WINDOW", lambda: (log_message("🛑 Program closed"), root.destroy()))

    root.mainloop()

if __name__ == "__main__":
    main()