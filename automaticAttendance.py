import tkinter as tk
from tkinter import *
import os
import cv2
import numpy as np
import datetime
import time
import mysql.connector
from mysql.connector import Error
from tkinter import ttk

# MySQL Database Configuration
MYSQL_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "shoibk897",
    "database": "CameraAttendance"
}

haarcasecade_path = "haarcascade_frontalface_default.xml"
trainimagelabel_path = "TrainingImageLabel/Trainner.yml"
trainimage_path = "./TrainingImage"

def subjectChoose(text_to_speech, group_name, teacher_username):
    def setup_styles():
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TButton', font=('Verdana', 12), padding=10)
        style.configure('TLabel', font=('Verdana', 14), background='black', foreground='yellow')
        style.configure('TEntry', font=('Verdana', 12), fieldbackground='#333333', foreground='yellow')
        style.configure('Primary.TButton', background='#4CAF50', foreground='white')
        style.map('Primary.TButton', background=[('active', '#45a049')])

    def FillAttendance():
        sub = tx.get().strip()
        now = time.time()
        unknown_timeout = now + 5
        last_known_time = now
        
        if sub == "":
            t = "Please enter the subject name!"
            text_to_speech(t)
            Notifica.configure(text=t, style='TLabel')
            return
        
        try:
            conn = mysql.connector.connect(**MYSQL_CONFIG)
            cursor = conn.cursor()
            
            if not os.path.exists(trainimagelabel_path):
                e = "No trained model found. Please train images first."
                Notifica.configure(text=e, style='TLabel')
                text_to_speech(e)
                return
            
            recognizer = cv2.face.LBPHFaceRecognizer_create()
            try:
                recognizer.read(trainimagelabel_path)
            except Exception as e:
                e = f"Failed to load trained model: {e}"
                Notifica.configure(text=e, style='TLabel')
                text_to_speech(e)
                return
            
            facecasCade = cv2.CascadeClassifier(haarcasecade_path)
            if facecasCade.empty():
                e = "Failed to load Haar cascade file."
                Notifica.configure(text=e, style='TLabel')
                text_to_speech(e)
                return
            
            cam = cv2.VideoCapture(0)
            if not cam.isOpened():
                e = "Failed to open camera."
                Notifica.configure(text=e, style='TLabel')
                text_to_speech(e)
                return
            
            font = cv2.FONT_HERSHEY_SIMPLEX
            known_face_detected = False
            
            while True:
                ret, im = cam.read()
                if not ret:
                    e = "Failed to capture image from camera."
                    Notifica.configure(text=e, style='TLabel')
                    text_to_speech(e)
                    break
                
                gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
                faces = facecasCade.detectMultiScale(gray, 1.2, 5)
                current_time = time.time()
                unknown_detected = True
                
                for (x, y, w, h) in faces:
                    Id, conf = recognizer.predict(gray[y:y+h, x:x+w])
                    print(f"Detected ID: {Id}, Confidence: {conf}")  # Debug output
                    
                    if conf < 80:  # Relaxed threshold
                        cursor.execute(
                            "SELECT username FROM users WHERE user_id=%s AND group_name=%s AND approved=1",
                            (str(Id), group_name)
                        )
                        result = cursor.fetchone()
                        if result:
                            aa = result[0]
                            tt = f"{Id}-{aa}"
                            ts = time.time()
                            date = datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
                            timeStamp = datetime.datetime.fromtimestamp(ts).strftime("%H:%M:%S")
                            
                            cursor.execute(
                                """
                                SELECT id, attendance_count FROM attendance
                                WHERE user_id=%s AND group_name=%s AND subject=%s AND date=%s
                                """,
                                (str(Id), group_name, sub, date)
                            )
                            attendance_record = cursor.fetchone()
                            
                            if attendance_record:
                                cursor.execute(
                                    """
                                    UPDATE attendance
                                    SET attendance_count = attendance_count + 1,
                                        status = 'Present',
                                        timestamp = %s
                                    WHERE id = %s
                                    """,
                                    (timeStamp, attendance_record[0])
                                )
                            else:
                                cursor.execute(
                                    """
                                    INSERT INTO attendance (user_id, group_name, date, status, subject, attendance_count, timestamp)
                                    VALUES (%s, %s, %s, %s, %s, 1, %s)
                                    """,
                                    (str(Id), group_name, date, "Present", sub, timeStamp)
                                )
                            
                            conn.commit()
                            
                            cv2.rectangle(im, (x, y), (x+w, y+h), (0, 260, 0), 4)
                            cv2.putText(im, str(tt), (x+h, y), font, 1, (255, 255, 0), 4)
                            
                            known_face_detected = True
                            last_known_time = current_time
                            unknown_detected = False
                        else:
                            Id = "Unknown"
                            print(f"User ID {Id} not found or not approved.")  # Debug output
                    else:
                        Id = "Unknown"
                        print(f"Confidence too high: {conf}")  # Debug output
                    
                    if Id == "Unknown":
                        tt = str(Id)
                        cv2.rectangle(im, (x, y), (x+w, y+h), (0, 25, 255), 7)
                        cv2.putText(im, str(tt), (x+h, y), font, 1, (0, 25, 255), 4)
                
                if unknown_detected and current_time > last_known_time + 5:
                    m = "Unknown face detected for 5 seconds, stopping..."
                    Notifica.configure(text=m, style='TLabel')
                    text_to_speech(m)
                    break
                
                cv2.imshow("Filling Attendance...", im)
                key = cv2.waitKey(30) & 0xFF
                if key == 27:
                    break
                if known_face_detected and current_time > now + 20:
                    break
            
            cam.release()
            cv2.destroyAllWindows()
            
            if known_face_detected:
                m = f"Attendance Filled Successfully for {sub} in group {group_name}"
            else:
                m = "No known faces detected, attendance not recorded."
            Notifica.configure(text=m, style='TLabel')
            text_to_speech(m)
            
            if known_face_detected:
                root = tk.Tk()
                root.title(f"Attendance of {sub} for Group {group_name}")
                root.configure(background="black")
                root.state('zoomed')
                
                cursor.execute(
                    """
                    SELECT user_id, username, date, subject, attendance_count
                    FROM attendance a
                    JOIN users u ON a.user_id = u.user_id
                    WHERE a.group_name=%s AND a.subject=%s AND a.date=%s
                    """,
                    (group_name, sub, date)
                )
                records = cursor.fetchall()
                
                headers = ["User ID", "Username", "Date", "Subject", "Count"]
                for c, header in enumerate(headers):
                    label = tk.Label(
                        root,
                        width=15,
                        height=1,
                        fg="yellow",
                        font=("times", 15, "bold"),
                        bg="black",
                        text=header,
                        relief=tk.RIDGE,
                    )
                    label.grid(row=0, column=c)
                
                for r, record in enumerate(records, start=1):
                    for c, field in enumerate(record):
                        label = tk.Label(
                            root,
                            width=15,
                            height=1,
                            fg="yellow",
                            font=("times", 15, "bold"),
                            bg="black",
                            text=str(field),
                            relief=tk.RIDGE,
                        )
                        label.grid(row=r, column=c)
                
                root.mainloop()
        
        except Error as e:
            Notifica.configure(text=f"Database Error: {e}", style='TLabel')
            text_to_speech(f"Database Error: {e}")
        except Exception as e:
            Notifica.configure(text=f"Error: {e}", style='TLabel')
            text_to_speech(f"Error: {e}")
        finally:
            if 'conn' in locals() and conn.is_connected():
                cursor.close()
                conn.close()
    
    subject = tk.Tk()
    setup_styles()
    subject.title("Subject and Attendance")
    subject.state('zoomed')
    subject.configure(background="black")
    
    titl = tk.Label(subject, bg="black", relief=RIDGE, bd=10, font=("arial", 30))
    titl.pack(fill=X)
    ttk.Label(
        subject,
        text=f"Enter Subject for Group {group_name}",
        style='TLabel',
        font=("arial", 25),
    ).place(relx=0.5, y=12, anchor='n')
    
    Notifica = ttk.Label(
        subject,
        text="",
        style='TLabel',
        width=40,
    )
    Notifica.place(relx=0.5, rely=0.8, anchor='center')
    
    def check_sheets():
        sub = tx.get().strip()
        if sub == "":
            t = "Please enter the subject name!"
            text_to_speech(t)
            Notifica.configure(text=t, style='TLabel')
        else:
            try:
                conn = mysql.connector.connect(**MYSQL_CONFIG)
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT DISTINCT subject FROM attendance WHERE group_name=%s AND subject=%s",
                    (group_name, sub)
                )
                if cursor.fetchone():
                    t = f"Subject {sub} exists in group {group_name}."
                    text_to_speech(t)
                    Notifica.configure(text=t, style='TLabel')
                else:
                    t = f"No records for {sub} in group {group_name}."
                    text_to_speech(t)
                    Notifica.configure(text=t, style='TLabel')
            except Error as e:
                t = f"Database Error: {e}"
                text_to_speech(t)
                Notifica.configure(text=t, style='TLabel')
            finally:
                if conn.is_connected():
                    cursor.close()
                    conn.close()
    
    main_frame = ttk.Frame(subject)
    main_frame.place(relx=0.5, rely=0.5, anchor='center')
    
    ttk.Label(
        main_frame,
        text="Enter Subject",
        style='TLabel',
    ).grid(row=0, column=0, padx=10, pady=10, sticky='e')
    
    tx = ttk.Entry(
        main_frame,
        width=20,
        style='TEntry',
    )
    tx.grid(row=0, column=1, padx=10, pady=10)
    
    button_frame = ttk.Frame(main_frame)
    button_frame.grid(row=1, column=0, columnspan=2, pady=10)
    
    ttk.Button(
        button_frame,
        text="Fill Attendance",
        command=FillAttendance,
        style='Primary.TButton',
    ).pack(side="left", padx=10)
    
    ttk.Button(
        button_frame,
        text="Check Sheets",
        command=check_sheets,
        style='Primary.TButton',
    ).pack(side="left", padx=10)
    
    subject.mainloop()