import os
import cv2
import numpy as np
from PIL import Image

def TrainImage(haarcasecade_path, trainimage_path, trainimagelabel_path, text_to_speech):
    try:
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        detector = cv2.CascadeClassifier(haarcasecade_path)
        
        if detector.empty():
            text_to_speech("Failed to load Haar cascade file!")
            return
        
        faces = []
        ids = []
        
        for root, dirs, files in os.walk(trainimage_path):
            for file in files:
                if file.endswith("jpg"):
                    path = os.path.join(root, file)
                    user_id = os.path.basename(root) 
                    try:
                        img = Image.open(path).convert('L')  
                        img_np = np.array(img, 'uint8')
                        face = detector.detectMultiScale(img_np)

                        if len(face) == 0:
                            print(f"No face found in: {path}")
                            continue

                        for (x, y, w, h) in face:
                            faces.append(img_np[y:y+h, x:x+w])
                            ids.append(int(user_id))
                    except Exception as e:
                        print(f"Error processing image {path}: {e}")
        
        if not faces:
            text_to_speech("No faces found in training images!")
            return
        
        recognizer.train(faces, np.array(ids, dtype=np.int32))
        os.makedirs(os.path.dirname(trainimagelabel_path), exist_ok=True)
        recognizer.write(trainimagelabel_path)
        
        text_to_speech("Image Trained Successfully!")
    
    except Exception as e:
        text_to_speech(f"Training Error: {e}")