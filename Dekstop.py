import cv2
import face_recognition
import pickle
import os
import numpy as np
import csv
import datetime
import time
import concurrent.futures
import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk

ENCODINGS_FILE = "encodings.pickle"
DATASET_DIR = "dataset"
ATTENDANCE_FILE = "attendance.csv"
CAPTURE_COUNT = 5


# Tentukan jadwal absen (ubah sesuai kebutuhan)
ATTENDANCE_SLOTS = [
    (5, 12),  # Masuk: 05:00 - 12:00
    (15, 21) # Pulang: 13:00 - 21:00
]

# Ensure required directories and files exist
if not os.path.exists(DATASET_DIR):
    os.makedirs(DATASET_DIR)
if os.path.exists(ENCODINGS_FILE):
    with open(ENCODINGS_FILE, "rb") as f:
        data = pickle.load(f)
else:
    data = {"encodings": [], "names": [], "ids": []}
if not os.path.exists(ATTENDANCE_FILE):
    with open(ATTENDANCE_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Name", "Timestamp"])

last_attendance = {}

def is_face_registered(face_encoding):
    return any(face_recognition.compare_faces(data["encodings"], face_encoding))

def register_user():
    user_id = id_entry.get().strip()
    name = name_entry.get().strip()
    if not user_id or not name:
        log("ID dan Nama harus diisi!")
        return

    user_folder = os.path.join(DATASET_DIR, user_id)
    if not os.path.exists(user_folder):
        os.makedirs(user_folder)

    captured_faces = []
    count = 0
    log(f"Memulai registrasi untuk: {name} ({user_id})")

    def capture_frame():
        nonlocal count  # Agar bisa mengakses count dari luar fungsi ini
        if count >= CAPTURE_COUNT:
            save_encodings()  # Simpan hasil jika sudah selesai
            return

        ret, frame = cap.read()
        if not ret:
            log("Gagal menangkap frame dari kamera!")
            return

        img_path = os.path.join(user_folder, f"{name}_{count+1}.jpg")
        cv2.imwrite(img_path, frame)

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        if face_encodings:
            face_encoding = face_encodings[0]
            if is_face_registered(face_encoding):
                log("Wajah sudah terdaftar! Registrasi dibatalkan.")
                os.remove(img_path)
                return

            captured_faces.append(face_encoding)
            count += 1
            log(f"Capture {count}/{CAPTURE_COUNT} berhasil.")

        # Panggil lagi setelah 2000ms (2 detik)
        root.after(2000, capture_frame)

    def save_encodings():
        if captured_faces:
            data["encodings"].extend(captured_faces)
            data["names"].extend([name] * len(captured_faces))
            data["ids"].extend([user_id] * len(captured_faces))

            with open(ENCODINGS_FILE, "wb") as f:
                pickle.dump(data, f)

            log(f"{count} gambar wajah {name} berhasil disimpan.")

    # Mulai proses capture pertama
    capture_frame()

def delete_user():
    user_id = id_entry.get().strip()
    name = name_entry.get().strip()
    if not user_id or not name:
        log("ID dan Nama harus diisi!")
        return
    if user_id in data["ids"] and name in data["names"]:
        indices = [i for i, x in enumerate(data["ids"]) if x == user_id]
        for i in reversed(indices):
            del data["encodings"][i]
            del data["names"][i]
            del data["ids"][i]
        with open(ENCODINGS_FILE, "wb") as f:
            pickle.dump(data, f)
        user_folder = os.path.join(DATASET_DIR, user_id)
        if os.path.exists(user_folder):
            for file in os.listdir(user_folder):
                os.remove(os.path.join(user_folder, file))
            os.rmdir(user_folder)
        log(f"Data {name} ({user_id}) berhasil dihapus!")
    else:
        log("User tidak ditemukan!")

def is_within_attendance_slot():
    """Cek apakah waktu sekarang berada dalam salah satu jadwal absen"""
    now = datetime.datetime.now()
    current_hour = now.hour
    for start, end in ATTENDANCE_SLOTS:
        if start <= current_hour < end:
            return True
    return False

def mark_attendance(user_id, name):
    now = datetime.datetime.now()

    if not is_within_attendance_slot():
        log(f"Absen ditolak! Sekarang bukan waktu absen yang ditentukan.")
        return

    if user_id in last_attendance:
        last_time = last_attendance[user_id]
        last_hour = last_time.hour

        # Cek apakah user sudah absen dalam sesi yang sama
        for start, end in ATTENDANCE_SLOTS:
            if start <= last_hour < end and start <= now.hour < end:
                log(f"{name} ({user_id}) sudah absen di sesi ini!")
                return

    # Simpan absen
    last_attendance[user_id] = now
    with open(ATTENDANCE_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([user_id, name, now.strftime("%Y-%m-%d %H:%M:%S")])
    log(f"Kehadiran dicatat: {name} ({user_id}) pada {now.strftime('%H:%M:%S')}")

def recognize_faces():
    ret, frame = cap.read()
    if not ret:
        return
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb_frame)
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
    for face_encoding in face_encodings:
        matches = face_recognition.compare_faces(data["encodings"], face_encoding)
        if True in matches:
            matched_idx = matches.index(True)
            user_id = data["ids"][matched_idx]
            name = data["names"][matched_idx]
            mark_attendance(user_id, name)
    root.after(1000, recognize_faces)

def log(message):
    log_box.insert(tk.END, message + "\n")
    log_box.see(tk.END)

def process_face(frame):
    """ Fungsi untuk melakukan deteksi wajah di thread terpisah """
    face_locations = face_recognition.face_locations(frame)
    encodings = face_recognition.face_encodings(frame, face_locations)
    return face_locations, encodings

def update_frame():
    ret, frame = cap.read()
    if ret:
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Ubah ke RGB untuk face_recognition

        # Gunakan Threading agar face encoding tidak menghambat loop utama
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(process_face, frame_rgb)
            face_locations, face_encodings = future.result()

        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            matches = face_recognition.compare_faces(data["encodings"], face_encoding)
            name = "Unknown"
            user_id = ""

            if True in matches:
                matched_idx = matches.index(True)
                user_id = data["ids"][matched_idx]
                name = data["names"][matched_idx]

            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            label = f"{name} ({user_id})"
            cv2.putText(frame, label, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Konversi ke RGB untuk ditampilkan di GUI

        # Tampilkan di GUI
        img = Image.fromarray(frame_rgb)
        img = ImageTk.PhotoImage(img)
        video_label.img = img
        video_label.config(image=img)

    video_label.after(10, update_frame)


root = tk.Tk()
root.title("Face Recognition System")
root.geometry(f"{root.winfo_screenwidth()}x{root.winfo_screenheight()}")
root.configure(bg="#333")

main_frame = tk.Frame(root, bg="#333")
main_frame.pack(fill=tk.BOTH, expand=True)

# Load dan resize logo
image = Image.open("images\BPKP_Logo.png")  # Ganti dengan path file logo
image = image.resize((141, 57))  # Ubah ukuran logo sesuai kebutuhan
logo_image = ImageTk.PhotoImage(image)

# Tambahkan logo ke dalam UI
logo_label = tk.Label(root, image=logo_image, bg="#333")
logo_label.pack(pady=10)  # Jarak antara logo dan header

# Frame Header
header_frame = tk.Frame(root, bg="#333")
header_frame.pack(fill=tk.X)

header_label = tk.Label(
    header_frame,
    text="VISAGIUM : FACE RECOGNITION ATTENDANCE SYSTEM",
    fg="white",
    bg="#333",
    font=("Arial", 16, "bold")
)
header_label.pack(pady=10)

# Frame Utama
main_frame = tk.Frame(root, bg="#444")
main_frame.pack(fill=tk.BOTH, expand=True)

# Frame Kiri (Video Feed)
left_frame = tk.Frame(main_frame, bg="#333")
left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

video_label = tk.Label(left_frame)
video_label.pack()
log_box = tk.Text(left_frame, height=10, width=80, bg="#222", fg="white")
log_box.pack(pady=10)

# Frame Kanan (Form Input) - Gunakan pack()
right_frame = tk.Frame(main_frame, bg="#333")
right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

# Sub-frame agar konten lebih mudah diatur
form_frame = tk.Frame(right_frame, bg="#333")
form_frame.pack(expand=True)  # Ini membuat form ada di tengah

# Form Input
tk.Label(form_frame, text="ID:", fg="white", bg="#333").pack(pady=10)
id_entry = tk.Entry(form_frame, width=30)
id_entry.pack(pady=5)

tk.Label(form_frame, text="Nama:", fg="white", bg="#333").pack(pady=10)
name_entry = tk.Entry(form_frame, width=30)
name_entry.pack(pady=5)

# Membuat tombol ukuran sama & vertikal
button_width = 20  
button_height = 2  

register_button = tk.Button(
    form_frame, text="Register", command=register_user,
    bg="#4CAF50", fg="white", width=button_width, height=button_height
)
register_button.pack(pady=5, fill=tk.X)

delete_button = tk.Button(
    form_frame, text="Delete", command=delete_user,
    bg="#f44336", fg="white", width=button_width, height=button_height
)
delete_button.pack(pady=5, fill=tk.X)

attendance_button = tk.Button(
    form_frame, text="Attendance", command=recognize_faces,
    bg="#4CAF50", fg="white", width=button_width, height=button_height
)
attendance_button.pack(pady=5, fill=tk.X)


cap = cv2.VideoCapture(0)
# Mengatur resolusi video agar lebih ringan
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
update_frame()

root.mainloop()
cap.release()
cv2.destroyAllWindows()
