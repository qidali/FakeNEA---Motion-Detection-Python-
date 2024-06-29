import numpy as np
import cv2 as cv
import time
import tkinter as tk
from tkinter import ttk
import threading
import sqlite3

kernel = np.ones((3,3), np.uint8)
cap = cv.VideoCapture(0)
if not cap.isOpened():
    print("Can't open camera, simply a skill issue")
    exit()

ret, frame_last = cap.read()
gray_last = cv.cvtColor(frame_last, cv.COLOR_BGR2GRAY)

count = 0
event_flag = False
fourcc = cv.VideoWriter_fourcc(*'MJPG')
on = False
videos = []
anyOutputs = None

# Function to handle video capture and processing
def video_capture():
    global count, event_flag, gray_last, frame_last, on
    while on:
        ret, frame = cap.read()
        if not ret:
            print('can\'t receive frame (stream end?). Exiting ...')
            break

        gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
        gray_diff = cv.subtract(gray, gray_last)
        gray_diff = cv.medianBlur(gray_diff, 5)
        mask = cv.adaptiveThreshold(gray_diff, 255, cv.ADAPTIVE_THRESH_GAUSSIAN_C, cv.THRESH_BINARY_INV, 9, 3)
        mask = cv.medianBlur(mask, 3)
        mask = cv.morphologyEx(mask, cv.MORPH_CLOSE, kernel, iterations=1)

        contours, _ = cv.findContours(mask, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
        frame_last = frame
        gray_last = gray
        cv.drawContours(frame, contours, -1, (0,255,0), 3)
        
        cv.imshow('mask', mask)

        vidname = "video"+str(count)+".avi"
        out = cv.VideoWriter(vidname, fourcc, 30, (640,480))
        count += 1
        event_flag = True

        if cv.waitKey(1) == ord('q'):
            break

# Start video capture
def start_video():
    global on
    on = True
    threading.Thread(target=video_capture).start()

# Stop video capture
def stop_video():
    global on
    on = False
    cv.destroyAllWindows()

# GUI setup
root = tk.Tk()
root.title("chair stealer")

start_button = tk.Button(root, text="Start", command=start_video)
start_button.pack(side=tk.LEFT)

stop_button = tk.Button(root, text="Stop", command=stop_video)
stop_button.pack(side=tk.RIGHT)

# Database setup
connection = sqlite3.connect("motion_events.db")
cursor = connection.cursor()
cursor.execute("DROP TABLE IF EXISTS LOG")
table = """CREATE TABLE LOG (
            Event_ID INT,
            Time VARCHAR(20),
            Camera_ID INT
        );"""
cursor.execute(table)

root.mainloop()