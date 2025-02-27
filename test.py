import cv2
import tkinter as tk
from PIL import Image, ImageTk

class FaceRecognitionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Face Recognition Attendance")
        self.root.geometry("800x600")

        # Label untuk menampilkan video
        self.video_label = tk.Label(root)
        self.video_label.pack()

        # Tombol untuk memulai kamera
        self.btn_start_camera = tk.Button(root, text="Start Camera", command=self.start_camera, font=("Arial", 12), bg="#2196F3", fg="white")
        self.btn_start_camera.pack(pady=10)

        # Tombol untuk berhenti
        self.btn_stop_camera = tk.Button(root, text="Stop Camera", command=self.stop_camera, font=("Arial", 12), bg="#f44336", fg="white")
        self.btn_stop_camera.pack(pady=10)

        self.cap = None
        self.running = False

    def start_camera(self):
        """Memulai kamera dan menampilkan di GUI."""
        if self.cap is None:
            self.cap = cv2.VideoCapture(0)  # Menggunakan kamera default (index 0)
            self.running = True
            self.update_frame()

    def update_frame(self):
        """Mengambil frame dari kamera dan menampilkannya di GUI."""
        if self.running and self.cap is not None:
            ret, frame = self.cap.read()
            if ret:
                # Konversi warna dari BGR ke RGB
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame)
                imgtk = ImageTk.PhotoImage(image=img)

                # Tampilkan gambar ke dalam label
                self.video_label.imgtk = imgtk
                self.video_label.configure(image=imgtk)

            # Looping untuk update frame setiap 10 ms
            self.root.after(10, self.update_frame)

    def stop_camera(self):
        """Menghentikan kamera dan membersihkan tampilan."""
        self.running = False
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        self.video_label.configure(image='')

# Jalankan aplikasi
if __name__ == "__main__":
    root = tk.Tk()
    app = FaceRecognitionApp(root)
    root.mainloop()
