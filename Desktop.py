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
import requests
import json
import shutil
from tkinter import messagebox, ttk
from PIL import Image, ImageTk


ENCODINGS_FILE = "encodings.pickle"
DATASET_DIR = "dataset"
ATTENDANCE_FILE = "attendance.csv"
CAPTURE_COUNT = 5
API_ATTENDANCE_URL = "https://visagium-api.onrender.com/Attendance"
API_EMPLOYEE = "https://visagium-api.onrender.com/Employee"

# Tentukan jadwal absen (ubah sesuai kebutuhan)
ATTENDANCE_SLOTS = [
    (5, 12),  # Masuk: 05:00 - 12:00
    (15, 23) # Pulang: 13:00 - 21:00
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
    """Cek apakah wajah sudah terdaftar berdasarkan jarak encoding"""
    if not data["encodings"]:  # Jika database kosong, langsung return False
        return False  

    distances = face_recognition.face_distance(data["encodings"], face_encoding)
    min_distance = min(distances)

    # Gunakan threshold yang lebih ketat (0.4 - 0.5) untuk menghindari false positive
    if min_distance < 0.45:
        log(f"Wajah terdeteksi sudah terdaftar dengan jarak {min_distance:.2f}")
        return True  
    return False  


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
        nonlocal count
        if count >= CAPTURE_COUNT:
            save_encodings()
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

            # 🔍 Cek apakah wajah sudah ada dengan metode baru
            if is_face_registered(face_encoding):
                log("⚠️ Wajah sudah terdaftar! Registrasi dibatalkan.")
                os.remove(img_path)
                return

            captured_faces.append(face_encoding)
            count += 1
            log(f"Capture {count}/{CAPTURE_COUNT} berhasil.")

        root.after(2000, capture_frame)

    def save_encodings():
        if captured_faces:
            try:
                payload = {
                    "employee_id": int(user_id),
                    "name": name
                }
                headers = {"Content-Type": "application/json"}
                
                response = requests.post(API_EMPLOYEE, data=json.dumps(payload), headers=headers)
                
                if response.status_code == 200:
                    log(f"Registrasi {name} berhasil dikirim ke API! ✅")
                else:
                    log(f"⚠️ Gagal mengirim data ke API! Status: {response.status_code}")
                    raise Exception("Gagal mengirim ke API")
                
            except Exception as e:
                log(f"❌ Registrasi dibatalkan! Error API: {e}")
                if os.path.exists(user_folder):
                    shutil.rmtree(user_folder)
                    log("Folder user dihapus untuk menghindari data yang tidak valid.")
                return

            data["encodings"].extend(captured_faces)
            data["names"].extend([name] * len(captured_faces))
            data["ids"].extend([user_id] * len(captured_faces))

            with open(ENCODINGS_FILE, "wb") as f:
                pickle.dump(data, f)

            log(f"{count} gambar wajah {name} berhasil disimpan.")

    capture_frame()

def delete_user():
    user_id = id_entry.get().strip()
    name = name_entry.get().strip()

    if not user_id or not name:
        log("ID dan Nama harus diisi!")
        return

    if user_id in data["ids"] and name in data["names"]:
        # Kirim permintaan DELETE ke API
        response = requests.delete(API_EMPLOYEE, json={"employee_id": int(user_id)})

        if response.status_code == 200:  # Pastikan API berhasil menghapus
            log(f"⚠️ User {name} ({user_id}) berhasil dihapus dari database!")

            # Hapus dari data lokal setelah sukses dari API
            indices = [i for i, x in enumerate(data["ids"]) if x == user_id]
            for i in reversed(indices):
                del data["encodings"][i]
                del data["names"][i]
                del data["ids"][i]

            with open(ENCODINGS_FILE, "wb") as f:
                pickle.dump(data, f)

            # Hapus folder dataset user
            user_folder = os.path.join(DATASET_DIR, user_id)
            if os.path.exists(user_folder):
                for file in os.listdir(user_folder):
                    os.remove(os.path.join(user_folder, file))
                os.rmdir(user_folder)

            log(f"⚠️ Data {name} ({user_id}) berhasil dihapus secara lokal!")
        else:
            log(f"❌ Gagal menghapus user {name} ({user_id}) dari database! Error: {response.status_code}")

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

def load_attendance_history():
    """Memuat riwayat kehadiran dari file agar tidak hilang saat restart."""
    if not os.path.exists(ATTENDANCE_FILE):
        return

    with open(ATTENDANCE_FILE, "r") as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) < 3:
                continue  # Lewati data yang tidak valid
            user_id, name, timestamp = row
            last_attendance[user_id] = datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")

def send_attendance_to_api(user_id, name, timestamp):
    """ Mengirim data ke API dan hanya menyimpan lokal jika berhasil """
    try:
        payload = {
            "employee_id": int(user_id),  # Pastikan sebagai integer
            "name": name,
            "timestamp": timestamp
        }
        headers = {"Content-Type": "application/json"}

        response = requests.post(API_ATTENDANCE_URL, data=json.dumps(payload), headers=headers)

        if response.status_code == 200:
            log(f"✅ Kehadiran {name} ({user_id}) berhasil dikirim ke API!")
            return True
        else:
            log(f"⚠️ Gagal mengirim ke API! Status: {response.status_code}")
            return False

    except Exception as e:
        log(f"❌ Error saat mengirim ke API: {e}")
        return False

def mark_attendance(user_id, name):
    """ Mencatat kehadiran hanya jika API berhasil menerima data """
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")

    if not is_within_attendance_slot():
        log(f"⏳ Absen ditolak! Sekarang bukan waktu absen yang ditentukan.")
        return

    if user_id in last_attendance:
        last_time = last_attendance[user_id]
        last_hour = last_time.hour

        for start, end in ATTENDANCE_SLOTS:
            if start <= last_hour < end and start <= now.hour < end:
                log(f"⚠️ {name} ({user_id}) sudah absen di sesi ini!")
                return

    # 🔹 Kirim ke API dulu
    if send_attendance_to_api(user_id, name, timestamp):
        # Jika sukses, lanjutkan menyimpan ke lokal
        last_attendance[user_id] = now

        with open(ATTENDANCE_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([user_id, name, timestamp])

        log(f"✅ Kehadiran dicatat & disimpan lokal: {name} ({user_id}) pada {timestamp}")
    else:
        log(f"❌ Kehadiran gagal dicatat karena API tidak merespons!")


# Panggil fungsi ini saat aplikasi dimulai
load_attendance_history()

def recognize_faces():
    """ Deteksi wajah dan pencocokan dengan data yang telah disimpan """
    ret, frame = cap.read()
    if not ret:
        return
    
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb_frame)
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

    for face_encoding in face_encodings:
        face_distances = face_recognition.face_distance(data["encodings"], face_encoding)
        if face_distances.size == 0:
            continue
        
        best_match_index = np.argmin(face_distances)
        if face_recognition.compare_faces([data["encodings"][best_match_index]], face_encoding, tolerance=0.4)[0]:
            user_id = data["ids"][best_match_index]
            name = data["names"][best_match_index]
            mark_attendance(user_id, name)

    root.after(1000, recognize_faces)


def log(message):
    """ Menampilkan log secara efisien tanpa menghambat UI """
    log_box.insert(tk.END, message + "\n")
    log_box.see(tk.END)
    root.after_idle(log_box.update_idletasks)


def process_face(frame):
    """ Deteksi wajah pada thread terpisah untuk meningkatkan performa """
    if frame is None or frame.size == 0:
        return [], []
    
    face_locations = face_recognition.face_locations(frame)
    return face_locations, face_recognition.face_encodings(frame, face_locations)


def update_frame():
    """ Mengupdate frame video dan menampilkan hasil deteksi wajah """
    ret, frame = cap.read()
    if not ret:
        video_label.after(10, update_frame)
        return

    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(process_face, frame_rgb)
        face_locations, face_encodings = future.result()

    for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
        face_distances = face_recognition.face_distance(data["encodings"], face_encoding)
        if face_distances.size == 0:
            continue

        best_match_index = np.argmin(face_distances)
        if face_recognition.compare_faces([data["encodings"][best_match_index]], face_encoding, tolerance=0.5)[0]:
            user_id = data["ids"][best_match_index]
            name = data["names"][best_match_index]
        else:
            user_id, name = "", "Unknown"

        label = f"{name.split()[0]} ({user_id})"  # Hanya tampilkan nama depan
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
        cv2.putText(frame, label, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = ImageTk.PhotoImage(Image.fromarray(frame_rgb))
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
update_frame()

root.mainloop()
cap.release()
cv2.destroyAllWindows()
