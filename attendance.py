import cv2
import face_recognition
import pickle
import os
import csv
from datetime import datetime, timedelta

# Cek apakah file encoding tersedia
if not os.path.exists("encodings.pickle"):
    print("Error: File 'encodings.pickle' tidak ditemukan. Lakukan registrasi wajah terlebih dahulu!")
    exit()

# Load encoding wajah yang sudah terdaftar
with open("encodings.pickle", "rb") as f:
    data = pickle.load(f)

# Dictionary untuk menyimpan waktu absensi terakhir
last_attendance_time = {}

# Fungsi untuk mencatat absensi dengan delay 1 jam
def mark_attendance(name):
    global last_attendance_time
    file_path = "attendance.csv"
    current_time = datetime.now()

    # Cek apakah user sudah pernah tercatat
    if name in last_attendance_time:
        last_time = last_attendance_time[name]
        if (current_time - last_time) < timedelta(hours=1):
            print(f"{name} sudah absen, menunggu {60 - (current_time - last_time).seconds // 60} menit lagi.")
            return  # Tidak mencatat ulang jika belum 1 jam
    last_attendance_time[name] = current_time  # Update waktu absensi terakhir

    # Cek apakah file absensi sudah ada
    if not os.path.exists(file_path):
        with open(file_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Nama", "Waktu"])

    # Catat kehadiran
    with open(file_path, "a", newline="") as f:
        writer = csv.writer(f)
        waktu = current_time.strftime("%Y-%m-%d %H:%M:%S")
        writer.writerow([name, waktu])
        print(f"Absensi dicatat: {name} pada {waktu}")

# Buka kamera
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        print("Gagal mengakses kamera")
        break

    # Konversi frame ke RGB
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Deteksi wajah dalam frame
    face_locations = face_recognition.face_locations(rgb_frame)
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

    for face_encoding, face_location in zip(face_encodings, face_locations):
        # Bandingkan wajah dengan database
        matches = face_recognition.compare_faces(data["encodings"], face_encoding)
        name = "Unknown"

        # Ambil jarak terkecil jika ada kecocokan
        face_distances = face_recognition.face_distance(data["encodings"], face_encoding)
        best_match_index = face_distances.argmin() if len(face_distances) > 0 else -1

        if matches[best_match_index]:
            name = data["names"][best_match_index]
            mark_attendance(name)  # Catat absensi dengan aturan 1 jam

        # Gambar kotak dan label pada wajah yang terdeteksi
        top, right, bottom, left = face_location
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
        cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

    # Tampilkan hasil di jendela
    cv2.imshow("Sistem Absensi Face Recognition", frame)

    # Tekan 'q' untuk keluar
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
