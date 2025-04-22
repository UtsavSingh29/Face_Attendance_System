import tkinter as tk
from tkinter import *
import os
import argparse
from PIL import Image, ImageTk
import pyttsx3

# Project modules
import show_attendance
import takeImage
import trainImage
import automaticAttedance

# Argument parser
parser = argparse.ArgumentParser()
parser.add_argument('--group', help='Filter by group')
args = parser.parse_args()

# TTS
def text_to_speech(user_text):
    engine = pyttsx3.init()
    engine.say(user_text)
    engine.runAndWait()

# Paths
haarcasecade_path = "haarcascade_frontalface_default.xml"
trainimagelabel_path = "./TrainingImageLabel/Trainner.yml"
trainimage_path = "./TrainingImage"
studentdetail_path = "./StudentDetails/studentdetails.csv"
attendance_path = "Attendance"

if not os.path.exists(trainimage_path):
    os.makedirs(trainimage_path)

# Tkinter window
window = Tk()
window.title("Face Recognizer")
window.attributes('-fullscreen', True)
window.configure(background="#1c1c1c")

def toggle_fullscreen(event=None):
    window.attributes('-fullscreen', not window.attributes('-fullscreen'))

def exit_fullscreen(event=None):
    window.attributes('-fullscreen', False)

window.bind("<F11>", toggle_fullscreen)
window.bind("<Escape>", exit_fullscreen)

def err_screen():
    global sc1
    sc1 = tk.Tk()
    sc1.geometry("400x110")
    sc1.title("Warning!!")
    sc1.configure(background="#1c1c1c")
    sc1.resizable(0, 0)
    tk.Label(sc1, text="Enrollment & Name required!!!", fg="yellow", bg="#1c1c1c",
             font=("Verdana", 16, "bold")).pack()
    tk.Button(sc1, text="OK", command=lambda: sc1.destroy(), fg="yellow", bg="#333333",
              width=9, height=1, activebackground="red", font=("Verdana", 16, "bold")).place(x=110, y=50)

def exit_app():
    window.destroy()

# Logo
logo = Image.open("UI_Image/0001.png").resize((50, 47), Image.LANCZOS)
logo1 = ImageTk.PhotoImage(logo)
titl = tk.Label(window, bg="#1c1c1c", relief=RIDGE, bd=10, font=("Verdana", 30, "bold"))
titl.pack(fill=X)
tk.Label(window, image=logo1, bg="#1c1c1c").place(x=470, y=10)

# Title
tk.Label(window, text="CAMATTEND", bg="#1c1c1c", fg="yellow",
         font=("Verdana", 27, "bold")).place(x=525, y=12)

# Welcome
tk.Label(window, text="Welcome to CamAttend", bg="#1c1c1c", fg="blue",
         bd=10, font=("Verdana", 35, "bold")).pack()

# Icons
ri = ImageTk.PhotoImage(Image.open("UI_Image/register.png"))
ai = ImageTk.PhotoImage(Image.open("UI_Image/attendance.png"))
vi = ImageTk.PhotoImage(Image.open("UI_Image/verifyy.png"))
Label(window, image=ri).place(x=100, y=270)
Label(window, image=ai).place(x=980, y=270)
Label(window, image=vi).place(x=600, y=270)

# Register face
def TakeImageUI():
    ImageUI = Tk()
    ImageUI.title("Take Student Image")
    ImageUI.geometry("780x480")
    ImageUI.configure(background="#1c1c1c")
    ImageUI.resizable(0, 0)

    tk.Label(ImageUI, bg="#1c1c1c", relief=RIDGE, bd=10,
             font=("Verdana", 30, "bold")).pack(fill=X)
    tk.Label(ImageUI, text="Register Your Face", bg="#1c1c1c", fg="blue",
             font=("Verdana", 30, "bold")).place(x=270, y=12)

    tk.Label(ImageUI, text="Roll No", width=10, height=2, bg="#1c1c1c", fg="yellow",
             bd=5, relief=RIDGE, font=("Verdana", 14)).place(x=120, y=130)
    txt1 = tk.Entry(ImageUI, width=17, bd=5, bg="#333333", fg="yellow",
                    relief=RIDGE, font=("Verdana", 18, "bold"))
    txt1.place(x=250, y=130)

    tk.Label(ImageUI, text="Name", width=10, height=2, bg="#1c1c1c", fg="yellow",
             bd=5, relief=RIDGE, font=("Verdana", 14)).place(x=120, y=200)
    txt2 = tk.Entry(ImageUI, width=17, bd=5, bg="#333333", fg="yellow",
                    relief=RIDGE, font=("Verdana", 18, "bold"))
    txt2.place(x=250, y=200)

    tk.Label(ImageUI, text="Group", width=10, height=2, bg="#1c1c1c", fg="yellow",
             bd=5, relief=RIDGE, font=("Verdana", 14)).place(x=120, y=270)
    txt3 = tk.Entry(ImageUI, width=17, bd=5, bg="#333333", fg="yellow",
                    relief=RIDGE, font=("Verdana", 18, "bold"))
    txt3.place(x=250, y=270)

    message = tk.Label(ImageUI, text="", width=32, height=2, bd=5,
                       bg="#333333", fg="yellow", relief=RIDGE,
                       font=("Verdana", 14, "bold"))
    message.place(x=250, y=340)

    def take_image():
        if args.group and txt3.get() != args.group:
            message.config(text=f"Must register for group: {args.group}", fg="red")
            return
        takeImage.TakeImage(txt1.get(), txt2.get(), txt3.get(), haarcasecade_path,
                            trainimage_path, message, err_screen, text_to_speech)
        txt1.delete(0, "end")
        txt2.delete(0, "end")
        txt3.delete(0, "end")

    def train_images():
        trainImage.TrainImage(haarcasecade_path, trainimage_path,
                              trainimagelabel_path, message, text_to_speech)
        message.config(text="Model Trained Successfully!", fg="green")

    tk.Button(ImageUI, text="Take Image", command=take_image, bd=10,
              font=("Verdana", 18, "bold"), bg="#333333", fg="yellow",
              height=2, width=12, relief=RIDGE).place(x=130, y=400)
    tk.Button(ImageUI, text="Train Image", command=train_images, bd=10,
              font=("Verdana", 18, "bold"), bg="#333333", fg="yellow",
              height=2, width=12, relief=RIDGE).place(x=400, y=400)

    ImageUI.mainloop()

# Group label
if args.group:
    tk.Label(window, text=f"GROUP MODE: {args.group}", fg="red",
             bg="#1c1c1c", font=("Verdana", 16, "bold")).place(x=550, y=200)

# Buttons
tk.Button(window, text="Register", command=TakeImageUI, bd=10,
          font=("Verdana", 16), bg="black", fg="yellow",
          height=2, width=17).place(x=100, y=520)

tk.Button(window, text="Take Attendance",
          command=lambda: automaticAttedance.subjectChoose(text_to_speech, args.group),
          bd=10, font=("Verdana", 16), bg="black", fg="yellow",
          height=2, width=17).place(x=600, y=520)

tk.Button(window, text="View Attendance",
          command=lambda: show_attendance.subjectchoose(text_to_speech, args.group),
          bd=10, font=("Verdana", 16), bg="black", fg="yellow",
          height=2, width=17).place(x=1000, y=520)

tk.Button(window, text="Exit", command=exit_app, bd=10,
          font=("Verdana", 16, "bold"), bg="yellow", fg="white",
          height=1, width=15).place(x=600, y=620)

window.mainloop()
