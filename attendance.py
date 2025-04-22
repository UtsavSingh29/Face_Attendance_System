import tkinter as tk
from tkinter import messagebox, ttk
import mysql.connector
from mysql.connector import Error
import os
import uuid
import re

ADMIN_USERNAME = "adminname"
ADMIN_PASSWORD = "adminpass"

MYSQL_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "pass of ur root",
    "database": "database name"
}

def setup_db():
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                            id INTEGER PRIMARY KEY AUTO_INCREMENT,
                            user_id VARCHAR(50) UNIQUE NOT NULL,
                            username VARCHAR(255) UNIQUE NOT NULL,
                            password VARCHAR(255) NOT NULL,
                            role VARCHAR(50) NOT NULL,
                            group_name VARCHAR(255) NOT NULL,
                            approved INTEGER DEFAULT 0
                        )''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS attendance (
                            id INTEGER PRIMARY KEY AUTO_INCREMENT,
                            user_id VARCHAR(50) NOT NULL,
                            group_name VARCHAR(255) NOT NULL,
                            date VARCHAR(50) NOT NULL,
                            status VARCHAR(50) NOT NULL
                        )''')
        
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

def fetch_attendance(username=None, group=None):
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        
        if username:
            cursor.execute("SELECT date, status FROM attendance WHERE username=%s", (username,))
        elif group:
            cursor.execute("SELECT username, date, status FROM attendance WHERE group_name=%s", (group,))
        else:
            cursor.execute("SELECT * FROM attendance")
        
        records = cursor.fetchall()
        return records
    except Error as e:
        messagebox.showerror("Database Error", f"Failed to fetch attendance: {e}")
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

            print(f"Fetched {len(users)} pending users: {users}")

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
            print(f"Approved user: {username}")
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
            print(f"Attempting to decline user: {username}")
            cursor.execute("DELETE FROM users WHERE username=%s", (username,))
            conn.commit()
            cursor.execute("SELECT username, role, group_name FROM users WHERE approved=0")
            remaining = cursor.fetchall()
            print(f"Remaining pending users after decline: {remaining}")
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
            print(f"Approved all {role}s")
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
                print(f"Declined all {role}s")
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
        cursor.execute("SELECT group_name FROM users WHERE username=%s", (username,))
        teacher_group = cursor.fetchone()[0]
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
        os.system(f"python face_recognition_ui.py --group {teacher_group}")

    def manage_group_members():
        manage_window = tk.Toplevel(root)
        manage_window.title("Manage Group Members")
        manage_window.state('zoomed')
        manage_window.configure(bg='#f0f0f0')

        try:
            conn = mysql.connector.connect(**MYSQL_CONFIG)
            cursor = conn.cursor()
            cursor.execute("SELECT username, role, approved FROM users WHERE group_name=%s", (teacher_group,))
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

            ttk.Label(scrollable_frame, text="Username", width=20, anchor="w", font=("Verdana", 12, "bold")).grid(row=0, column=0, padx=5, pady=5)
            ttk.Label(scrollable_frame, text="Role", width=10, anchor="w", font=("Verdana", 12, 'bold')).grid(row=0, column=1, padx=5, pady=5)
            ttk.Label(scrollable_frame, text="Approved", width=10, anchor="w", font=('Verdana', 12, 'bold')).grid(row=0, column=2, padx=5, pady=5)
            ttk.Label(scrollable_frame, text="Action", width=10, anchor="w", font=('Verdana', 12, 'bold')).grid(row=0, column=3, padx=5, pady=5)

            for i, (user, role, approved) in enumerate(members, start=1):
                approved_text = "Yes" if approved else "No"
                ttk.Label(scrollable_frame, text=user, width=20, anchor="w").grid(row=i, column=0, padx=5, pady=5)
                ttk.Label(scrollable_frame, text=role, width=10, anchor="w").grid(row=i, column=1, padx=5, pady=5)
                ttk.Label(scrollable_frame, text=approved_text, width=10, anchor="w").grid(row=i, column=2, padx=5, pady=5)
                if user != username:
                    ttk.Button(scrollable_frame, text="Remove", command=lambda u=user: remove_user(u, manage_window), style='Danger.TButton').grid(row=i, column=3, padx=5, pady=5)

            canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
            scrollbar.pack(side="right", fill="y")
        except Error as e:
            messagebox.showerror("Database Error", f"Failed to manage group: {e}")
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

    def remove_user(username_to_remove, window):
        confirm = messagebox.askyesno("Confirm", f"Remove {username_to_remove} from group?")
        if confirm:
            try:
                conn = mysql.connector.connect(**MYSQL_CONFIG)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM users WHERE username=%s", (username_to_remove,))
                conn.commit()
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
        cursor.execute("SELECT group_name FROM users WHERE username=%s", (username,))
        student_group = cursor.fetchone()[0]
        
        main_frame = ttk.Frame(root)
        main_frame.place(relx=0.5, rely=0.5, anchor='center')
        
        ttk.Label(main_frame, text=f"Welcome, {username}", font=("Verdana", 24, 'bold')).pack(pady=20)
        ttk.Label(main_frame, text=f"Group: {student_group}", font=("Verdana", 18)).pack(pady=10)
        
        attendance_records = fetch_attendance(username)
        attendance_text = "Date\tStatus\n" + "\n".join([f"{date}\t{status}" for date, status in attendance_records])
        attendance_label = ttk.Label(main_frame, text=attendance_text, font=("Verdana", 14), justify='left')
        attendance_label.pack(pady=20)
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