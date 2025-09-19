import pandas as pd
import cv2
import os
import numpy as np

imagesFolder = 'Images'
dataFolder = 'Data'

os.makedirs(dataFolder, exist_ok=True)

data = {
    "100000": {
        "name": "Sultansyah",
        "major": "CSE",
        "starting_year": 2020,
        "total_attendance": 0,
        "year": 4,
        "last_attendance_time": "2022-12-11 00:54:34"
    },
    "100001": {
        "name": "Emly Blunt",
        "major": "Economics",
        "starting_year": 2021,
        "total_attendance": 0,
        "year": 2,
        "last_attendance_time": "2022-12-11 00:54:34"
    },
    "100002": {
        "name": "Elon Musk",
        "major": "Science",
        "starting_year": 2020,
        "total_attendance": 0,
        "year": 2,
        "last_attendance_time": "2022-12-11 00:54:34"
    },
    "100003": {
        "name": "Anand",
        "major": "Physics",
        "starting_year": 2020,
        "total_attendance": 0,
        "year": 2,
        "last_attendance_time": "2022-12-11 00:54:34"
    }
}

csvPath = os.path.join(dataFolder, "students.csv")
df = pd.DataFrame.from_dict(data, orient='index').reset_index()
df.rename(columns={'index': 'id'}, inplace=True)
df.to_csv(csvPath, index=False)
print(f"✅ Student data saved to {csvPath}")

faces = []
labels = []

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

print("Collecting faces for LBPH training...")

for studentId in os.listdir(imagesFolder):
    studentFolder = os.path.join(imagesFolder, studentId)
    if not os.path.isdir(studentFolder):
        continue

    for imgName in os.listdir(studentFolder):
        imgPath = os.path.join(studentFolder, imgName)
        img = cv2.imread(imgPath, cv2.IMREAD_GRAYSCALE)
        if img is None:
            print(f"⚠️ Could not read {imgPath}, skipping...")
            continue

        faces_rects = face_cascade.detectMultiScale(img, scaleFactor=1.2, minNeighbors=5)
        if len(faces_rects) == 0:
            print(f"⚠️ No face found in {imgPath}, skipping...")
            continue

        (x, y, w, h) = faces_rects[0]
        face_roi = img[y:y+h, x:x+w]
        face_resized = cv2.resize(face_roi, (200, 200))

        faces.append(face_resized)
        labels.append(int(studentId))

print(f"✅ Collected {len(faces)} face images for training")

if len(faces) > 0:
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.train(faces, np.array(labels))

    modelPath = os.path.join(dataFolder, "face_model.yml")
    recognizer.save(modelPath)
    print(f"✅ LBPH model trained and saved to {modelPath}")
else:
    print("❌ No valid training images found. Training aborted.")