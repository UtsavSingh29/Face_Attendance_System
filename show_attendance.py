import tkinter as tk
from tkinter import *
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

def subjectchoose(text_to_speech, group_name=""):
    def setup_styles():
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TButton', font=('Verdana', 12), padding=10)
        style.configure('TLabel', font=('Verdana', 14), background='black', foreground='yellow')
        style.configure('TEntry', font=('Verdana', 12), fieldbackground='#333333', foreground='yellow')
        style.configure('Primary.TButton', background='#4CAF50', foreground='white')
        style.map('Primary.TButton', background=[('active', '#45a049')])

    def calculate_attendance():
        subject = tx.get().strip()
        if subject == "":
            t = "Please enter the subject name."
            text_to_speech(t)
            notifica.configure(text=t, style='TLabel')
            return
        
        try:
            conn = mysql.connector.connect(**MYSQL_CONFIG)
            cursor = conn.cursor()
            
            query = """
                SELECT a.user_id, u.username, a.date, a.subject, a.status, a.attendance_count
                FROM attendance a
                JOIN users u ON a.user_id = u.user_id
                WHERE a.subject=%s AND a.group_name=%s
                ORDER BY a.date DESC
            """
            cursor.execute(query, (subject, group_name))
            records = cursor.fetchall()
            
            if not records:
                t = f"No attendance records found for {subject} in group {group_name}."
                text_to_speech(t)
                notifica.configure(text=t, style='TLabel')
                return
            
            root = tk.Tk()
            root.title(f"Attendance of {subject} for Group {group_name}")
            root.configure(background="black")
            root.state('zoomed')
            
            headers = ["User ID", "Username", "Date", "Subject", "Status", "Count"]
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
            t = f"Database Error: {e}"
            text_to_speech(t)
            notifica.configure(text=t, style='TLabel')
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

    def view_all_subjects():
        try:
            conn = mysql.connector.connect(**MYSQL_CONFIG)
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT DISTINCT subject FROM attendance WHERE group_name=%s",
                (group_name,)
            )
            subjects = cursor.fetchall()
            
            if not subjects:
                t = f"No subjects found for group {group_name}."
                text_to_speech(t)
                notifica.configure(text=t, style='TLabel')
                return
            
            root = tk.Tk()
            root.title(f"All Subjects for Group {group_name}")
            root.configure(background="black")
            root.state('zoomed')
            
            for r, subject in enumerate(subjects, start=0):
                label = tk.Label(
                    root,
                    width=20,
                    height=1,
                    fg="yellow",
                    font=("times", 15, "bold"),
                    bg="black",
                    text=subject[0],
                    relief=tk.RIDGE,
                )
                label.grid(row=r, column=0)
            
            root.mainloop()
        
        except Error as e:
            t = f"Database Error: {e}"
            text_to_speech(t)
            notifica.configure(text=t, style='TLabel')
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

    def check_sheets():
        subject = tx.get().strip()
        if subject == "":
            t = "Please enter the subject name!"
            text_to_speech(t)
            notifica.configure(text=t, style='TLabel')
        else:
            try:
                conn = mysql.connector.connect(**MYSQL_CONFIG)
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT DISTINCT subject FROM attendance WHERE group_name=%s AND subject=%s",
                    (group_name, subject)
                )
                if cursor.fetchone():
                    t = f"Subject {subject} exists in group {group_name}."
                    text_to_speech(t)
                    notifica.configure(text=t, style='TLabel')
                else:
                    t = f"No records for {subject} in group {group_name}."
                    text_to_speech(t)
                    notifica.configure(text=t, style='TLabel')
            except Error as e:
                t = f"Database Error: {e}"
                text_to_speech(t)
                notifica.configure(text=t, style='TLabel')
            finally:
                if conn.is_connected():
                    cursor.close()
                    conn.close()

    subject = tk.Tk()
    setup_styles()
    subject.title("Subject...")
    subject.state('zoomed')
    subject.configure(background="black")

    titl = tk.Label(subject, bg="black", relief=RIDGE, bd=10, font=("arial", 30))
    titl.pack(fill=X)
    ttk.Label(
        subject,
        text=f"Which Subject for Group {group_name}?",
        style='TLabel',
        font=("arial", 25),
    ).place(relx=0.5, y=12, anchor='n')

    notifica = ttk.Label(
        subject,
        text="",
        style='TLabel',
        width=40,
    )
    notifica.place(relx=0.5, rely=0.8, anchor='center')

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
        text="View Attendance",
        command=calculate_attendance,
        style='Primary.TButton',
    ).pack(side="left", padx=10)

    ttk.Button(
        button_frame,
        text="Check Sheets",
        command=check_sheets,
        style='Primary.TButton',
    ).pack(side="left", padx=10)

    ttk.Button(
        button_frame,
        text="All Subjects",
        command=view_all_subjects,
        style='Primary.TButton',
    ).pack(side="left", padx=10)

    subject.mainloop()