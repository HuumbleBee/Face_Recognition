import cv2
import face_recognition
import pickle
import os
import numpy as np
import sys

ENCODINGS_FILE = "encodings.pickle"
DATASET_DIR = "dataset"  # Folder untuk menyimpan foto wajah
CAPTURE_COUNT = 5  # Jumlah foto yang harus diambil

# Pastikan folder dataset ada
if not os.path.exists(DATASET_DIR):
    os.makedirs(DATASET_DIR)

# Load encoding wajah yang sudah ada jika file tersedia
if os.path.exists(ENCODINGS_FILE):
    with open(ENCODINGS_FILE, "rb") as f:
        data = pickle.load(f)
else:
    data = {"encodings": [], "names": []}

# Fungsi untuk mengecek apakah wajah sudah terdaftar
def is_face_registered(face_encoding):
    return any(face_recognition.compare_faces(data["encodings"], face_encoding))

# Ambil nama dari argumen (GUI)
if len(sys.argv) < 2:
    print("Harap masukkan nama pengguna sebagai argumen!")
    exit()

name = sys.argv[1].strip()
if not name:
    print("Nama tidak boleh kosong!")
    exit()

print(f"Memulai registrasi untuk: {name}")

# Buat folder user jika belum ada
user_folder = os.path.join(DATASET_DIR, name)
if not os.path.exists(user_folder):
    os.makedirs(user_folder)

# Inisialisasi kamera
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Gagal mengakses kamera!")
    exit()

captured_faces = []
count = 0

print("Tekan 'c' untuk mengambil gambar (5 kali). Tekan 'q' untuk keluar.")

while count < CAPTURE_COUNT:
    ret, frame = cap.read()
    if not ret:
        print("Gagal menangkap frame dari kamera!")
        break

    # Tampilkan kamera dengan OpenCV
    cv2.imshow("Registrasi Wajah", frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        print("Registrasi dibatalkan oleh pengguna.")
        break  # Keluar dari loop jika 'q' ditekan
    elif key == ord('c'):
        print(f"Mengambil gambar {count+1}/{CAPTURE_COUNT}...")

        # Simpan gambar ke folder dataset
        img_path = os.path.join(user_folder, f"{name}_{count+1}.jpg")
        cv2.imwrite(img_path, frame)

        # Proses encoding wajah
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        if face_encodings:
            face_encoding = face_encodings[0]

            # Cek apakah wajah sudah terdaftar
            if is_face_registered(face_encoding):
                print("Wajah ini sudah terdaftar! Registrasi dibatalkan.")
                os.remove(img_path)  # Hapus gambar jika wajah sudah ada
                break  # Hentikan registrasi

            captured_faces.append(face_encoding)
            count += 1  # Tambah hitungan capture

if captured_faces:
    # Simpan encoding ke data
    data["encodings"].extend(captured_faces)
    data["names"].extend([name] * len(captured_faces))

    # Simpan encoding ke file pickle
    with open(ENCODINGS_FILE, "wb") as f:
        pickle.dump(data, f)

    print(f"{count} gambar wajah {name} berhasil disimpan!")

cap.release()
cv2.destroyAllWindows()
