import tkinter as tk
from tkinter import messagebox, ttk
import sqlite3
import os
import uuid

# Predefined Admin Credentials
ADMIN_USERNAME = "a"
ADMIN_PASSWORD = "1"

def setup_db():
    # Connect to database (this will create it if it doesn't exist)
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    
    # Create new tables only if they don't exist
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE,
                        password TEXT,
                        role TEXT,
                        group_name TEXT,
                        approved INTEGER DEFAULT 0)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS attendance (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT,
                        group_name TEXT,
                        date TEXT,
                        status TEXT)''')
    
    conn.commit()
    conn.close()

def signup():
    username = username_entry.get().strip()
    password = password_entry.get().strip()
    role = role_var.get()
    group = group_entry.get().strip()

    # Check if any field is empty
    if not username or not password or not group:
        messagebox.showerror("Error", "All fields are required!")
        return

    try:
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password, role, group_name, approved) VALUES (?, ?, ?, ?, 0)",
                       (username, password, role, group))
        conn.commit()
        conn.close()
        messagebox.showinfo("Signup Request Sent", "Wait for Admin Approval!")
    except sqlite3.IntegrityError:
        messagebox.showerror("Error", "Username already exists!")

def check_login(username, password, role):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username=? AND password=? AND role=? AND approved=1",
                  (username, password, role))
    result = cursor.fetchone()
    conn.close()
    return result

# Function to fetch attendance with group filter
def fetch_attendance(username=None, group=None):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    
    if username:
        cursor.execute("SELECT date, status FROM attendance WHERE username=?", (username,))
    elif group:
        cursor.execute("SELECT username, date, status FROM attendance WHERE group_name=?", (group,))
    else:
        cursor.execute("SELECT * FROM attendance")
        
    records = cursor.fetchall()
    conn.close()
    return records

def clear_window(window):
    for widget in window.winfo_children():
        widget.destroy()

def setup_styles():
    style = ttk.Style()
    style.theme_use('clam')  # Modern theme
    style.configure('TButton', font=('Verdana', 12), padding=10)
    style.configure('TLabel', font=('Verdana', 14))
    style.configure('TEntry', font=('Verdana', 12))
    style.configure('TRadiobutton', font=('Verdana', 12))
    style.configure('TFrame', background='#f0f0f0')
    style.configure('TLabelframe', font=('Verdana', 14, 'bold'), background='#f0f0f0')
    style.configure('TLabelframe.Label', font=('Verdana', 14, 'bold'), background='#f0f0f0')
    
    # Custom button styles
    style.configure('Primary.TButton', background='#4CAF50', foreground='white')
    style.map('Primary.TButton', background=[('active', '#45a049')])
    style.configure('Danger.TButton', background='#f44336', foreground='white')
    style.map('Danger.TButton', background=[('active', '#da190b')])
    style.configure('Warning.TButton', background='#ff9800', foreground='black')
    style.map('Warning.TButton', background=[('active', '#e68a00')])

def show_login_screen():
    clear_window(root)
    root.title("Login / Signup")
    root.state('zoomed')  # Maximize window to full screen
    root.configure(bg='#f0f0f0')  # Light background

    # Center content frame
    main_frame = ttk.Frame(root)
    main_frame.place(relx=0.5, rely=0.5, anchor='center')

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

    ttk.Button(main_frame, text="Login", command=login, style='Primary.TButton').pack(pady=20)
    ttk.Button(main_frame, text="Signup", command=signup, style='Primary.TButton').pack(pady=10)

# Enhanced Admin Portal with Group Management
def open_admin_portal():
    clear_window(root)
    root.title("Admin Portal")
    root.state('zoomed')  # Maximize window to full screen
    root.configure(bg='#f0f0f0')

    # Logout Button
    ttk.Button(root, text="Logout", command=show_login_screen, style='Danger.TButton').pack(anchor="ne", padx=20, pady=20)

    # Group Management Section
    group_frame = ttk.LabelFrame(root, text="Group Management", padding=20)
    group_frame.pack(fill="both", expand=True, padx=20, pady=10)

    def clear_all_users():
        confirm = messagebox.askyesno("Confirm", "Are you sure you want to delete ALL users?")
        if confirm:
            conn = sqlite3.connect("users.db")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users")  # Delete all user records
            conn.commit()
            conn.close()
            update_user_lists()
            messagebox.showinfo("Success", "All users have been deleted.")

    def view_group_users():
        group = group_view_entry.get()
        if not group:
            messagebox.showerror("Error", "Please enter a group name")
            return

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("SELECT username, role, approved FROM users WHERE group_name=?", (group,))
        users = cursor.fetchall()
        conn.close()

        view_window = tk.Toplevel(root)
        view_window.title(f"Users in Group: {group}")
        view_window.state('zoomed')  # Maximize child window
        view_window.configure(bg='#f0f0f0')

        def remove_user(username):
            confirm = messagebox.askyesno("Confirm Remove", f"Are you sure you want to remove {username}?")
            if confirm:
                conn = sqlite3.connect("users.db")
                cursor = conn.cursor()
                cursor.execute("DELETE FROM users WHERE username=?", (username,))
                conn.commit()
                conn.close()
                view_window.destroy()
                messagebox.showinfo("Removed", f"{username} has been removed.")
                view_group_users()

        canvas = tk.Canvas(view_window, bg='#f0f0f0')
        scrollbar = ttk.Scrollbar(view_window, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
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

    ttk.Label(group_frame, text="View Group Members:").grid(row=0, column=0, padx=10, pady=10)
    group_view_entry = ttk.Entry(group_frame, width=30)
    group_view_entry.grid(row=0, column=1, padx=10, pady=10)
    ttk.Button(group_frame, text="View Group", command=view_group_users, style='Primary.TButton').grid(row=0, column=2, padx=10, pady=10)
    ttk.Button(root, text="⚠️ Clear All Users", command=clear_all_users, style='Danger.TButton').pack(pady=20)

    # User Approval Section
    def update_user_lists():
        for widget in student_frame.winfo_children():
            widget.destroy()
        for widget in teacher_frame.winfo_children():
            widget.destroy()

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("SELECT username, role, group_name FROM users WHERE approved=0")
        users = cursor.fetchall()
        conn.close()

        student_users = [u for u in users if u[1] == "Student"]
        teacher_users = [u for u in users if u[1] == "Teacher"]

        for username, _, group in student_users:
            row = ttk.Frame(student_frame)
            row.pack(fill="x", pady=5)
            ttk.Label(row, text=f"{username} (Group: {group})", width=30, anchor="w").pack(side="left")
            ttk.Button(row, text="Approve", command=lambda u=username: approve_user(u), style='Primary.TButton').pack(side="left", padx=5)
            ttk.Button(row, text="Decline", command=lambda u=username: decline_user(u), style='Danger.TButton').pack(side="left", padx=5)

        if student_users:
            ttk.Button(student_frame, text="Approve All Students", command=lambda: approve_all("Student"), style='Primary.TButton').pack(pady=10)

        for username, _, _ in teacher_users:
            row = ttk.Frame(teacher_frame)
            row.pack(fill="x", pady=5)
            ttk.Label(row, text=username, width=30, anchor="w").pack(side="left")
            ttk.Button(row, text="Approve", command=lambda u=username: approve_user(u), style='Primary.TButton').pack(side="left", padx=5)
            ttk.Button(row, text="Decline", command=lambda u=username: decline_user(u), style='Danger.TButton').pack(side="left", padx=5)

        if teacher_users:
            ttk.Button(teacher_frame, text="Approve All Teachers", command=lambda: approve_all("Teacher"), style='Primary.TButton').pack(pady=10)

    def approve_user(username):
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET approved=1 WHERE username=?", (username,))
        conn.commit()
        conn.close()
        update_user_lists()

    def decline_user(username):
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE username=?", (username,))
        conn.commit()
        conn.close()
        update_user_lists()

    def approve_all(role):
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET approved=1 WHERE approved=0 AND role=?", (role,))
        conn.commit()
        conn.close()
        update_user_lists()

    student_frame = ttk.LabelFrame(root, text="Student Requests", padding=20)
    student_frame.pack(fill="both", expand=True, padx=20, pady=10)

    teacher_frame = ttk.LabelFrame(root, text="Teacher Requests", padding=20)
    teacher_frame.pack(fill="both", expand=True, padx=20, pady=10)

    update_user_lists()

# Login function
def login():
    username = username_entry.get().strip()
    password = password_entry.get().strip()
    role = role_var.get()
    group = group_entry.get().strip()

    # Check for empty fields
    if not username or not password or not group or not role:
        messagebox.showerror("Error", "All fields (including group) are required!")
        return

    # Admin login
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        messagebox.showinfo("Admin Login Successful", "Welcome, Admin!")
        open_admin_portal()
        return

    # Verify group matches registered user
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username=? AND password=? AND role=? AND group_name=? AND approved=1",
                   (username, password, role, group))
    result = cursor.fetchone()
    conn.close()

    if result:
        messagebox.showinfo("Login Successful", f"Welcome, {username}!")
        if role == "Teacher":
            open_teacher_dashboard(username)
        else:
            open_student_dashboard(username)
    else:
        messagebox.showerror("Error", "Invalid credentials, group mismatch, or approval pending.")

# Teacher Dashboard with Group Features
def open_teacher_dashboard(username):
    clear_window(root)
    root.title("Teacher Dashboard")
    root.state('zoomed')  # Maximize window to full screen
    root.configure(bg='#f0f0f0')

    # Logout Button
    ttk.Button(root, text="Logout", command=show_login_screen, style='Danger.TButton').pack(anchor="ne", padx=20, pady=20)

    # Get teacher's group
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT group_name FROM users WHERE username=?", (username,))
    teacher_group = cursor.fetchone()[0]
    conn.close()

    # Center content frame
    main_frame = ttk.Frame(root)
    main_frame.place(relx=0.5, rely=0.5, anchor='center')

    ttk.Label(main_frame, text=f"Welcome, {username}", font=("Verdana", 24, 'bold')).pack(pady=20)
    ttk.Label(main_frame, text=f"Group Admin for: {teacher_group}", font=("Verdana", 18)).pack(pady=10)

    def take_group_attendance():
        os.system(f"python face_recognition_ui.py --group {teacher_group}")

    def manage_group_members():
        manage_window = tk.Toplevel(root)
        manage_window.title("Manage Group Members")
        manage_window.state('zoomed')  # Maximize child window
        manage_window.configure(bg='#f0f0f0')

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("SELECT username, role, approved FROM users WHERE group_name=?", (teacher_group,))
        members = cursor.fetchall()
        conn.close()

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
        ttk.Label(scrollable_frame, text="Role", width=10, anchor="w", font=("Verdana", 12, "bold")).grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(scrollable_frame, text="Approved", width=10, anchor="w", font=("Verdana", 12, "bold")).grid(row=0, column=2, padx=5, pady=5)
        ttk.Label(scrollable_frame, text="Action", width=10, anchor="w", font=("Verdana", 12, "bold")).grid(row=0, column=3, padx=5, pady=5)

        for i, (user, role, approved) in enumerate(members, start=1):
            approved_text = "Yes" if approved else "No"
            ttk.Label(scrollable_frame, text=user, width=20, anchor="w").grid(row=i, column=0, padx=5, pady=5)
            ttk.Label(scrollable_frame, text=role, width=10, anchor="w").grid(row=i, column=1, padx=5, pady=5)
            ttk.Label(scrollable_frame, text=approved_text, width=10, anchor="w").grid(row=i, column=2, padx=5, pady=5)
            if user != username:  # Prevent self-removal
                ttk.Button(scrollable_frame, text="Remove", command=lambda u=user: remove_user(u, manage_window), style='Danger.TButton').grid(row=i, column=3, padx=5, pady=5)

        canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y")

    def remove_user(username_to_remove, window):
        confirm = messagebox.askyesno("Confirm", f"Remove {username_to_remove} from group?")
        if confirm:
            conn = sqlite3.connect("users.db")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE username=?", (username_to_remove,))
            conn.commit()
            conn.close()
            messagebox.showinfo("Removed", f"{username_to_remove} has been removed.")
            window.destroy()
            manage_group_members()

    # Group Student Approvals
    def approve_group_students():
        approve_window = tk.Toplevel(root)
        approve_window.title("Approve Students in Your Group")
        approve_window.state('zoomed')  # Maximize child window
        approve_window.configure(bg='#f0f0f0')

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users WHERE group_name=? AND role='Student' AND approved=0", (teacher_group,))
        pending_students = cursor.fetchall()
        conn.close()

        for student in pending_students:
            student_name = student[0]
            row = ttk.Frame(approve_window)
            row.pack(fill="x", pady=5, padx=20)
            ttk.Label(row, text=student_name, width=30, anchor="w").pack(side="left")
            ttk.Button(row, text="Approve", command=lambda s=student_name: approve_student(s), style='Primary.TButton').pack(side="left", padx=5)
            ttk.Button(row, text="Decline", command=lambda s=student_name: decline_student(s), style='Danger.TButton').pack(side="left", padx=5)

    def approve_student(username):
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET approved=1 WHERE username=?", (username,))
        conn.commit()
        conn.close()
        messagebox.showinfo("Approved", f"{username} approved!")

    def decline_student(username):
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE username=?", (username,))
        conn.commit()
        conn.close()
        messagebox.showinfo("Declined", f"{username} removed!")

    ttk.Button(main_frame, text="Approve Student Requests", command=approve_group_students, style='Warning.TButton').pack(pady=20, ipadx=20, ipady=10)
    ttk.Button(main_frame, text="Take Group Attendance", command=take_group_attendance, style='Primary.TButton').pack(pady=20, ipadx=20, ipady=10)
    ttk.Button(main_frame, text="Manage Group Members", command=manage_group_members, style='Primary.TButton').pack(pady=20, ipadx=20, ipady=10)

# Student Dashboard
def open_student_dashboard(username):
    clear_window(root)
    root.title("Student Dashboard")
    root.state('zoomed')  # Maximize window to full screen
    root.configure(bg='#f0f0f0')
    
    # Logout Button
    ttk.Button(root, text="Logout", command=show_login_screen, style='Danger.TButton').pack(anchor="ne", padx=20, pady=20)
    
    # Get student's group
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT group_name FROM users WHERE username=?", (username,))
    student_group = cursor.fetchone()[0]
    conn.close()
    
    # Center content frame
    main_frame = ttk.Frame(root)
    main_frame.place(relx=0.5, rely=0.5, anchor='center')
    
    ttk.Label(main_frame, text=f"Welcome, {username}", font=("Verdana", 24, 'bold')).pack(pady=20)
    ttk.Label(main_frame, text=f"Group: {student_group}", font=("Verdana", 18)).pack(pady=10)
    
    attendance_records = fetch_attendance(username)
    attendance_text = "Date\tStatus\n" + "\n".join([f"{date}\t{status}" for date, status in attendance_records])
    attendance_label = ttk.Label(main_frame, text=attendance_text, font=("Verdana", 14), justify='left')
    attendance_label.pack(pady=20)

# UI Setup
setup_db()
root = tk.Tk()
setup_styles()
show_login_screen()
root.mainloop()