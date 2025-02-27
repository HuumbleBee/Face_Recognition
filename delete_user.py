import pickle
import os
import shutil

ENCODINGS_FILE = "encodings.pickle"
DATASET_DIR = "dataset"

def delete_user(name):
    if not os.path.exists(ENCODINGS_FILE):
        print("Database encoding tidak ditemukan!")
        return

    # Load data encoding yang ada
    with open(ENCODINGS_FILE, "rb") as f:
        data = pickle.load(f)

    # Filter untuk menghapus user dari database
    new_encodings = []
    new_names = []
    for encoding, stored_name in zip(data["encodings"], data["names"]):
        if stored_name != name:
            new_encodings.append(encoding)
            new_names.append(stored_name)

    if len(new_names) == len(data["names"]):
        print(f"Tidak ada user bernama '{name}' dalam database.")
    else:
        # Simpan ulang encoding tanpa user yang dihapus
        with open(ENCODINGS_FILE, "wb") as f:
            pickle.dump({"encodings": new_encodings, "names": new_names}, f)
        print(f"User '{name}' berhasil dihapus dari database face recognition!")

    # Hapus foto dari dataset jika ada
    user_folder = os.path.join(DATASET_DIR, name)
    if os.path.exists(user_folder):
        shutil.rmtree(user_folder)  # Hapus folder user
        print(f"Semua foto user '{name}' telah dihapus dari dataset.")

# Input nama user yang ingin dihapus
name_to_delete = input("Masukkan nama user yang ingin dihapus: ").strip()
delete_user(name_to_delete)
