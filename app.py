import os
import subprocess
import tkinter as tk
from tkinter import messagebox

# Dapatkan direktori saat ini
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Fungsi untuk menjalankan skrip Python
def run_script(script_name):
    script_path = os.path.join(BASE_DIR, script_name)
    
    if not os.path.exists(script_path):
        messagebox.showerror("Error", f"File {script_name} tidak ditemukan!")
        return
    
    try:
        subprocess.Popen(f'start cmd /k python "{script_path}"', shell=True)
    except Exception as e:
        messagebox.showerror("Error", f"Gagal menjalankan {script_name}\n{str(e)}")

# Membuat Window
root = tk.Tk()
root.title("Face Recognition Attendance")
root.geometry("400x300")
root.resizable(False, False)

# Judul
label_title = tk.Label(root, text="Sistem Absensi Berbasis Wajah", font=("Arial", 14, "bold"))
label_title.pack(pady=10)

# Tombol Registrasi Wajah
btn_register = tk.Button(root, text="Registrasi Wajah", font=("Arial", 12), command=lambda: run_script("register_face.py"))
btn_register.pack(pady=5, fill="x", padx=50)

# Tombol Absensi
btn_attendance = tk.Button(root, text="Mulai Absensi", font=("Arial", 12), command=lambda: run_script("attendance.py"))
btn_attendance.pack(pady=5, fill="x", padx=50)

# Tombol Hapus User
btn_delete = tk.Button(root, text="Hapus User", font=("Arial", 12), command=lambda: run_script("delete_user.py"))
btn_delete.pack(pady=5, fill="x", padx=50)

# Tombol Keluar
btn_exit = tk.Button(root, text="Keluar", font=("Arial", 12), fg="white", bg="red", command=root.quit)
btn_exit.pack(pady=10, fill="x", padx=50)

# Jalankan GUI
root.mainloop()
