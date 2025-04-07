import tkinter as tk
from tkinter import messagebox
import sqlite3
import os

# Predefined Admin Credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# Database setup
def setup_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE,
                        password TEXT,
                        role TEXT,
                        approved INTEGER DEFAULT 0)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS attendance (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT,
                        date TEXT,
                        status TEXT)''')
    conn.commit()
    conn.close()

# Function to check login
def check_login(username, password, role):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username=? AND password=? AND role=? AND approved=1", (username, password, role))
    result = cursor.fetchone()
    conn.close()
    return result

# Function to fetch attendance
def fetch_attendance(username):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT date, status FROM attendance WHERE username=?", (username,))
    records = cursor.fetchall()
    conn.close()
    return records

# Function to request signup
def signup():
    username = username_entry.get()
    password = password_entry.get()
    role = role_var.get()
    
    if not username or not password:
        messagebox.showerror("Error", "All fields are required!")
        return
    
    try:
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password, role, approved) VALUES (?, ?, ?, 0)", (username, password, role))
        conn.commit()
        conn.close()
        messagebox.showinfo("Signup Request Sent", "Wait for Admin Approval!")
    except sqlite3.IntegrityError:
        messagebox.showerror("Error", "Username already exists!")

def open_admin_portal():
    admin_window = tk.Tk()
    admin_window.title("Admin Portal")
    admin_window.geometry("700x600")

    student_frame = tk.LabelFrame(admin_window, text="Student Requests", padx=10, pady=10)
    student_frame.pack(fill="both", expand=True, padx=10, pady=5)

    teacher_frame = tk.LabelFrame(admin_window, text="Teacher Requests", padx=10, pady=10)
    teacher_frame.pack(fill="both", expand=True, padx=10, pady=5)

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

    def view_all_users_by_role(role):
        view_window = tk.Toplevel(admin_window)
        view_window.title(f"All {role}s")
        view_window.geometry("500x400")

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("SELECT username, password, role, approved FROM users WHERE role=?", (role,))
        users = cursor.fetchall()
        conn.close()

        text = tk.Text(view_window, wrap="none")
        scrollbar = tk.Scrollbar(view_window, command=text.yview)
        text.configure(yscrollcommand=scrollbar.set)

        text.insert("end", f"{'Username':<20}{'Role':<10}{'Approved':<10}\n")
        text.insert("end", "-"*45 + "\n")
        for user in users:
            approved_text = "Yes" if user[3] else "No"
            text.insert("end", f"{user[0]:<20}{user[2]:<10}{approved_text:<10}\n")

        text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
    def view_all_registered_users():
        view_window = tk.Toplevel()
        view_window.title("All Registered Users")
        view_window.geometry("600x500")

        student_frame = tk.LabelFrame(view_window, text="Students", padx=10, pady=10)
        student_frame.pack(fill="both", expand=True, padx=10, pady=5)

        teacher_frame = tk.LabelFrame(view_window, text="Teachers", padx=10, pady=10)
        teacher_frame.pack(fill="both", expand=True, padx=10, pady=5)

        def refresh_data():
            for widget in student_frame.winfo_children():
                widget.destroy()
            for widget in teacher_frame.winfo_children():
                widget.destroy()

            conn = sqlite3.connect("users.db")
            cursor = conn.cursor()
            cursor.execute("SELECT username, role, approved FROM users")
            users = cursor.fetchall()
            conn.close()

            students = [u for u in users if u[1] == "Student"]
            teachers = [u for u in users if u[1] == "Teacher"]

            def populate_frame(frame, data):
                tk.Label(frame, text=f"{'Username':<25}{'Approved':<10}", font=("Courier", 10, "bold")).grid(row=0, column=0, sticky="w")
                tk.Label(frame, text="", width=10).grid(row=0, column=1)  # spacing
                tk.Label(frame, text="Action", font=("Courier", 10, "bold")).grid(row=0, column=2)

                for idx, user in enumerate(data, start=1):
                    username, _, approved = user
                    approved_text = "Yes" if approved else "No"
                    tk.Label(frame, text=f"{username:<25}{approved_text:<10}", font=("Courier", 10)).grid(row=idx, column=0, sticky="w")

                    def delete_user(u=username):
                        confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to remove {u}?")
                        if confirm:
                            conn = sqlite3.connect("users.db")
                            cursor = conn.cursor()
                            cursor.execute("DELETE FROM users WHERE username=?", (u,))
                            conn.commit()
                            conn.close()
                            refresh_data()

                    tk.Button(frame, text="Remove", command=delete_user).grid(row=idx, column=2)

            populate_frame(student_frame, students)
            populate_frame(teacher_frame, teachers)

        refresh_data()


    def update_user_lists():
        for widget in student_frame.winfo_children():
            widget.destroy()
        for widget in teacher_frame.winfo_children():
            widget.destroy()

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("SELECT username, role FROM users WHERE approved=0")
        users = cursor.fetchall()
        conn.close()

        student_users = [u for u in users if u[1] == "Student"]
        teacher_users = [u for u in users if u[1] == "Teacher"]

        for username, _ in student_users:
            row = tk.Frame(student_frame)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=username, width=25, anchor="w").pack(side="left")
            tk.Button(row, text="Approve", command=lambda u=username: approve_user(u)).pack(side="left", padx=5)
            tk.Button(row, text="Decline", command=lambda u=username: decline_user(u)).pack(side="left", padx=5)

        if student_users:
            tk.Button(student_frame, text="Approve All Students", command=lambda: approve_all("Student")).pack(pady=5)

        tk.Button(student_frame, text="View All Students", command=lambda: view_all_users_by_role("Student")).pack(pady=5)

        for username, _ in teacher_users:
            row = tk.Frame(teacher_frame)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=username, width=25, anchor="w").pack(side="left")
            tk.Button(row, text="Approve", command=lambda u=username: approve_user(u)).pack(side="left", padx=5)
            tk.Button(row, text="Decline", command=lambda u=username: decline_user(u)).pack(side="left", padx=5)

        if teacher_users:
            tk.Button(teacher_frame, text="Approve All Teachers", command=lambda: approve_all("Teacher")).pack(pady=5)

        tk.Button(teacher_frame, text="View All Teachers", command=lambda: view_all_users_by_role("Teacher")).pack(pady=5)

    update_user_lists()
    tk.Button(admin_window, text="View All Registered Users", command=view_all_registered_users).pack(pady=10)
    admin_window.mainloop()


# Login function
def login():
    username = username_entry.get()
    password = password_entry.get()
    role = role_var.get()
    
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        messagebox.showinfo("Admin Login Successful", "Welcome, Admin!")
        root.destroy()
        open_admin_portal()
        return
    
    if check_login(username, password, role):
        messagebox.showinfo("Login Successful", f"Welcome, {username}!")
        root.destroy()
        if role == "Teacher":
            open_teacher_dashboard()
        else:
            open_student_dashboard(username)
    else:
        messagebox.showerror("Error", "Invalid Credentials or Approval Pending!")

# Open teacher dashboard
def open_teacher_dashboard():
    os.system("python face_recognition_ui.py")

# Open student dashboard
def open_student_dashboard(username):
    student_window = tk.Tk()
    student_window.title("Student Dashboard")
    student_window.geometry("400x300")
    tk.Label(student_window, text=f"Welcome, {username}!", font=("Verdana", 20)).pack()
    
    attendance_records = fetch_attendance(username)
    attendance_text = "Date\tStatus\n" + "\n".join([f"{date}\t{status}" for date, status in attendance_records])
    attendance_label = tk.Label(student_window, text=attendance_text, font=("Verdana", 12))
    attendance_label.pack()
    
    student_window.mainloop()

# UI Setup
setup_db()
root = tk.Tk()
root.title("Login / Signup")
root.geometry("300x300")

tk.Label(root, text="Username").pack()
username_entry = tk.Entry(root)
username_entry.pack()

tk.Label(root, text="Password").pack()
password_entry = tk.Entry(root, show="*")
password_entry.pack()

role_var = tk.StringVar(value="Student")
tk.Radiobutton(root, text="Student", variable=role_var, value="Student").pack()
tk.Radiobutton(root, text="Teacher", variable=role_var, value="Teacher").pack()

tk.Button(root, text="Login", command=login).pack()
tk.Button(root, text="Signup", command=signup).pack()

root.mainloop()
