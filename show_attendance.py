import pandas as pd
from glob import glob
import os
import tkinter
import csv
import numpy as np
import tkinter as tk
from tkinter import *

def subjectchoose(text_to_speech):
    def calculate_attendance():
        Subject = tx.get().strip()
        if Subject == "":
            text_to_speech("Please enter the subject name.")
            return

        filenames = glob(f"Attendance\\{Subject}\\{Subject}*.csv")

        if not filenames:
            text_to_speech(f"No attendance files found for subject: {Subject}")
            return
        
        df_list = [pd.read_csv(f, dtype={'Name': str}) for f in filenames]  # Ensure "Name" is read as string
        newdf = df_list[0]

        for i in range(1, len(df_list)):
            newdf = newdf.merge(df_list[i], how="outer")

        newdf.fillna(0, inplace=True)

        # Ensure 'Name' column remains a clean string
        if 'Name' in newdf.columns:
            newdf['Name'] = newdf['Name'].astype(str)  # Convert to string
            newdf['Name'] = newdf['Name'].str.replace(r"[\[\]']", "", regex=True)  # Remove brackets and quotes ✅

        # Convert all other columns (except "Enrollment" and "Name") to numeric
        for col in newdf.columns[2:]:  # Skip Enrollment and Name
            newdf[col] = pd.to_numeric(newdf[col], errors='coerce')

        # Initialize Attendance column
        newdf["Attendance"] = "0%"

        for i in range(len(newdf)):
            numeric_cols = newdf.iloc[i, 2:-1]  # Skip Enrollment and Name, but take numeric columns

            mean_attendance = numeric_cols.mean()
            if not np.isnan(mean_attendance):  # Check if mean is valid
                newdf.at[i, "Attendance"] = f"{int(round(mean_attendance * 100))}%"

        output_path = f"Attendance\\{Subject}\\attendance.csv"
        newdf.to_csv(output_path, index=False)

        root = Toplevel(subject)
        root.title(f"Attendance of {Subject}")
        root.configure(background="black")

        with open(output_path) as file:
            reader = csv.reader(file)
            for r, row in enumerate(reader):
                for c, cell in enumerate(row):
                    label = tkinter.Label(
                        root, text=cell, width=15, height=1,  # Increased width for names
                        fg="yellow", font=("times", 15, "bold"),
                        bg="black", relief=tkinter.RIDGE
                    )
                    label.grid(row=r, column=c)

        root.mainloop()
        print(newdf)

    def Attf():
        sub = tx.get().strip()
        if sub == "":
            text_to_speech("Please enter the subject name!!!")
        else:
            os.startfile(f"Attendance\\{sub}")

    subject = Tk()
    subject.title("Subject...")
    subject.geometry("580x320")
    subject.resizable(0, 0)
    subject.configure(background="black")

    tk.Label(subject, text="Which Subject of Attendance?", bg="black", fg="green", font=("arial", 25)).place(x=100, y=12)

    tk.Label(subject, text="Enter Subject", width=10, height=2, bg="black", fg="yellow", bd=5, relief=RIDGE, font=("times new roman", 15)).place(x=50, y=100)

    tx = tk.Entry(subject, width=15, bd=5, bg="black", fg="yellow", relief=RIDGE, font=("times", 30, "bold"))
    tx.place(x=190, y=100)

    tk.Button(subject, text="Check Sheets", command=Attf, bd=7, font=("times new roman", 15), bg="black", fg="yellow", height=2, width=10, relief=RIDGE).place(x=360, y=170)

    tk.Button(subject, text="View Attendance", command=calculate_attendance, bd=7, font=("times new roman", 15), bg="black", fg="yellow", height=2, width=12, relief=RIDGE).place(x=195, y=170)

    subject.mainloop()
