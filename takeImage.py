import cv2
import os
import mysql.connector
from mysql.connector import Error
import tkinter as tk
from tkinter import ttk

MYSQL_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "okucan123",
    "database": "CameraAttendance"
}

def TakeImage(user_id, teacher_group, haarcasecade_path, trainimage_path, text_to_speech):
    if user_id == "":
        text_to_speech("ERROR USE ID")
        return False
    
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT username FROM users WHERE user_id=%s AND group_name=%s AND role='Student' AND approved=1",
            (user_id, teacher_group)
        )
        result = cursor.fetchone()
        
        print(result)

        if result:
            username = result[0]
        else:
            text_to_speech("User not found in the database.")
            return False

        Enrollment = user_id
        Name = username
        
        cam = cv2.VideoCapture(0)
        detector = cv2.CascadeClassifier(haarcasecade_path)
        sampleNum = 0
        
        directory = Enrollment
        path = os.path.join(trainimage_path, directory)
        os.mkdir(path)
        
        while True:
            ret, img = cam.read()
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = detector.detectMultiScale(gray, 1.3, 5)
            for (x, y, w, h) in faces:
                cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
                sampleNum = sampleNum + 1
                cv2.imwrite(f"{path}\\ "+ Name+ "_"+ Enrollment+ "_"+ str(sampleNum)+ ".jpg",gray[y : y + h, x : x + w],)
                cv2.imshow("Frame", img)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
            elif sampleNum > 50:
                break
           
        cam.release()
        cv2.destroyAllWindows()
        
        res = f"Images Updated for User ID: {user_id}, Name: {username}, Group: {teacher_group}"
        text_to_speech(res)
        return True
        
    except Error as e:
        text_to_speech(f"Database Error: {e}")
        return False 
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()