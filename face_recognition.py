import tkinter as tk
from tkinter import *
from tkinter import ttk
import os
import cv2
import numpy as np
from PIL import ImageTk, Image
import mysql.connector
from mysql.connector import Error
import pandas as pd
import datetime
import time
import tkinter.font as font
import pyttsx3
import sys
import getopt

# Project modules
import show_attendance
import takeImage
import trainImage
import automaticAttendance

MYSQL_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "shoibk897",
    "database": "CameraAttendance"
}

def text_to_speech(user_text):
    engine = pyttsx3.init()
    engine.say(user_text)
    engine.runAndWait()

haarcasecade_path = "haarcascade_frontalface_default.xml"
trainimagelabel_path = "TrainingImageLabel/Trainner.yml"
trainimage_path = "./TrainingImage"
if not os.path.exists(trainimage_path):
    os.makedirs(trainimage_path)

def setup_styles():
    style = ttk.Style()
    style.theme_use('clam')
    style.configure('TButton', font=('Verdana', 12), padding=10)
    style.configure('TLabel', font=('Verdana', 14), background='#1c1c1c', foreground='yellow')
    style.configure('TEntry', font=('Verdana', 12), fieldbackground='#333333', foreground='yellow')
    style.configure('Primary.TButton', background='#4CAF50', foreground='white')
    style.map('Primary.TButton', background=[('active', '#45a049')])
    style.configure('Warning.TButton', background='#ff9800', foreground='black')
    style.map('Warning.TButton', background=[('active', '#e68a00')])

def main(argv):
    teacher_username = ""
    group_name = ""
    try:
        opts, args = getopt.getopt(argv, "", ["teacher_username=", "group_name="])
    except getopt.GetoptError:
        print("facerecognition.py --teacher_username <username> --group_name <group>")
        sys.exit(2)
    for opt, arg in opts:
        if opt == "--teacher_username":
            teacher_username = arg
        elif opt == "--group_name":
            group_name = arg
    
    window = tk.Tk()
    setup_styles()
    window.title("Face Recognizer")
    window.state('zoomed')
    window.configure(background="#1c1c1c")

    def del_sc1():
        sc1.destroy()

    def err_screen():
        global sc1
        sc1 = tk.Tk()
        sc1.geometry("400x110")
        sc1.title("Warning!!")
        sc1.configure(background="#1c1c1c")
        sc1.resizable(0, 0)
        ttk.Label(
            sc1,
            text="Please select a student!!!",
            style='TLabel',
        ).pack(pady=10)
        ttk.Button(
            sc1,
            text="OK",
            command=del_sc1,
            style='Primary.TButton',
        ).pack(pady=10)

    logo = Image.open("UI_Image/0001.png")
    logo = logo.resize((50, 47), Image.LANCZOS)
    logo1 = ImageTk.PhotoImage(logo)
    titl = tk.Label(window, bg="#1c1c1c", relief=RIDGE, bd=10, font=("Verdana", 30, "bold"))
    titl.pack(fill=X)
    l1 = tk.Label(window, image=logo1, bg="#1c1c1c")
    l1.place(relx=0.5, y=10, anchor='n')

    titl = tk.Label(
        window, text="CLASS VISION", bg="#1c1c1c", fg="yellow", font=("Verdana", 27, "bold")
    )
    titl.place(relx=0.5, y=12, anchor='n')

    a = tk.Label(
        window,
        text=f"Welcome to CLASS VISION (Group: {group_name})",
        bg="#1c1c1c",
        fg="yellow",
        bd=10,
        font=("Verdana", 35, "bold"),
    )
    a.pack(pady=20)

    ri = Image.open("UI_Image/register.png")
    ri = ri.resize((150, 150), Image.LANCZOS)
    r = ImageTk.PhotoImage(ri)
    label1 = Label(window, image=r)
    label1.image = r
    label1.place(relx=0.2, rely=0.5, anchor='center')

    ai = Image.open("UI_Image/attendance.png")
    ai = ai.resize((150, 150), Image.LANCZOS)
    a = ImageTk.PhotoImage(ai)
    label2 = Label(window, image=a)
    label2.image = a
    label2.place(relx=0.8, rely=0.5, anchor='center')

    vi = Image.open("UI_Image/verifyy.png")
    vi = vi.resize((150, 150), Image.LANCZOS)
    v = ImageTk.PhotoImage(vi)
    label3 = Label(window, image=v)
    label3.image = v
    label3.place(relx=0.5, rely=0.5, anchor='center')

    def TakeImageUI():
        ImageUI = tk.Tk()
        ImageUI.title("Update Student Face Images")
        ImageUI.state('zoomed')
        ImageUI.configure(background="#1c1c1c")
        ImageUI.resizable(0, 0)
        
        titl = tk.Label(ImageUI, bg="#1c1c1c", relief=RIDGE, bd=10, font=("Verdana", 30, "bold"))
        titl.pack(fill=X)
        ttk.Label(
            ImageUI, text="Update Student Face Images", style='TLabel', font=("Verdana", 30, "bold")
        ).place(relx=0.5, y=12, anchor='n')

        main_frame = ttk.Frame(ImageUI, style='TFrame')
        main_frame.place(relx=0.5, rely=0.5, anchor='center')

        ttk.Label(
            main_frame,
            text="Select Student",
            style='TLabel',
            font=("Verdana", 24, "bold"),
        ).grid(row=0, column=0, columnspan=2, pady=20)

        ttk.Label(
            main_frame,
            text="Student",
            style='TLabel',
        ).grid(row=1, column=0, padx=10, pady=10, sticky='e')
        
        # Fetch approved students in the group
        try:
            conn = mysql.connector.connect(**MYSQL_CONFIG)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT user_id, username FROM users WHERE role='Student' AND group_name=%s AND approved=1 ORDER BY username",
                (group_name,)
            )
            students = cursor.fetchall()
            student_options = [f"{user_id} - {username}" for user_id, username in students]
            student_ids = [user_id for user_id, _ in students]
        except Error as e:
            student_options = []
            student_ids = []
            tk.messagebox.showerror("Database Error", f"Failed to fetch students: {e}")
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
        
        if not student_options:
            ttk.Label(
                main_frame,
                text="No approved students in this group!",
                style='TLabel',
            ).grid(row=1, column=1, padx=10, pady=10)
            return
        
        student_var = tk.StringVar()
        student_dropdown = ttk.Combobox(
            main_frame,
            textvariable=student_var,
            values=student_options,
            state='readonly',
            width=30,
            font=('Verdana', 12)
        )
        student_dropdown.grid(row=1, column=1, padx=10, pady=10)
        student_dropdown.current(0)

        ttk.Label(
            main_frame,
            text="Notification",
            style='TLabel',
        ).grid(row=2, column=0, padx=10, pady=10, sticky='e')
        message = ttk.Label(
            main_frame,
            text="Select a student and update their face images, then train!",
            style='TLabel',
            width=40,
        )
        message.grid(row=2, column=1, padx=10, pady=10)

        def take_image():
            selected = student_var.get()
            if not selected:
                err_screen()
                return
            user_id = student_ids[student_options.index(selected)]
            takeImage.TakeImage(
                user_id,
                group_name,
                haarcasecade_path,
                trainimage_path,
                message,
                err_screen,
                text_to_speech,
            )

        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=20)
        ttk.Button(
            button_frame,
            text="Take Image",
            command=take_image,
            style='Primary.TButton',
        ).pack(side="left", padx=10)
        
        def train_image():
            trainImage.TrainImage(
                haarcasecade_path,
                trainimage_path,
                trainimagelabel_path,
                message,
                text_to_speech,
            )

        ttk.Button(
            button_frame,
            text="Train Image",
            command=train_image,
            style='Primary.TButton',
        ).pack(side="left", padx=10)

    r = ttk.Button(
        window,
        text="Update student face images",
        command=TakeImageUI,
        style='Primary.TButton',
        width=20,
    )
    r.place(relx=0.2, rely=0.8, anchor='center')

    def automatic_attendance():
        try:
            conn = mysql.connector.connect(**MYSQL_CONFIG)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM users WHERE group_name=%s AND role='Student' AND approved=1",
                (group_name,)
            )
            approved_students = cursor.fetchone()[0]
            if approved_students == 0:
                m = "No approved students in this group. Register and approve students first."
                text_to_speech(m)
                tk.messagebox.showwarning("Warning", m)
                return
        except Error as e:
            tk.messagebox.showerror("Database Error", f"Failed to check approved students: {e}")
            return
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
        
        automaticAttendance.subjectChoose(text_to_speech, group_name, teacher_username)

    r = ttk.Button(
        window,
        text="Take Attendance",
        command=automatic_attendance,
        style='Primary.TButton',
        width=20,
    )
    r.place(relx=0.5, rely=0.8, anchor='center')

    def view_attendance():
        show_attendance.subjectchoose(text_to_speech, group_name)

    r = ttk.Button(
        window,
        text="View Attendance",
        command=view_attendance,
        style='Primary.TButton',
        width=20,
    )
    r.place(relx=0.8, rely=0.8, anchor='center')

    r = ttk.Button(
        window,
        text="EXIT",
        command=window.quit,
        style='Warning.TButton',
        width=20,
    )
    r.place(relx=0.5, rely=0.9, anchor='center')

    window.mainloop()

if __name__ == "__main__":
    main(sys.argv[1:])