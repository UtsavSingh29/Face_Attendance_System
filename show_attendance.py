import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector
from mysql.connector import Error
from tkcalendar import DateEntry
from datetime import datetime

MYSQL_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "okucan123",
    "database": "CameraAttendance"
}

def fetch_subjects(group_name):
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT subject_name FROM attendance_session WHERE group_name=%s", (group_name,))
        subjects = [row[0] for row in cursor.fetchall()]
        return subjects
    except Error as e:
        messagebox.showerror("Database Error", f"Failed to fetch subjects: {e}")
        return []
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def fetch_attendance(group_name, subject_name, selected_date=None):
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()

        if selected_date:
            query = """
                SELECT
                    u.username,
                    s.subject_name,
                    s.session_date,
                    COUNT(a.id) AS total_sessions,
                    SUM(a.status = 1) AS present_count,
                    SUM(a.status = 0) AS absent_count,
                    ROUND(SUM(a.status = 1) / COUNT(a.id) * 100, 2) AS attendance_percentage
                FROM
                    users u
                JOIN
                    attendance a ON u.user_id = a.student_id
                JOIN
                    attendance_session s ON a.session_id = s.id
                WHERE
                    s.group_name = %s
                    AND s.subject_name = %s
                    AND s.session_date = %s
                GROUP BY
                    u.user_id, s.subject_name, s.session_date
                ORDER BY
                    u.username
            """
            params = [group_name, subject_name, selected_date]
        else:
            query = """
                SELECT
                    u.username,
                    s.subject_name,
                    NULL as session_date,
                    COUNT(a.id) AS total_sessions,
                    SUM(a.status = 1) AS present_count,
                    SUM(a.status = 0) AS absent_count,
                    ROUND(SUM(a.status = 1) / COUNT(a.id) * 100, 2) AS attendance_percentage
                FROM
                    users u
                JOIN
                    attendance a ON u.user_id = a.student_id
                JOIN
                    attendance_session s ON a.session_id = s.id
                WHERE
                    s.group_name = %s
                    AND s.subject_name = %s
                GROUP BY
                    u.user_id, s.subject_name
                ORDER BY
                    u.username
            """
            params = [group_name, subject_name]

        cursor.execute(query, params)
        records = cursor.fetchall()
        return records
    except Error as e:
        messagebox.showerror("Database Error", f"Failed to fetch attendance: {e}")
        return []
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def fetch_overall_percentage(group_name, subject_name):
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        query = """
            SELECT
                u.username,
                s.subject_name,
                COUNT(a.id) AS total_sessions,
                SUM(a.status = 1) AS present_count,
                SUM(a.status = 0) AS absent_count,
                ROUND(SUM(a.status = 1) / COUNT(a.id) * 100, 2) AS attendance_percentage
            FROM
                users u
            JOIN
                attendance a ON u.user_id = a.student_id
            JOIN
                attendance_session s ON a.session_id = s.id
            WHERE
                s.group_name = %s
                AND s.subject_name = %s
            GROUP BY
                u.user_id, s.subject_name
            ORDER BY
                u.username
        """
        params = [group_name, subject_name]
        cursor.execute(query, params)
        records = cursor.fetchall()
        return records
    except Error as e:
        messagebox.showerror("Database Error", f"Failed to fetch overall percentage: {e}")
        return []
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def subjectchoose(set_notification, group_name):
    window = tk.Toplevel()
    window.title("View Attendance")
    window.state('zoomed')
    window.configure(bg='#f0f0f0')

    style = ttk.Style()
    style.configure('TButton', font=('Verdana', 10), padding=10)
    style.configure('TLabel', font=('Verdana', 14))
    style.configure('Primary.TButton', background='#4CAF50', foreground='white')
    style.map('Primary.TButton', background=[('active', '#45a049')])

    subjects = fetch_subjects(group_name)
    if not subjects:
        set_notification("No subjects found for this group.")
        window.destroy()
        return

    notification_label = ttk.Label(window, text="", font=("Verdana", 12), foreground="red", background='#f0f0f0')
    notification_label.pack(pady=10)

    ttk.Label(window, text="Select Subject:", font=("Verdana", 14)).pack(pady=10)
    subject_var = tk.StringVar()
    subject_dropdown = ttk.Combobox(window, textvariable=subject_var, values=subjects, state='readonly', width=30, font=('Verdana', 12))
    subject_dropdown.pack(pady=10)
    subject_dropdown.current(0)

    ttk.Label(window, text="Select Date:", font=("Verdana", 14)).pack(pady=10)
    date_entry = DateEntry(window, width=30, font=('Verdana', 12), date_pattern='yyyy-mm-dd', maxdate=datetime.now())
    date_entry.pack(pady=10)

    def show_attendance(selected_date=None):
        notification_label.config(text="")

        subject = subject_var.get()
        if not subject:
            notification_label.config(text="Please select a subject.")
            return

        date_str = selected_date if selected_date else (date_entry.get() if not selected_date else None)
        if date_str and selected_date is None:
            try:
                datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                notification_label.config(text="Invalid date format. Please select a valid date.")
                return

        records = fetch_attendance(group_name, subject, date_str)
        if not records:
            if date_str:
                notification_label.config(text=f"No data found for {subject} on {date_str}.")
            else:
                notification_label.config(text=f"No data found for {subject}.")
            return

        table_window = tk.Toplevel(window)
        table_window.title(f"Attendance for {subject}" + (f" on {date_str}" if date_str else ""))
        table_window.state('zoomed')
        table_window.configure(bg='#f0f0f0')

        headers = [
            "Username", 
            "Subject", 
            "Date", 
            "Total Sessions", 
            "Present", 
            "Absent", 
            "Attendance %"
        ]
        
        for c, header in enumerate(headers):
            label = tk.Label(
                table_window,
                width=10,
                height=1,
                fg="black",
                font=("times", 11, "bold"),
                bg="#f0f0f0",
                text=header,
                relief=tk.RIDGE,
            )
            label.grid(row=0, column=c, padx=2, pady=2)

        for r, record in enumerate(records, start=1):
            for c, field in enumerate(record):
                if field is None:
                    display_text = "N/A"
                elif c == 7: 
                    display_text = f"{float(field):.2f}%"
                else:
                    display_text = str(field)
                
                bg_color = "#f0f0f0" 
                if c == 7 and field is not None: 
                    percentage = float(field)
                    if percentage >= 75:
                        bg_color = "#90EE90" 
                    elif percentage >= 50:
                        bg_color = "#FFD700" 
                    else:
                        bg_color = "#FFB6C1"  

                label = tk.Label(
                    table_window,
                    width=10,
                    height=1,
                    fg="black",
                    font=("times", 11),
                    bg=bg_color,
                    text=display_text,
                    relief=tk.RIDGE,
                )
                label.grid(row=r, column=c, padx=2, pady=2)

        notification_label.config(text=f"Showing attendance for {subject}" + (f" on {date_str}" if date_str else " for all dates."))

    button_frame = ttk.Frame(window)
    button_frame.pack(pady=20)
    ttk.Button(button_frame, text="Show Attendance", command=lambda: show_attendance(), style='Primary.TButton').pack(side="left", padx=10)
    
    def show_percentage():
        subject = subject_var.get()
        if not subject:
            notification_label.config(text="Please select a subject.")
            return
        records = fetch_overall_percentage(group_name, subject)
        if not records:
            notification_label.config(text=f"No data found for {subject}.")
            return
        table_window = tk.Toplevel(window)
        table_window.title(f"Overall Percentage for {subject}")
        table_window.state('zoomed')
        table_window.configure(bg='#f0f0f0')
        headers = [
            "Username", 
            "Subject", 
            "Total Sessions", 
            "Present", 
            "Absent", 
            "Attendance %"
        ]
        for c, header in enumerate(headers):
            label = tk.Label(
                table_window,
                width=10,
                height=1,
                fg="black",
                font=("times", 11, "bold"),
                bg="#f0f0f0",
                text=header,
                relief=tk.RIDGE,
            )
            label.grid(row=0, column=c, padx=2, pady=2)
        for r, record in enumerate(records, start=1):
            display_row = [
                record[0], 
                record[1],
                record[2],
                record[3], 
                record[4], 
                f"{float(record[5]):.2f}%" 
            ]
            for c, field in enumerate(display_row):
                bg_color = "#f0f0f0"
                if c == 5:
                    percentage = float(record[5])
                    if percentage >= 75:
                        bg_color = "#90EE90"
                    elif percentage >= 50:
                        bg_color = "#FFD700"
                    else:
                        bg_color = "#FFB6C1"
                label = tk.Label(
                    table_window,
                    width=10,
                    height=1,
                    fg="black",
                    font=("times", 11),
                    bg=bg_color,
                    text=field,
                    relief=tk.RIDGE,
                )
                label.grid(row=r, column=c, padx=2, pady=2)
        notification_label.config(text=f"Showing overall percentage for {subject}.")
    ttk.Button(button_frame, text="View Percentage", command=show_percentage, style='Primary.TButton').pack(side="left", padx=10)