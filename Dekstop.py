import cv2
import face_recognition
import pickle
import os
import numpy as np
import csv
import datetime
import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk

ENCODINGS_FILE = "encodings.pickle"
DATASET_DIR = "dataset"
ATTENDANCE_FILE = "attendance.csv"
CAPTURE_COUNT = 5
ATTENDANCE_INTERVAL = 7200  # 2 hours in seconds

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
    while count < CAPTURE_COUNT:
        ret, frame = cap.read()
        if not ret:
            log("Gagal menangkap frame dari kamera!")
            break
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
    if captured_faces:
        data["encodings"].extend(captured_faces)
        data["names"].extend([name] * len(captured_faces))
        data["ids"].extend([user_id] * len(captured_faces))
        with open(ENCODINGS_FILE, "wb") as f:
            pickle.dump(data, f)
        log(f"{count} gambar wajah {name} berhasil disimpan!")

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

def mark_attendance(user_id, name):
    now = datetime.datetime.now()
    if user_id in last_attendance and (now - last_attendance[user_id]).total_seconds() < ATTENDANCE_INTERVAL:
        log(f"{name} ({user_id}) sudah absen dalam 2 jam terakhir!")
        return
    last_attendance[user_id] = now
    with open(ATTENDANCE_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([user_id, name, now.strftime("%Y-%m-%d %H:%M:%S")])
    log(f"Kehadiran dicatat: {name} ({user_id})")

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

def update_frame():
    ret, frame = cap.read()
    if ret:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame)
        img = ImageTk.PhotoImage(img)
        video_label.img = img
        video_label.config(image=img)
    video_label.after(10, update_frame)

root = tk.Tk()
root.title("Face Recognition System")
root.geometry(f"{root.winfo_screenwidth()}x{root.winfo_screenheight()}")
root.configure(bg="#333")

video_label = tk.Label(root)
video_label.pack(pady=10)
log_box = tk.Text(root, height=10, width=80, bg="#222", fg="white")
log_box.pack(pady=10)

frame = tk.Frame(root, bg="#333")
frame.pack()
tk.Label(frame, text="ID:", fg="white", bg="#333").grid(row=0, column=0)
id_entry = tk.Entry(frame)
id_entry.grid(row=0, column=1)
tk.Label(frame, text="Nama:", fg="white", bg="#333").grid(row=1, column=0)
name_entry = tk.Entry(frame)
name_entry.grid(row=1, column=1)

register_button = tk.Button(frame, text="Register", command=register_user, bg="#4CAF50", fg="white")
register_button.grid(row=2, column=0, pady=10)
delete_button = tk.Button(frame, text="Delete", command=delete_user, bg="#f44336", fg="white")
delete_button.grid(row=2, column=1, pady=10)
attendance_button = tk.Button(frame, text="Attendance", command=recognize_faces, bg="#4CAF50", fg="white")
attendance_button.grid(row=2, column=2, pady=10)

cap = cv2.VideoCapture(0)
update_frame()

root.mainloop()
cap.release()
cv2.destroyAllWindows()
