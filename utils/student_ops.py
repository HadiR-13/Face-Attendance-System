from pathlib import Path
from tkinter import filedialog, messagebox

try:
    from utils.data_manager import save_data, add_student_row
    from utils.face_utils import save_faces
    from utils.logger import log_message
    from utils.config import IMAGES_DIR
except ImportError:
    from utils.data_manager import save_data, add_student_row
    from utils.face_utils import save_faces
    from utils.logger import log_message
    from utils.config import IMAGES_DIR

def add_student(app):
    selected = app.tree.selection()
    photo_paths = filedialog.askopenfilenames(filetypes=[("Images", "*.jpg *.png *.jpeg")])
    if not photo_paths:
        return

    if selected:
        student_id = app.tree.item(selected)["values"][0]
    else:
        app.student_df, student_id = add_student_row(app.student_df, app.entries)

    folder = Path(IMAGES_DIR) / str(student_id)
    count = save_faces(student_id, photo_paths, folder, app.log_box)

    if count == 0:
        messagebox.showerror("Error", "No valid faces found")
        return

    app.refresh_treeview(app.tree, app.student_df)
    save_data(app.student_df)
    log_message(f"🎉 Added {count} images to student ID={student_id}", app.log_box)


def edit_student(app):
    selected = app.tree.selection()
    if not selected:
        messagebox.showwarning("Warning", "Select a student first!")
        return

    student_id = app.tree.item(selected)["values"][0]
    idx = app.student_df.index[app.student_df["id"] == student_id][0]

    type_map = {"Nomor Telepon": int, "Total Kehadiran": int, "Email": str, "Waktu Kehadiran": str}

    for col, entry in app.entries.items():
        val = entry.get().strip()
        if not val:
            continue
        try:
            if col in type_map:
                app.student_df.at[idx, col.lower().replace(" ", "_")] = type_map[col](val)
            else:
                app.student_df.at[idx, col.lower().replace(" ", "_")] = val
        except ValueError:
            app.student_df.at[idx, col.lower().replace(" ", "_")] = val

    app.refresh_treeview(app.tree, app.student_df)
    save_data(app.student_df)
    log_message(f"✏️ Edited student {student_id}", app.log_box)


def delete_student(app):
    selected = app.tree.selection()
    if not selected:
        messagebox.showwarning("Warning", "Select a student first!")
        return

    student_id = app.tree.item(selected)["values"][0]
    if not messagebox.askyesno("Confirm Delete", f"Delete student ID={student_id}?"):
        return

    app.student_df = app.student_df[app.student_df["id"] != student_id]

    folder = Path(IMAGES_DIR) / str(student_id)
    if folder.exists():
        for f in folder.iterdir():
            try:
                f.unlink()
            except Exception as e:
                log_message(f"⚠ Failed to delete file {f}: {e}", app.log_box)
        try:
            folder.rmdir()
        except Exception:
            pass

    app.refresh_treeview(app.tree, app.student_df)
    save_data(app.student_df)
    log_message(f"🗑️ Deleted student {student_id}", app.log_box)