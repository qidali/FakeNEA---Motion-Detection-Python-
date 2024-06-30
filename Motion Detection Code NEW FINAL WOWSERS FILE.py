import numpy as np
import cv2 as cv
import time
import tkinter as tk
import threading
import sqlite3
import os

# Initialize camera and variables
kernel = np.ones((3, 3), dtype=np.uint8)
cap = cv.VideoCapture(0)
if not cap.isOpened():
    print("Cant open Camera, simply a Skill Issue")
    exit()

ret, frame_last = cap.read()
if not ret:
    print("Cant receive frame (Maybe you should have done your helper tasks!)")
    exit()

gray_last = cv.cvtColor(frame_last, cv.COLOR_BGR2GRAY)
frame_width = int(cap.get(cv.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv.CAP_PROP_FRAME_HEIGHT))
fourcc = cv.VideoWriter_fourcc(*'MJPG')
event_flag, armed, count = False, False, 0
max_videos = 5
video_files, out = [], None

# Database setup
connection = sqlite3.connect("motion_events.db")
cursor = connection.cursor()
cursor.execute("DROP TABLE IF EXISTS LOG")
cursor.execute("""CREATE TABLE LOG (
                    Event_ID INTEGER PRIMARY KEY,
                    Camera_ID INTEGER
                );""")

# Functions for GUI and video processing
def activate_system():
    global armed
    armed = True
    start_recording()

def deactivate_system():
    global armed, out
    armed = False
    if out is not None:
        out.release()
        out = None

def start_recording():
    if armed:
        create_video()
        threading.Timer(30, start_recording).start()

def create_video():
    global count, out, video_files
    if out is not None:
        out.release()

    vidname = "video" + str(count) + ".avi"
    out = cv.VideoWriter(vidname, fourcc, 30, (frame_width, frame_height))
    if not out.isOpened():
        print("The video output does not work sorry")
        out = None
    else:
        count += 1
        video_files.append(vidname)
        if len(video_files) > max_videos:
            os.remove(video_files.pop(0))
        refresh_video_list()

def play_selected_video():
    video_path = video_entry.get()
    if video_path:
        cap_video = cv.VideoCapture(video_path)
        new_window = tk.Toplevel(root)
        new_window.title("Video Playback")
        video_frame = tk.Label(new_window)
        video_frame.pack(fill=tk.BOTH, expand=True)
        while cap_video.isOpened():
            ret, frame = cap_video.read()
            if not ret:
                break
            frame_rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
            frame_processed = cv.cvtColor(frame_rgb, cv.COLOR_RGB2BGR)
            imgtk = cv_to_tk(frame_processed)
            video_frame.imgtk = imgtk
            video_frame.config(image=imgtk)
            video_frame.update()
            time.sleep(0.001)
        cap_video.release()

def cv_to_tk(frame):
    return tk.PhotoImage(data=cv.imencode('.ppm', frame)[1].tobytes())

def refresh_video_list():
    video_listbox.delete(0, tk.END)
    for filename in video_files:
        video_listbox.insert(tk.END, filename)

def update_live_feed():
    global frame_last, gray_last, event_flag, out, armed

    ret, frame = cap.read()
    if not ret:
        root.after(10, update_live_feed)
        return

    gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    gray_diff = cv.absdiff(gray, gray_last)
    gray_diff = cv.medianBlur(gray_diff, 5)
    mask = cv.adaptiveThreshold(gray_diff, 255, cv.ADAPTIVE_THRESH_GAUSSIAN_C, cv.THRESH_BINARY_INV, 9, 3)
    mask = cv.medianBlur(mask, 3)
    mask = cv.morphologyEx(mask, cv.MORPH_CLOSE, kernel, iterations=1)

    contours, _ = cv.findContours(mask, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
    frame_last = frame
    gray_last = gray
    cv.drawContours(frame, contours, -1, (0, 255, 0), 3)

    if len(contours) > 0 and armed and not event_flag:
        cursor.execute("INSERT INTO LOG (Camera_ID) VALUES (?)", (1,))
        connection.commit()
        event_flag = True
    if event_flag and armed and out is not None:
        out.write(frame)

    frame_rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
    frame_processed = cv.cvtColor(frame_rgb, cv.COLOR_RGB2BGR)
    imgtk = cv_to_tk(frame_processed)
    live_feed_frame.imgtk = imgtk
    live_feed_frame.config(image=imgtk)

    root.after(10, update_live_feed)

# GUI setup
root = tk.Tk()
root.title("Motion Detection System Wowsers")

camera_frame = tk.Frame(root)
camera_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

control_frame = tk.Frame(root)
control_frame.pack(side=tk.RIGHT, fill=tk.BOTH)

live_feed_frame = tk.Label(camera_frame)
live_feed_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

button_frame = tk.Frame(control_frame)
button_frame.pack(side=tk.TOP, fill=tk.X)

log_frame = tk.Frame(control_frame)
log_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

arm_button = tk.Button(button_frame, text="Arm", command=activate_system)
arm_button.pack(side=tk.LEFT, padx=5, pady=5)

disarm_button = tk.Button(button_frame, text="Disarm", command=deactivate_system)
disarm_button.pack(side=tk.RIGHT, padx=5, pady=5)

video_entry = tk.Entry(log_frame, width=50)
video_entry.pack(padx=5, pady=5, fill=tk.X)

play_video_button = tk.Button(log_frame, text="Play Video", command=play_selected_video)
play_video_button.pack(padx=5, pady=5, fill=tk.X)

video_listbox = tk.Listbox(log_frame)
video_listbox.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)

refresh_video_list()
update_live_feed()
root.mainloop()

cap.release()
if out is not None:
    out.release()
cv.destroyAllWindows()
connection.close()
