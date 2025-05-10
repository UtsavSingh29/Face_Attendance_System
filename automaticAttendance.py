import tkinter as tk
from tkinter import messagebox, ttk
import os
import cv2
import numpy as np
import datetime
import time
import mysql.connector
from mysql.connector import Error

MYSQL_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "okucan123",
    "database": "CameraAttendance"
}

def run_attendance(group_name, trainimagelabel_path, haarcasecade_path, notifica_label):
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()

        if not os.path.exists(trainimagelabel_path):
            e = "No trained model found. Please train images first."
            notifica_label.configure(text=e, style='TLabel')
            return [], []
        
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        try:
            recognizer.read(trainimagelabel_path)
        except Exception as e:
            e = f"Failed to load trained model: {e}"
            notifica_label.configure(text=e, style='TLabel')
            return [], []
        
        face_cascade = cv2.CascadeClassifier(haarcasecade_path)
        if face_cascade.empty():
            e = "Failed to load Haar cascade file."
            notifica_label.configure(text=e, style='TLabel')
            return [], []

        cursor.execute("SELECT user_id, username FROM users WHERE group_name=%s AND role='Student' AND approved=1", (group_name,))
        students = cursor.fetchall()
        all_students = {str(row[0]): row[1] for row in students}
        present_students = set()

        cam = cv2.VideoCapture(0)
        if not cam.isOpened():
            raise Exception("Failed to open camera.")

        start_time = time.time()
        min_confidence = 100 

        while True:
            ret, frame = cam.read()
            if not ret:
                print("Warning: Failed to capture frame. Retrying...")
                time.sleep(0.1)
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.equalizeHist(gray)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.05, minNeighbors=10, minSize=(100, 100))

            for (x, y, w, h) in faces:
                face_roi = gray[y:y + h, x:x + w]
                face_roi = cv2.resize(face_roi, (200, 200))
                student_id, conf = recognizer.predict(face_roi)
                print(f"Detected ID: {student_id}, Confidence: {conf}")

                if conf < 80 and str(student_id) in all_students:
                    student_name = all_students[str(student_id)]
                    present_students.add(str(student_id))
                    label = f"{student_id}-{student_name} ({conf:.2f})"
                    min_confidence = min(min_confidence, conf)
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 4)
                    cv2.putText(frame, label, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 4)
                else:
                    print(f"Unknown face detected at ({x}, {y}, {w}, {h}) with confidence: {conf}")
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 4)
                    cv2.putText(frame, f"Unknown ({conf:.2f})", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 4)

            cv2.imshow("Auto Attendance (Preview Only)", frame)

            if cv2.waitKey(50) & 0xFF == 27:
                break
            if time.time() > start_time + 20:
                break

        cam.release()
        cv2.destroyAllWindows()

        all_ids = set(all_students.keys())
        absent_students = list(all_ids - present_students)
        present_students = list(present_students)

        print(f"Final Present Students: {present_students}")
        print(f"Final Absent Students: {absent_students}")

        m = f"Detected {len(present_students)} present, {len(absent_students)} absent."
        notifica_label.configure(text=m, style='TLabel')

        return present_students, absent_students

    except Exception as e:
        error_msg = f"Error during attendance: {str(e)}"
        notifica_label.configure(text=error_msg, style='TLabel')
        return [], []

    finally:
        if 'cam' in locals() and cam.isOpened():
            cam.release()
        cv2.destroyAllWindows()
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()