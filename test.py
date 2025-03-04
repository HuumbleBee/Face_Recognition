import face_recognition_models
import os

model_path = face_recognition_models.pose_predictor_model_location
print("Model Path:", model_path)

# Cek apakah file benar-benar ada
print("File Exists:", os.path.exists(model_path))
