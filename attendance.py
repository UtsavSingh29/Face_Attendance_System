import tkinter as tk
from tkinter import messagebox, ttk
import mysql.connector
from mysql.connector import Error
import os
import uuid
import re
import shutil
from datetime import date, datetime
import threading
from tkcalendar import DateEntry

import show_attendance
import takeImage
import trainImage
import automaticAttendance

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

MYSQL_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "okucan123",
    "database": "CameraAttendance"
}

haarcasecade_path = "haarcascade_frontalface_default.xml"
trainimagelabel_path = "./TrainingImageLabel/Trainner.yml"
trainimage_path = "./TrainingImage"

def setup_db():
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                            user_id VARCHAR(50) PRIMARY KEY,
                            username VARCHAR(255) UNIQUE NOT NULL,
                            password VARCHAR(255) NOT NULL,
                            role VARCHAR(50) NOT NULL,
                            group_name VARCHAR(255) NOT NULL,
                            approved INTEGER DEFAULT 0
                        )''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS attendance_session (
                            id INTEGER PRIMARY KEY AUTO_INCREMENT,
                            teacher_id VARCHAR(50) NOT NULL,
                            subject_name VARCHAR(255) NOT NULL,
                            group_name VARCHAR(255) NOT NULL,
                            session_date DATE NOT NULL,
                            session_count INTEGER NOT NULL,
                            INDEX (teacher_id)
                        )''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS attendance (
                            id INTEGER PRIMARY KEY AUTO_INCREMENT,
                            session_id INTEGER NOT NULL,
                            student_id VARCHAR(50) NOT NULL,
                            status TINYINT NOT NULL,
                            date DATE NOT NULL,
                            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (session_id) REFERENCES attendance_session(id)
                        )''')
        
        try:
            cursor.execute("ALTER TABLE attendance_session ADD COLUMN session_date DATE NOT NULL ")
        except Error as e:
            if e.errno != 1060:  
                raise e
        
        conn.commit()
    except Error as e:
        messagebox.showerror("Database Error", f"Failed to set up database: {e}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def signup():
    username = username_entry.get().strip()
    password = password_entry.get().strip()
    role = role_var.get()
    group = group_entry.get().strip()
    user_id = user_id_entry.get().strip()

    if not username or not password or not group or not user_id:
        messagebox.showerror("Error", "All fields (including ID) are required!")
        return

    if not re.match("^[A-Za-z0-9]+$", group):
        messagebox.showerror("Error", "Group name must contain only letters (A-Z, a-z) or numbers (0-9)!")
        return

    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (user_id, username, password, role, group_name, approved) VALUES (%s, %s, %s, %s, %s, 0)",
                       (user_id, username, password, role, group))
        conn.commit()
        messagebox.showinfo("Signup Request Sent", "Wait for Admin Approval!")
    except Error as e:
        if e.errno == 1062:
            messagebox.showerror("Error", "This ID or username is already in use!")
        else:
            messagebox.showerror("Database Error", f"Signup failed: {e}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def check_login(username, password, role):
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s AND role=%s AND approved=1 AND user_id=%s",
                       (username, password, role, user_id_entry.get().strip()))
        result = cursor.fetchone()
        return result
    except Error as e:
        messagebox.showerror("Database Error", f"Login check failed: {e}")
        return None
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def fetch_subjects(student_id=None, group_name=None):
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        if student_id:
            cursor.execute("""
                SELECT DISTINCT s.subject_name 
                FROM attendance_session s
                JOIN attendance a ON s.id = a.session_id
                WHERE a.student_id=%s
            """, (student_id,))
        elif group_name:
            cursor.execute("SELECT DISTINCT subject_name FROM attendance_session WHERE group_name=%s", (group_name,))
        else:
            return []
        subjects = [row[0] for row in cursor.fetchall()]
        return sorted(subjects)
    except Error as e:
        messagebox.showerror("Database Error", f"Failed to fetch subjects: {e}")
        return []
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def fetch_attendance(group_name, subject_name, selected_date=None, student_id=None):
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
            """
            params = [group_name, subject_name, selected_date]
            if student_id:
                query += " AND u.user_id = %s"
                params.append(student_id)
            query += " GROUP BY u.user_id, s.subject_name, s.session_date ORDER BY u.username"
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
            """
            params = [group_name, subject_name]
            if student_id:
                query += " AND u.user_id = %s"
                params.append(student_id)
            query += " GROUP BY u.user_id, s.subject_name ORDER BY u.username"

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

def fetch_student_overall_percentage(student_id, subject_name):
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
                u.user_id = %s
                AND s.subject_name = %s
            GROUP BY
                u.user_id, s.subject_name
        """
        params = [student_id, subject_name]
        cursor.execute(query, params)
        records = cursor.fetchall()
        return records
    except Error as e:
        messagebox.showerror("Database Error", f"Failed to fetch student overall percentage: {e}")
        return []
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def clear_window(window):
    for widget in window.winfo_children():
        widget.destroy()

def setup_styles():
    style = ttk.Style()
    style.theme_use('clam')
    style.configure('TButton', font=('Verdana', 10), padding=10)
    style.configure('TLabel', font=('Verdana', 14))
    style.configure('TEntry', font=('Verdana', 12))
    style.configure('TRadiobutton', font=('Verdana', 12))
    style.configure('TFrame', background='#f0f0f0')
    style.configure('TLabelframe', font=('Verdana', 14, 'bold'), background='#f0f0f0')
    style.configure('TLabelframe.Label', font=('Verdana', 14, 'bold'), background='#f0f0f0')
    
    style.configure('Primary.TButton', background='#4CAF50', foreground='white')
    style.map('Primary.TButton', background=[('active', '#45a049')])
    style.configure('Danger.TButton', background='#f44336', foreground='white')
    style.map('Danger.TButton', background=[('active', '#da190b')])
    style.configure('Warning.TButton', background='#ff9800', foreground='black')
    style.map('Warning.TButton', background=[('active', '#e68a00')])
    style.configure('Success.TButton', background='#2196F3', foreground='white')
    style.map('Success.TButton', background=[('active', '#1976D2')])

def show_login_screen():
    clear_window(root)
    root.title("Login / Signup")
    root.state('zoomed')
    root.configure(bg='#f0f0f0')

    main_frame = ttk.Frame(root)
    main_frame.place(relx=0.5, rely=0.5, anchor='center')

    ttk.Label(main_frame, text="Welcome to CamAttend", font=('Verdana', 24, 'bold')).pack(pady=20)

    ttk.Label(main_frame, text="ID").pack(pady=10)
    global user_id_entry
    user_id_entry = ttk.Entry(main_frame, width=30)
    user_id_entry.pack(pady=10)

    ttk.Label(main_frame, text="Group").pack(pady=10)
    global group_entry
    group_entry = ttk.Entry(main_frame, width=30)
    group_entry.pack(pady=10)

    ttk.Label(main_frame, text="Username").pack(pady=10)
    global username_entry
    username_entry = ttk.Entry(main_frame, width=30)
    username_entry.pack(pady=10)

    ttk.Label(main_frame, text="Password").pack(pady=10)
    global password_entry
    password_entry = ttk.Entry(main_frame, width=30, show="*")
    password_entry.pack(pady=10)

    global role_var
    role_var = tk.StringVar(value="Student")
    ttk.Radiobutton(main_frame, text="Student", variable=role_var, value="Student").pack(pady=5)
    ttk.Radiobutton(main_frame, text="Teacher", variable=role_var, value="Teacher").pack(pady=5)

    button_frame = ttk.Frame(main_frame)
    button_frame.pack(pady=20)
    ttk.Button(button_frame, text="Login", command=login, style='Primary.TButton').pack(side="left", padx=10)
    ttk.Button(button_frame, text="Signup", command=signup, style='Primary.TButton').pack(side="left", padx=10)

def open_admin_portal():
    clear_window(root)
    root.title("Admin Portal")
    root.state('zoomed')
    root.configure(bg='#f0f0f0')

    ttk.Button(root, text="Logout", command=show_login_screen, style='Danger.TButton').pack(anchor="ne", padx=20, pady=20)

    group_frame = ttk.LabelFrame(root, text="Group Management", padding=20)
    group_frame.pack(fill="both", expand=True, padx=20, pady=10)

    def clear_all_users():
        confirm = messagebox.askyesno("Confirm", "Are you sure you want to delete ALL users?")
        if confirm:
            try:
                conn = mysql.connector.connect(**MYSQL_CONFIG)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM users")
                conn.commit()
                update_user_lists()
                messagebox.showinfo("Success", "All users have been deleted.")
            except Error as e:
                messagebox.showerror("Database Error", f"Failed to clear users: {e}")
            finally:
                if conn.is_connected():
                    cursor.close()
                    conn.close()

    def view_group_users():
        group = group_view_entry.get()
        if not group:
            messagebox.showerror("Error", "Please enter a group name")
            return
        if not re.match("^[A-Za-z0-9]+$", group):
            messagebox.showerror("Error", "Group name must contain only letters (A-Z, a-z) or numbers (0-9)!")
            return

        try:
            conn = mysql.connector.connect(**MYSQL_CONFIG)
            cursor = conn.cursor()
            cursor.execute("SELECT username, role, approved FROM users WHERE group_name=%s", (group,))
            users = cursor.fetchall()
            
            view_window = tk.Toplevel(root)
            view_window.title(f"Users in Group: {group}")
            view_window.state('zoomed')
            view_window.configure(bg='#f0f0f0')

            def remove_user(username):
                confirm = messagebox.askyesno("Confirm Remove", f"Are you sure you want to remove {username}?")
                if confirm:
                    try:
                        conn = mysql.connector.connect(**MYSQL_CONFIG)
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM users WHERE username=%s", (username,))
                        conn.commit()
                        view_window.destroy()
                        messagebox.showinfo("Removed", f"{username} has been removed.")
                        view_group_users()
                    except Error as e:
                        messagebox.showerror("Database Error", f"Failed to remove user: {e}")
                    finally:
                        if conn.is_connected():
                            cursor.close()
                            conn.close()

            canvas = tk.Canvas(view_window, bg='#f0f0f0')
            scrollbar = ttk.Scrollbar(view_window, command=canvas.yview)
            scrollable_frame = ttk.Frame(canvas)

            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )

            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)

            header = ttk.Frame(scrollable_frame)
            header.pack(fill="x", pady=10)
            ttk.Label(header, text="Username", width=20, anchor="w", font=('Verdana', 12, 'bold')).pack(side="left")
            ttk.Label(header, text="Role", width=10, anchor="w", font=('Verdana', 12, 'bold')).pack(side="left")
            ttk.Label(header, text="Approved", width=10, anchor="w", font=('Verdana', 12, 'bold')).pack(side="left")
            ttk.Label(header, text="Action", width=10, anchor="w", font=('Verdana', 12, 'bold')).pack(side="left")

            for user in users:
                username, role, approved = user
                approved_text = "Yes" if approved else "No"
                row = ttk.Frame(scrollable_frame)
                row.pack(fill="x", pady=5)
                ttk.Label(row, text=username, width=20, anchor="w").pack(side="left")
                ttk.Label(row, text=role, width=10, anchor="w").pack(side="left")
                ttk.Label(row, text=approved_text, width=10, anchor="w").pack(side="left")
                ttk.Button(row, text="Remove", command=lambda u=username: remove_user(u), style='Danger.TButton').pack(side="left", padx=5)

            canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
            scrollbar.pack(side="right", fill="y")
        except Error as e:
            messagebox.showerror("Database Error", f"Failed to view group: {e}")
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

    ttk.Label(group_frame, text="View Group Members:").grid(row=0, column=0, padx=10, pady=10)
    group_view_entry = ttk.Entry(group_frame, width=30)
    group_view_entry.grid(row=0, column=1, padx=10, pady=10)
    ttk.Button(group_frame, text="View Group", command=view_group_users, style='Primary.TButton').grid(row=0, column=2, padx=10, pady=10)
    ttk.Button(root, text="⚠️ Clear All Users", command=clear_all_users, style='Danger.TButton').pack(pady=20)

    approval_container = ttk.Frame(root)
    approval_container.pack(fill="both", expand=True, padx=20, pady=10)

    student_frame_container = tk.Frame(approval_container)
    student_frame_container.grid(row=0, column=0, sticky="nsew")
    student_canvas = tk.Canvas(student_frame_container, bg='#f0f0f0')
    student_scrollbar = ttk.Scrollbar(student_frame_container, command=student_canvas.yview)
    student_scrollable_frame = ttk.Frame(student_canvas)

    student_scrollable_frame.bind(
        "<Configure>",
        lambda e: student_canvas.configure(scrollregion=student_canvas.bbox("all"))
    )

    student_canvas.create_window((0, 0), window=student_scrollable_frame, anchor="nw")
    student_canvas.configure(yscrollcommand=student_scrollbar.set)

    student_label_frame = ttk.LabelFrame(student_scrollable_frame, text="Student Requests", padding=20)
    student_label_frame.pack(fill="both", expand=True, padx=10, pady=10)

    student_canvas.pack(side="left", fill="both", expand=True)
    student_scrollbar.pack(side="right", fill="y")

    teacher_frame_container = tk.Frame(approval_container)
    teacher_frame_container.grid(row=0, column=1, sticky="nsew")
    teacher_canvas = tk.Canvas(teacher_frame_container, bg='#f0f0f0')
    teacher_scrollbar = ttk.Scrollbar(teacher_frame_container, command=teacher_canvas.yview)
    teacher_scrollable_frame = ttk.Frame(teacher_canvas)

    teacher_scrollable_frame.bind(
        "<Configure>",
        lambda e: teacher_canvas.configure(scrollregion=teacher_canvas.bbox("all"))
    )

    teacher_canvas.create_window((0, 0), window=teacher_scrollable_frame, anchor="nw")
    teacher_canvas.configure(yscrollcommand=teacher_scrollbar.set)

    teacher_label_frame = ttk.LabelFrame(teacher_scrollable_frame, text="Teacher Requests", padding=20)
    teacher_label_frame.pack(fill="both", expand=True, padx=10, pady=10)

    teacher_canvas.pack(side="left", fill="both", expand=True)
    teacher_scrollbar.pack(side="right", fill="y")

    approval_container.grid_columnconfigure(0, weight=1)
    approval_container.grid_columnconfigure(1, weight=1)
    approval_container.grid_rowconfigure(0, weight=1)

    def update_user_lists():
        for widget in student_label_frame.winfo_children():
            widget.destroy()
        for widget in teacher_label_frame.winfo_children():
            widget.destroy()

        try:
            conn = mysql.connector.connect(**MYSQL_CONFIG)
            cursor = conn.cursor()
            cursor.execute("SELECT username, role, group_name FROM users WHERE approved=0")
            users = cursor.fetchall()

            student_users = [u for u in users if u[1] == "Student"]
            teacher_users = [u for u in users if u[1] == "Teacher"]

            if not student_users:
                ttk.Label(student_label_frame, text="No pending student requests", font=('Verdana', 12)).pack(pady=10)
            else:
                for username, _, group in student_users:
                    row = ttk.Frame(student_label_frame)
                    row.pack(fill="x", pady=5)
                    ttk.Label(row, text=f"{username} (Group: {group})", width=30, anchor="w").pack(side="left")
                    ttk.Button(row, text="Approve", command=lambda u=username: approve_user(u), style='Primary.TButton').pack(side="left", padx=2)
                    ttk.Button(row, text="Decline", command=lambda u=username: decline_user(u), style='Danger.TButton').pack(side="left", padx=2)
                button_frame = ttk.Frame(student_label_frame)
                button_frame.pack(pady=10)
                ttk.Button(button_frame, text="Approve All Students", command=lambda: approve_all("Student"), style='Primary.TButton').pack(side="left", padx=5)
                ttk.Button(button_frame, text="Decline All Students", command=lambda: decline_all("Student"), style='Danger.TButton').pack(side="left", padx=5)

            if not teacher_users:
                ttk.Label(teacher_label_frame, text="No pending teacher requests", font=('Verdana', 12)).pack(pady=10)
            else:
                for username, _, group in teacher_users:
                    row = ttk.Frame(teacher_label_frame)
                    row.pack(fill="x", pady=5)
                    ttk.Label(row, text=f"{username} (Group: {group})", width=30, anchor="w").pack(side="left")
                    ttk.Button(row, text="Approve", command=lambda u=username: approve_user(u), style='Primary.TButton').pack(side="left", padx=5)
                    ttk.Button(row, text="Decline", command=lambda u=username: decline_user(u), style='Danger.TButton').pack(side="left", padx=5)
                button_frame = ttk.Frame(teacher_label_frame)
                button_frame.pack(pady=10)
                ttk.Button(button_frame, text="Approve All Teachers", command=lambda: approve_all("Teacher"), style='Primary.TButton').pack(side="left", padx=5)
                ttk.Button(button_frame, text="Decline All Teachers", command=lambda: decline_all("Teacher"), style='Danger.TButton').pack(side="left", padx=5)

        except Error as e:
            messagebox.showerror("Database Error", f"Failed to update user lists: {e}")
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

    def approve_user(username):
        try:
            conn = mysql.connector.connect(**MYSQL_CONFIG)
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET approved=1 WHERE username=%s", (username,))
            conn.commit()
            messagebox.showinfo("Success", f"User {username} approved.")
            update_user_lists()
        except Error as e:
            messagebox.showerror("Database Error", f"Failed to approve user: {e}")
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

    def decline_user(username):
        try:
            conn = mysql.connector.connect(**MYSQL_CONFIG)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE username=%s", (username,))
            conn.commit()
            messagebox.showinfo("Success", f"User {username} declined and removed.")
            update_user_lists()
        except Error as e:
            messagebox.showerror("Database Error", f"Failed to decline user: {e}")
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

    def approve_all(role):
        try:
            conn = mysql.connector.connect(**MYSQL_CONFIG)
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET approved=1 WHERE approved=0 AND role=%s", (role,))
            conn.commit()
            messagebox.showinfo("Success", f"All {role}s approved.")
            update_user_lists()
        except Error as e:
            messagebox.showerror("Database Error", f"Failed to approve all: {e}")
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

    def decline_all(role):
        confirm = messagebox.askyesno("Confirm", f"Are you sure you want to decline ALL {role} requests?")
        if confirm:
            try:
                conn = mysql.connector.connect(**MYSQL_CONFIG)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM users WHERE approved=0 AND role=%s", (role,))
                conn.commit()
                messagebox.showinfo("Success", f"All {role}s declined and removed.")
                update_user_lists()
            except Error as e:
                messagebox.showerror("Database Error", f"Failed to decline all: {e}")
            finally:
                if conn.is_connected():
                    cursor.close()
                    conn.close()

    update_user_lists()

def login():
    username = username_entry.get().strip()
    password = password_entry.get().strip()
    role = role_var.get()
    group = group_entry.get().strip()
    user_id = user_id_entry.get().strip()

    if not username or not password or not group or not user_id:
        messagebox.showerror("Error", "All fields (including ID) are required!")
        return

    if not re.match("^[A-Za-z0-9]+$", group):
        messagebox.showerror("Error", "Group name must contain only letters (A-Z, a-z) or numbers (0-9)!")
        return

    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        messagebox.showinfo("Admin Login Successful", "Welcome, Admin!")
        open_admin_portal()
        return

    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s AND role=%s AND group_name=%s AND approved=1 AND user_id=%s",
                       (username, password, role, group, user_id))
        result = cursor.fetchone()
        
        if result:
            messagebox.showinfo("Login Successful", f"Welcome, {username}!")
            if role == "Teacher":
                open_teacher_dashboard(username)
            else:
                open_student_dashboard(username)
        else:
            messagebox.showerror("Error", "Invalid credentials, group mismatch, ID mismatch, or approval pending.")
    except Error as e:
        messagebox.showerror("Database Error", f"Login failed: {e}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def open_teacher_dashboard(username):
    clear_window(root)
    root.title("Teacher Dashboard")
    root.state('zoomed')
    root.configure(bg='#f0f0f0')

    ttk.Button(root, text="Logout", command=show_login_screen, style='Danger.TButton').pack(anchor="ne", padx=20, pady=20)

    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT group_name, user_id FROM users WHERE username=%s", (username,))
        cursor_result = cursor.fetchone()
        if cursor_result:
            teacher_group = cursor_result[0]
            teacher_id = cursor_result[1]
        else:
            messagebox.showerror("Error", "Teacher not found.")
            return
    except Error as e:
        messagebox.showerror("Database Error", f"Failed to fetch group: {e}")
        return
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

    main_frame = ttk.Frame(root)
    main_frame.place(relx=0.5, rely=0.5, anchor='center')

    ttk.Label(main_frame, text=f"Welcome, {username}", font=("Verdana", 24, 'bold')).pack(pady=20)
    ttk.Label(main_frame, text=f"Group Admin for: {teacher_group}", font=("Verdana", 18)).pack(pady=10)

    def take_group_attendance():
        manage_window = tk.Toplevel(root)
        manage_window.title("Attendance Manager")
        manage_window.state('zoomed')
        manage_window.configure(bg='#f0f0f0')
        heading = tk.Label(manage_window, text=f"Manage Attendance: G {teacher_group}", font=("Arial", 24, "bold"), bg='#f0f0f0')
        heading.pack(pady=40)
        
        subject_label_fill_attendance = tk.Label(manage_window, text="Enter Subject Name:", font=("Arial", 14), bg='#f0f0f0')
        subject_label_fill_attendance.pack(pady=5)
        subject_entry_fill_attendance = tk.Entry(manage_window, font=("Arial", 14), width=30)
        subject_entry_fill_attendance.pack(pady=10)

        notifica_label = ttk.Label(
            manage_window,
            text="",
            style='TLabel',
            width=40,
        )
        notifica_label.pack(pady=20)

        def fill_attendance():
            subject = subject_entry_fill_attendance.get().strip()
            if not subject:
                messagebox.showwarning("Input Required", "Please enter a subject name.")
                return
            try:
                conn = mysql.connector.connect(**MYSQL_CONFIG)
                cursor = conn.cursor()
                notifica_label.configure(text=f"Filling attendance for subject: {subject}")

                session_id = create_attendance_session(teacher_id, teacher_group, subject)

                if not session_id:
                    notifica_label.configure(text="Failed to create or fetch session ID.")
                    return

                def run_attendance_thread():
                    present, absent = automaticAttendance.run_attendance(
                        group_name=teacher_group,
                        trainimagelabel_path=trainimagelabel_path,
                        haarcasecade_path=haarcasecade_path,
                        notifica_label=notifica_label
                    )
                    root.after(0, lambda: post_attendance(present, absent, session_id, notifica_label))

                threading.Thread(target=run_attendance_thread, daemon=True).start()

            except Exception as e:
                notifica_label.configure(text=f"Failed to fill attendance: {e}")
                print(f"Error: Failed to fill attendance: {e}")
            finally:
                if conn.is_connected():
                    cursor.close()
                    conn.close()

        def post_attendance(present, absent, session_id, notifica_label):
            try:
                for student_id in present:
                    mark_attendance(session_id, student_id, status=1)

                for student_id in absent:
                    mark_attendance(session_id, student_id, status=0)

                notifica_label.configure(text="Attendance marked successfully.")
                messagebox.showinfo("Attendance", "Attendance marked successfully.")

            except Exception as e:
                notifica_label.configure(text=f"Failed to mark attendance: {e}")
                messagebox.showerror("Error", f"Failed to mark attendance: {e}")

        def view_group_attendance():
            show_attendance.subjectchoose(lambda msg: notifica_label.configure(text=msg), teacher_group)

        def create_attendance_session(teacher_id, group_name, subject_name):
            try:
                conn = mysql.connector.connect(**MYSQL_CONFIG, connect_timeout=10)
                cursor = conn.cursor()
                today = datetime.now().date()

                cursor.execute("""
                    SELECT MAX(session_count)
                    FROM attendance_session
                    WHERE teacher_id=%s AND subject_name=%s AND group_name=%s AND session_date=%s
                """, (teacher_id, subject_name, group_name, today))
                result = cursor.fetchone()
                current_count = result[0] if result[0] is not None else 0

                cursor.execute("""
                    INSERT INTO attendance_session 
                    (teacher_id, subject_name, group_name, session_date, session_count)
                    VALUES (%s, %s, %s, %s, %s)
                """, (teacher_id, subject_name, group_name, today, current_count + 1))
                
                session_id = cursor.lastrowid
                conn.commit()
                print(f"Created Session ID: {session_id}, Session Count: {current_count + 1}")
                return session_id

            except Error as e:
                print(f"Session Creation Error: {e}")
                notifica_label.configure(text=f"Failed to create session: {e}")
                return None
            finally:
                if conn.is_connected():
                    cursor.close()
                    conn.close()

        def mark_attendance(session_id, student_id, status):
            try:
                conn = mysql.connector.connect(**MYSQL_CONFIG, connect_timeout=10)
                cursor = conn.cursor()
                today = datetime.now().date()
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                cursor.execute("""
                    INSERT INTO attendance (session_id, student_id, status, date, timestamp)
                    VALUES (%s, %s, %s, %s, %s)
                """, (session_id, student_id, status, today, now))
                print(f"Inserted attendance for student {student_id}, status: {status}")

                conn.commit()
            except Error as e:
                print(f"Mark Attendance Error: {e}")
                raise Exception(f"Failed to mark attendance for {student_id}: {e}")
            finally:
                if conn.is_connected():
                    cursor.close()
                    conn.close()

        fill_attendance_btn = tk.Button(manage_window, text="Fill Attendance", font=("Arial", 16), width=20, height=2, bg="#4CAF50", fg="white", command=fill_attendance)
        fill_attendance_btn.pack(pady=20)
        view_attendance_btn = tk.Button(manage_window, text="View Attendance", font=("Arial", 16), width=20, height=2, bg="#2196F3", fg="white", command=view_group_attendance)
        view_attendance_btn.pack(pady=10)

    def manage_group_members():
        manage_window = tk.Toplevel(root)
        manage_window.title("Manage Group Members")
        manage_window.state('zoomed')
        manage_window.configure(bg='#f0f0f0')

        try:
            conn = mysql.connector.connect(**MYSQL_CONFIG)
            cursor = conn.cursor()
            cursor.execute("SELECT username, role, approved, user_id FROM users WHERE group_name=%s", (teacher_group,))
            members = cursor.fetchall()
            
            canvas = tk.Canvas(manage_window, bg='#f0f0f0')
            scrollbar = ttk.Scrollbar(manage_window, command=canvas.yview)
            scrollable_frame = ttk.Frame(canvas)

            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )

            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)

            student_frame = ttk.Frame(scrollable_frame)
            teacher_frame = ttk.Frame(scrollable_frame)

            student_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nw")
            teacher_frame.grid(row=0, column=1, padx=10, pady=10, sticky="ne")

            ttk.Label(student_frame, text="Roll No", width=20, anchor="w", font=("Verdana", 12, "bold")).grid(row=0, column=0, padx=5, pady=5)
            ttk.Label(student_frame, text="Username", width=20, anchor="w", font=("Verdana", 12, "bold")).grid(row=0, column=1, padx=5, pady=5)
            ttk.Label(student_frame, text="Approved", width=10, anchor="w", font=("Verdana", 12, 'bold')).grid(row=0, column=2, padx=5, pady=5)
            ttk.Label(student_frame, text="Action", width=10, anchor="w", font=("Verdana", 12, 'bold')).grid(row=0, column=3, padx=5, pady=5)
            ttk.Label(student_frame, text="Train", width=10, anchor="w", font=("Verdana", 12, 'bold')).grid(row=0, column=4, padx=5, pady=5)

            ttk.Label(teacher_frame, text="Username", width=20, anchor="w", font=("Verdana", 12, "bold")).grid(row=0, column=0, padx=5, pady=5)
            ttk.Label(teacher_frame, text="Role", width=10, anchor="w", font=("Verdana", 12, 'bold')).grid(row=0, column=1, padx=5, pady=5)
           
            student_row = 1
            teacher_row = 1

            for user, role, approved, user_id in members:
                approved_text = "Yes" if approved else "No"
                if role.lower() == "student":
                    ttk.Label(student_frame, text=user_id, width=20, anchor="w").grid(row=student_row, column=0, padx=5, pady=5)
                    ttk.Label(student_frame, text=user, width=20, anchor="w").grid(row=student_row, column=1, padx=5, pady=5)
                    ttk.Label(student_frame, text=approved_text, width=10, anchor="w").grid(row=student_row, column=2, padx=5, pady=5)
                    if user != username:
                        ttk.Button(student_frame, text="Remove", command=lambda u=user: remove_user(u, manage_window), style='Danger.TButton').grid(row=student_row, column=3, padx=5, pady=5)
                        ttk.Button(student_frame, text="Train Image", command=lambda rn=user_id: take_and_train_image(rn), style='Success.TButton').grid(row=student_row, column=4, padx=5, pady=5)
                    student_row += 1
                else:
                    ttk.Label(teacher_frame, text=user, width=20, anchor="w").grid(row=teacher_row, column=0, padx=5, pady=5)
                    ttk.Label(teacher_frame, text=role, width=10, anchor="w").grid(row=teacher_row, column=1, padx=5, pady=5)
                    teacher_row += 1

            canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
            scrollbar.pack(side="right", fill="y")
        except Error as e:
            messagebox.showerror("Database Error", f"Failed to manage group: {e}")
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

    def take_and_train_image(roll_no):
        image_taken = takeImage.TakeImage(
            roll_no,
            teacher_group,
            haarcasecade_path,
            trainimage_path,
            lambda msg: messagebox.showinfo("Info", msg)
        )
        if image_taken:
            trainImage.TrainImage(
                haarcasecade_path,
                trainimage_path,
                trainimagelabel_path,
                lambda msg: messagebox.showinfo("Info", msg)
            )
        else:
            messagebox.showerror("Error", "Error in capturing image")

    def remove_user(username_to_remove, window):
        confirm = messagebox.askyesno("Confirm", f"Remove {username_to_remove} from group?")
        if confirm:
            try:
                conn = mysql.connector.connect(**MYSQL_CONFIG)
                cursor = conn.cursor()
                
                cursor.execute("SELECT user_id FROM users WHERE username=%s", (username_to_remove,))
                result = cursor.fetchone()
                user_id = result[0]
                user_folder_path = os.path.join(trainimage_path, user_id)

                cursor.execute("DELETE FROM attendance WHERE student_id=%s", (user_id,))
                cursor.execute("DELETE FROM users WHERE username=%s", (username_to_remove,))
                conn.commit()
                
                if os.path.exists(user_folder_path):
                    shutil.rmtree(user_folder_path)
                
                messagebox.showinfo("Removed", f"{username_to_remove} has been removed.")
                window.destroy()
                manage_group_members()
            except Error as e:
                messagebox.showerror("Database Error", f"Failed to remove user: {e}")
            finally:
                if conn.is_connected():
                    cursor.close()
                    conn.close()

    def approve_group_students():
        approve_window = tk.Toplevel(root)
        approve_window.title("Approve Students in Your Group")
        approve_window.state('zoomed')
        approve_window.configure(bg='#f0f0f0')

        try:
            conn = mysql.connector.connect(**MYSQL_CONFIG)
            cursor = conn.cursor()
            cursor.execute("SELECT username FROM users WHERE group_name=%s AND role='Student' AND approved=0", (teacher_group,))
            pending_students = cursor.fetchall()
            
            for student in pending_students:
                student_name = student[0]
                row = ttk.Frame(approve_window)
                row.pack(fill="x", pady=5, padx=10)
                ttk.Label(row, text=student_name, width=10, anchor="w").pack(side="left")
                ttk.Button(row, text="Approve", width=5, command=lambda s=student_name: approve_student(s), style='Primary.TButton').pack(side="left", padx=1)
                ttk.Button(row, text="Decline", width=5, command=lambda s=student_name: decline_student(s), style='Danger.TButton').pack(side="left", padx=1)

        except Error as e:
            messagebox.showerror("Database Error", f"Failed to fetch students: {e}")
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

    def approve_student(username):
        try:
            conn = mysql.connector.connect(**MYSQL_CONFIG)
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET approved=1 WHERE username=%s", (username,))
            conn.commit()
            messagebox.showinfo("Approved", f"{username} approved!")
        except Error as e:
            messagebox.showerror("Database Error", f"Failed to approve student: {e}")
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

    def decline_student(username):
        try:
            conn = mysql.connector.connect(**MYSQL_CONFIG)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE username=%s", (username,))
            conn.commit()
            messagebox.showinfo("Declined", f"{username} removed!")
        except Error as e:
            messagebox.showerror("Database Error", f"Failed to decline student: {e}")
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

    ttk.Button(main_frame, text="Approve Student Requests", command=approve_group_students, style='Warning.TButton').pack(pady=20, ipadx=20, ipady=10)
    ttk.Button(main_frame, text="Take Group Attendance", command=take_group_attendance, style='Primary.TButton').pack(pady=20, ipadx=20, ipady=10)
    ttk.Button(main_frame, text="Manage Group Members", command=manage_group_members, style='Primary.TButton').pack(pady=20, ipadx=20, ipady=10)

def open_student_dashboard(username):
    clear_window(root)
    root.title("Student Dashboard")
    root.state('zoomed')
    root.configure(bg='#f0f0f0')
    
    ttk.Button(root, text="Logout", command=show_login_screen, style='Danger.TButton').pack(anchor="ne", padx=20, pady=20)
    
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT group_name, user_id FROM users WHERE username=%s", (username,))
        result = cursor.fetchone()
        if not result:
            messagebox.showerror("Error", "User not found.")
            return
        student_group, student_id = result
        
        main_frame = ttk.Frame(root)
        main_frame.place(relx=0.5, rely=0.5, anchor='center')
        
        ttk.Label(main_frame, text=f"Welcome, {username}", font=("Verdana", 24, 'bold')).pack(pady=20)
        ttk.Label(main_frame, text=f"Group: {student_group}", font=("Verdana", 18)).pack(pady=10)

        notification_label = ttk.Label(main_frame, text="", font=("Verdana", 12), foreground="red", background='#f0f0f0')
        notification_label.pack(pady=10)

        subjects = fetch_subjects(student_id=student_id)
        if not subjects:
            notification_label.config(text="No subjects found for you.")
            return

        ttk.Label(main_frame, text="Select Subject:", font=("Verdana", 14)).pack(pady=10)
        subject_var = tk.StringVar()
        subject_dropdown = ttk.Combobox(main_frame, textvariable=subject_var, values=subjects, state='readonly', width=30, font=('Verdana', 12))
        subject_dropdown.pack(pady=10)
        subject_dropdown.current(0)

        ttk.Label(main_frame, text="Select Date:", font=("Verdana", 14)).pack(pady=10)
        date_entry = DateEntry(main_frame, width=30, font=('Verdana', 12), date_pattern='yyyy-mm-dd', maxdate=datetime.now())
        date_entry.pack(pady=10)

        def show_student_attendance(selected_date=None):
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

            records = fetch_attendance(student_group, subject, date_str, student_id)
            if not records:
                if date_str:
                    notification_label.config(text=f"No data found for {subject} on {date_str}.")
                else:
                    notification_label.config(text=f"No data found for {subject}.")
                return

            table_window = tk.Toplevel(root)
            table_window.title(f"Attendance for {subject}" + (f" on {date_str}" if date_str else ""))
            table_window.state('zoomed')
            table_window.configure(bg='#f0f0f0')

            headers = ["Username", "Subject", "Date", "Total Sessions", "Present", "Absent", "Attendance %"]
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
                    record[5], 
                    f"{float(record[6]):.2f}%"  
                ]
                for c, field in enumerate(display_row):
                    bg_color = "#f0f0f0"
                    if c == 6:
                        percentage = float(record[6])
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
            notification_label.config(text=f"Showing attendance for {subject}" + (f" on {date_str}" if date_str else " for all dates."))

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=20)
        ttk.Button(button_frame, text="Show Attendance", command=lambda: show_student_attendance(), style='Primary.TButton').pack(side="left", padx=10)
        
        def show_student_percentage():
            subject = subject_var.get()
            if not subject:
                notification_label.config(text="Please select a subject.")
                return
            records = fetch_student_overall_percentage(student_id, subject)
            if not records:
                notification_label.config(text=f"No data found for {subject}.")
                return
            table_window = tk.Toplevel(root)
            table_window.title(f"Overall Percentage for {subject}")
            table_window.state('zoomed')
            table_window.configure(bg='#f0f0f0')
            headers = ["Username", "Subject", "Total Sessions", "Present", "Absent", "Attendance %"]
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
        ttk.Button(button_frame, text="Show Percentage", command=show_student_percentage, style='Primary.TButton').pack(side="left", padx=10)
    except Error as e:
        messagebox.showerror("Database Error", f"Failed to load dashboard: {e}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

setup_db()
root = tk.Tk()
setup_styles()
show_login_screen()
root.mainloop()