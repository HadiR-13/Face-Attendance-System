import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import os, sys
from PIL import Image, ImageTk

try:
    from config import LOG_PATH, IMAGES_DIR, LOGS_DIR
    from data_manager import load_data, load_attendance, save_data, add_student_row, save_api_key, load_api_key
    from face_utils import train_model, save_faces
    from logger import log_message
    from exceptions import set_log_box
except ImportError:
    from utils.config import LOG_PATH, IMAGES_DIR, LOGS_DIR
    from utils.data_manager import load_data, load_attendance, save_data, add_student_row, save_api_key, load_api_key
    from utils.face_utils import train_model, save_faces
    from utils.logger import log_message
    from utils.exceptions import set_log_box

df = load_data()
attendance_df = load_attendance()


def refresh_table(tree, df):
    tree.delete(*tree.get_children())
    for _, row in df.iterrows():
        tree.insert("", "end", values=row.tolist())


def refresh_history(history_tree, attendance_df):
    history_tree.delete(*history_tree.get_children())
    for _, row in attendance_df.iterrows():
        history_tree.insert("", "end", values=row.tolist())


def clear_entries(entries):
    for e in entries.values():
        e.delete(0, tk.END)


def set_entries(entries, values):
    clear_entries(entries)
    for key, v in zip(entries.keys(), values[1:]):
        entries[key].insert(0, v)


def search_dataframe(df, query: str):
    if not query:
        return df
    query = query.lower()
    mask = df.astype(str).agg(lambda row: row.str.lower().str.contains(query).any(), axis=1)
    return df[mask]


def get_next_id(df):
    return 100000 if df.empty else int(df["id"].max()) + 1


def add_student(tree, entries, log_box):
    global df
    selected = tree.selection()
    photo_paths = filedialog.askopenfilenames(filetypes=[("Images", "*.jpg *.png *.jpeg")])
    if not photo_paths:
        return

    if selected:
        student_id = tree.item(selected)["values"][0]
    else:
        df, student_id = add_student_row(df, entries, get_next_id)

    folder = os.path.join(IMAGES_DIR, str(student_id))
    count = save_faces(student_id, photo_paths, folder, log_box)

    if count == 0:
        messagebox.showerror("Error", "No valid faces found")
        return

    refresh_table(tree, df)
    save_data(df)
    log_message(f"🎉 Added {count} images to student ID={student_id}", log_box)


def edit_student(tree, entries, log_box):
    global df
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("Warning", "Select a student first!")
        return

    student_id = tree.item(selected)["values"][0]
    idx = df.index[df["id"] == student_id][0]

    type_map = {
        "Nomor Telepon": int,
        "Total Kehadiran": int,
        "Email": str,
        "Waktu Kehadiran": str,
    }

    for col, entry in entries.items():
        val = entry.get().strip()
        if not val:
            continue
        try:
            if col in type_map:
                df.at[idx, col.lower().replace(" ", "_")] = type_map[col](val)
            else:
                df.at[idx, col.lower().replace(" ", "_")] = val
        except ValueError:
            df.at[idx, col.lower().replace(" ", "_")] = val

    refresh_table(tree, df)
    save_data(df)
    log_message(f"✏️ Edited student {student_id}", log_box)


def delete_student(tree, log_box):
    global df
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("Warning", "Select a student first!")
        return

    student_id = tree.item(selected)["values"][0]
    df = df[df["id"] != student_id]

    folder = os.path.join(IMAGES_DIR, str(student_id))
    if os.path.exists(folder):
        for f in os.listdir(folder):
            try:
                os.remove(os.path.join(folder, f))
            except Exception:
                pass
        try:
            os.rmdir(folder)
        except Exception:
            pass

    refresh_table(tree, df)
    save_data(df)
    log_message(f"🗑️ Deleted student {student_id}", log_box)

def get_api_key():
    api_key = load_api_key()
    if api_key:
        return api_key

    root = tk.Tk()
    root.withdraw()
    api_input = simpledialog.askstring(
        "API Key Required",
        "Enter your API key or full URL:",
        parent=root
    )
    root.resizable(False, False)

    if not api_input:
        messagebox.showerror("Error", "API key is required to continue.")
        sys.exit(1)
    if api_input.startswith("http"):
        api_input = api_input.rstrip("/").split("/")[-1]

    save_api_key(api_input)
    root.destroy()
    return api_input

def start_ui():
    global df, attendance_df


    root = tk.Tk()
    root.title("Student Data Manager with Face Recognition [DEBUG MODE]")
    root.geometry("1200x700")
    root.resizable(False, False)
    root.configure(bg="#f5f6fa")
    api_key = get_api_key()

    def build_menus():
        menubar = tk.Menu(root)

        file_menu = tk.Menu(menubar, tearoff=0)
        for label in ["New Data", "Save Data", "Change Data"]:
            file_menu.add_command(label=label, command=lambda: save_data(df))
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        log_menu = tk.Menu(menubar, tearoff=0)
        log_menu.add_command(label="Open Log File", command=lambda: os.startfile(LOG_PATH))
        log_menu.add_command(label="Clear Log", command=lambda: open(LOG_PATH, "w").close())
        menubar.add_cascade(label="Logs", menu=log_menu)

        root.config(menu=menubar)
    build_menus()

    form_frame = tk.LabelFrame(
        root, text="Student Information", padx=15, pady=15,
        bg="#f5f6fa", font=("Arial", 12, "bold")
    )
    form_frame.place(x=20, y=20, width=400, height=350)

    labels = ["Nama", "Kelas", "Total Kehadiran", "Email", "Nomor Telepon", "Waktu Kehadiran"]
    entries, label_widgets = {}, {}
    for i, text in enumerate(labels):
        lbl = tk.Label(form_frame, text=text + ":", anchor="w", bg="#f5f6fa", font=("Arial", 10))
        lbl.grid(row=i, column=0, sticky="w", pady=5)
        e = tk.Entry(form_frame, width=30, font=("Arial", 10))
        e.grid(row=i, column=1, pady=5, padx=10, sticky="w")
        entries[text] = e
        label_widgets[text] = lbl

    clear_btn = tk.Button(
        form_frame, text="✖ Clear Form", command=lambda: clear_entries(entries), 
        bg="#f77862", fg="white",font=("Arial", 10, "bold"), relief="flat", padx=10, pady=5
    )
    clear_btn.grid(row=7, column=1, padx=100, pady=8)

    image_label = tk.Label(form_frame, bg="#dcdde1")
    image_label.grid(row=0, column=2, rowspan=8, padx=10, pady=5)
    image_label.grid_remove()

    btn_frame = tk.LabelFrame(
        root, text="Actions", padx=10, pady=10,
        bg="#f5f6fa", font=("Arial", 12, "bold")
    )
    btn_frame.place(x=20, y=380, width=400, height=150)

    buttons = {
        "add": dict(text="➕ Add (Select Photos)", cmd=lambda: add_student(tree, entries, log_box),
                    bg="#3498db"),
        "edit": dict(text="✏️ Edit", cmd=lambda: edit_student(tree, entries, log_box),
                     bg="#f39c12"),
        "delete": dict(text="🗑 Delete", cmd=lambda: delete_student(tree, log_box),
                       bg="#e74c3c"),
        "train": dict(text="🧠 Train Model", cmd=lambda: train_model(log_box), 
                      bg="#27ae60"),
    }

    for i, (key, spec) in enumerate(buttons.items()):
        row, col = divmod(i, 2)
        btn = tk.Button(
            btn_frame, text=spec["text"], command=spec["cmd"],
            bg=spec["bg"], fg="white", font=("Arial", 10, "bold"),
            relief="flat", padx=10, pady=5
        )
        btn.grid(row=row, column=col, padx=10, pady=8, sticky="ew")
        buttons[key] = btn

    search_frame = tk.LabelFrame(
        root, text="Search Student", padx=10, pady=10,
        bg="#f5f6fa", font=("Arial", 12, "bold")
    )
    search_frame.place(x=450, y=20, width=720, height=80)

    tk.Label(search_frame, text="Search:", font=("Arial", 10), bg="#f5f6fa").pack(side="left", padx=5)
    search_entry = tk.Entry(search_frame, width=40, font=("Arial", 10))
    search_entry.pack(side="left", padx=5)

    def global_search():
        query = search_entry.get().strip().lower()
        tab = notebook.tab(notebook.select(), "text")
        if tab == "📋 Students":
            filtered = search_dataframe(df, query)
            refresh_table(tree, filtered)
        else:
            filtered = search_dataframe(attendance_df, query)
            refresh_history(history_tree, filtered)
        log_message(f"🔍 Found {len(filtered)} result(s) for '{query}'", log_box)

    def global_clear():
        tab = notebook.tab(notebook.select(), "text")
        if tab == "📋 Students":
            refresh_table(tree, df)
        else:
            refresh_history(history_tree, attendance_df)

    tk.Button(search_frame, text="🔍 Search", command=global_search,
              bg="#2980b9", fg="white", font=("Arial", 9, "bold"),
              relief="flat", padx=10, pady=5).pack(side="left", padx=5)

    tk.Button(search_frame, text="✖ Clear", command=global_clear,
              bg="#7f8c8d", fg="white", font=("Arial", 9, "bold"),
              relief="flat", padx=10, pady=5).pack(side="left", padx=5)

    notebook = ttk.Notebook(root)
    notebook.place(x=450, y=120, width=720, height=411)

    student_tab = tk.Frame(notebook, bg="#f5f6fa")
    notebook.add(student_tab, text="📋 Students")

    cols = ["ID", "Nama", "Kelas", "Total Kehadiran", "Email", "Nomor Telepon", "Waktu Kehadiran"]
    tree = ttk.Treeview(student_tab, columns=cols, show="headings", height=12)
    for col in cols:
        tree.heading(col, text=col)
        tree.column(col, width=100, anchor="center")
    tree.pack(fill="both", expand=True)

    history_tab = tk.Frame(notebook, bg="#f5f6fa")
    notebook.add(history_tab, text="🕒 Attendance History")

    hist_cols = ["id", "name", "date", "status"]
    history_tree = ttk.Treeview(history_tab, columns=hist_cols, show="headings", height=12)
    for col in hist_cols:
        history_tree.heading(col, text=col)
        history_tree.column(col, width=120, anchor="center")
    history_tree.pack(fill="both", expand=True)

    def on_select(event):
        selected = tree.selection()
        if selected:
            set_entries(entries, tree.item(selected)["values"])
    
    def restore_form():
        image_label.grid_remove()
        for lbl in label_widgets.values():
            lbl.grid()
        for entry in entries.values():
            entry.grid()
        clear_btn.grid()

    def on_history_select(event):
        selected = history_tree.selection()
        if not selected:
            return

        values = history_tree.item(selected)["values"]
        student_id, date = values[0], values[2]
        filename = f"{student_id}-{date.replace('-','').replace(':','').replace(' ','')}.png"
        img_path = os.path.join(LOGS_DIR, filename)

        if not os.path.exists(img_path):
            log_message(f"❌ Image not found: {img_path}", log_box)
            return

        try:
            img = Image.open(img_path).resize((300, 300))
            photo = ImageTk.PhotoImage(img)

            image_label.config(image=photo)
            image_label.image = photo
            image_label.grid()

            for widget in entries.values():
                widget.grid_remove()
            for widget in label_widgets.values():
                widget.grid_remove()
            clear_btn.grid_remove()

        except Exception as e:
            log_message(f"❌ Failed to load image {filename}: {e}", log_box)


    def on_tab_change(event):
        tab = notebook.tab(notebook.select(), "text")
        log_message(f"📑 Switched to {tab} tab", log_box)
        if tab == "📋 Students":
            restore_form()
            refresh_table(tree, df)
            for btn in ["add", "edit", "delete"]:
                buttons[btn].config(state="normal")
        else:
            refresh_history(history_tree, attendance_df)
            for btn in ["add", "edit", "delete"]:
                buttons[btn].config(state="disabled")

    tree.bind("<<TreeviewSelect>>", on_select)
    history_tree.bind("<<TreeviewSelect>>", on_history_select)
    notebook.bind("<<NotebookTabChanged>>", on_tab_change)

    log_frame = tk.LabelFrame(root, text="System Log", padx=5, pady=5, bg="#f5f6fa", font=("Arial", 12, "bold"))
    log_frame.place(x=20, y=540, width=1150, height=140)

    log_box = tk.Text(log_frame, height=6, wrap="word", bg="black", fg="lime", font=("Consolas", 10))
    log_box.pack(fill="both", expand=True)

    refresh_table(tree, df)
    refresh_history(history_tree, attendance_df)
    log_message("🚀 Program started", log_box)
    log_message(f"🔑 API Key received: {api_key}", log_box)
    set_log_box(log_box)

    root.protocol("WM_DELETE_WINDOW", lambda: (log_message("🛑 Program closed", log_box), root.destroy()))
    root.mainloop()