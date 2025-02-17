import cv2
import numpy as np
import face_recognition
import mysql.connector
from datetime import datetime
import tkinter as tk
from tkinter import simpledialog, messagebox
from PIL import Image, ImageTk
import pickle

# Connect to MySQL Database
conn = mysql.connector.connect(
    host="52.20.7.147",
    user="petalhosuser",
    password="PetalHosDb@20#19",
    database="face_attendance"
)
cursor = conn.cursor()

class FaceRecognitionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Face Recognition Attendance")
        self.root.geometry("800x500")
        self.root.configure(bg="white")

        # Video Frame
        self.video_label = tk.Label(self.root)
        self.video_label.pack(side=tk.LEFT, padx=10, pady=10)

        # Buttons
        button_frame = tk.Frame(self.root, bg="white")
        button_frame.pack(side=tk.RIGHT, padx=20, pady=20)

        tk.Button(button_frame, text="Register", command=self.register_face, width=20, height=2).pack(pady=10)
        tk.Button(button_frame, text="Mark Attendance", command=self.mark_attendance, width=20, height=2).pack(pady=10)
        tk.Button(button_frame, text="Delete ID", command=self.delete_face, width=20, height=2).pack(pady=10)
        tk.Button(button_frame, text="Exit", command=self.root.quit, width=20, height=2, bg="red", fg="white").pack(pady=10)

        self.cap = cv2.VideoCapture(0)
        self.update_video()

    def update_video(self):
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (400, 300))
            img = Image.fromarray(frame)
            imgtk = ImageTk.PhotoImage(image=img)
            self.video_label.imgtk = imgtk
            self.video_label.config(image=imgtk)
        self.root.after(10, self.update_video)

    def register_face(self):
        """Capture and register face into the database"""
        ret, frame = self.cap.read()
        if ret:
            name = simpledialog.askstring("Input", "Enter Name:")
            if name:
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                face_encodings = face_recognition.face_encodings(rgb_frame)

                if face_encodings:
                    face_encoding_blob = pickle.dumps(face_encodings[0])  # Convert encoding to binary

                    # Insert into database
                    cursor.execute('INSERT INTO users (name, face_encoding) VALUES (%s, %s)', (name, face_encoding_blob))
                    conn.commit()

                    messagebox.showinfo("Success", f"{name} registered successfully!")
                else:
                    messagebox.showwarning("Face Not Found", "No face detected. Please try again.")

    def fetch_registered_faces(self):
        """Fetch registered faces from the database"""
        cursor.execute('SELECT id, name, face_encoding FROM users')
        records = cursor.fetchall()

        encodings, names, ids = [], [], []
        for record in records:
            user_id, name, encoding_blob = record
            encoding = pickle.loads(encoding_blob)

            encodings.append(encoding)
            names.append(name)
            ids.append(user_id)

        return encodings, names, ids

    def mark_attendance(self):
        """Mark attendance for recognized faces"""
        known_encodings, known_names, known_ids = self.fetch_registered_faces()

        ret, frame = self.cap.read()
        if ret:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_frame)
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

            for encoding in face_encodings:
                matches = face_recognition.compare_faces(known_encodings, encoding)
                face_distances = face_recognition.face_distance(known_encodings, encoding)
                best_match_index = np.argmin(face_distances) if matches else -1

                if best_match_index != -1 and matches[best_match_index]:
                    name = known_names[best_match_index]
                    user_id = known_ids[best_match_index]
                    date = datetime.now().strftime('%Y-%m-%d')
                    time = datetime.now().strftime('%H:%M:%S')

                    # Check if attendance already marked today
                    cursor.execute('SELECT * FROM attendance WHERE user_id = %s AND date = %s', (user_id, date))
                    result = cursor.fetchone()

                    if result is None:
                        cursor.execute('INSERT INTO attendance (user_id, date, time) VALUES (%s, %s, %s)', (user_id, date, time))
                        conn.commit()
                        messagebox.showinfo("Attendance Marked", f"Attendance recorded for {name}")
                    else:
                        messagebox.showinfo("Already Marked", f"Attendance already marked for {name} today.")
                else:
                    messagebox.showwarning("Unregistered", "Person not registered!")

    def delete_face(self):
        """Delete a registered face from the database"""
        name = simpledialog.askstring("Delete Face", "Enter Name to Delete:")
        if name:
            # Check if the user exists
            cursor.execute('SELECT id FROM users WHERE name = %s', (name,))
            user = cursor.fetchone()

            if user:
                user_id = user[0]
                confirm = messagebox.askquestion("Delete", f"Are you sure you want to delete {name}?", icon='warning')
                if confirm == 'yes':
                    # Delete attendance records first
                    cursor.execute('DELETE FROM attendance WHERE user_id = %s', (user_id,))
                    conn.commit()

                    # Now delete the user
                    cursor.execute('DELETE FROM users WHERE id = %s', (user_id,))
                    conn.commit()

                    messagebox.showinfo("Success", f"{name} deleted successfully!")
            else:
                messagebox.showerror("Error", "Name not found!")

if __name__ == "__main__":
    root = tk.Tk()
    app = FaceRecognitionApp(root)
    root.mainloop()

    # Close the database connection on exit
    conn.close()
