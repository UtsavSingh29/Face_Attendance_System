import csv
import os
import cv2

def TakeImage(l1, l2, l3, haarcasecade_path, trainimage_path, message, err_screen, text_to_speech):
    # Input validation
    if not l1 and not l2:
        t = 'Please Enter your Enrollment Number and Name.'
        text_to_speech(t)
        err_screen()
        return
    elif not l1:
        t = 'Please Enter your Enrollment Number.'
        text_to_speech(t)
        err_screen()
        return
    elif not l2:
        t = 'Please Enter your Name.'
        text_to_speech(t)
        err_screen()
        return
    elif not l3:
        t = 'Please Enter your Group.'
        text_to_speech(t)
        err_screen()
        return

    try:
        Enrollment = l1.strip()
        Name = l2.strip()
        Group = l3.strip()
        directory = f"{Group}_{Enrollment}_{Name}"
        path = os.path.join(trainimage_path, directory)

        # Skip if folder already exists
        if os.path.exists(path):
            t = "Student data already exists."
            message.configure(text=t)
            text_to_speech(t)
            return

        os.makedirs(path)

        cam = cv2.VideoCapture(0)
        cv2.namedWindow("Frame", cv2.WND_PROP_FULLSCREEN)
        cv2.setWindowProperty("Frame", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

        detector = cv2.CascadeClassifier(haarcasecade_path)
        sampleNum = 0

        while True:
            ret, img = cam.read()
            if not ret:
                break

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = detector.detectMultiScale(gray, 1.3, 5)

            for (x, y, w, h) in faces:
                sampleNum += 1
                face_img = gray[y:y + h, x:x + w]
                cv2.imwrite(f"{path}\\{Group}_{Name}_{Enrollment}_{sampleNum}.jpg", face_img)
                cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)

            cv2.imshow("Frame", img)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
            elif sampleNum >= 50:
                break

        cam.release()
        cv2.destroyAllWindows()

        # Ensure StudentDetails directory exists
        os.makedirs("StudentDetails", exist_ok=True)

        # Save details to CSV
        file_path = "StudentDetails/studentdetails.csv"
        file_exists = os.path.isfile(file_path)
        with open(file_path, "a+", newline='') as csvFile:
            writer = csv.writer(csvFile)
            if not file_exists:
                writer.writerow(["Enrollment", "Name", "Group"])
            writer.writerow([Enrollment, Name, Group])

        res = f"Images Saved for:\nER No: {Enrollment}\nName: {Name}\nGroup: {Group}"
        message.configure(text=res)
        text_to_speech(res)

    except Exception as e:
        t = f"Error: {str(e)}"
        message.configure(text=t)
        text_to_speech(t)
