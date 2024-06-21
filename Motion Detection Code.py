# Imports

import numpy as np
import cv2 as cv
import time
import tkinter as tk
import threading
import sqlite3
import os

# Forgot what this thing does 
kernel = np.ones((3, 3), dtype=np.uint8)
cap = cv.VideoCapture(0) # Opens camera 1

# Error handling

if not cap.isOpened():
    print("Cant open Camera, simply a Skill Issue") # VERY UNPROFRESSIONAL
    exit()

ret, frame_last = cap.read() # Checks if a frame is received
if not ret:
    print("Cant receive frame (Maybe you should have done your helper tasks!)")
    exit() # Still haven't started derby lol

count = 0 
gray_last = cv.cvtColor(frame_last, cv.COLOR_BGR2GRAY)
frame_width = int(cap.get(cv.CAP_PROP_FRAME_WIDTH)) # why
frame_height = int(cap.get(cv.CAP_PROP_FRAME_HEIGHT)) # why
event_flag = False # Catches an event for something to happen
fourcc = cv.VideoWriter_fourcc(*'MJPG') # Codec coding

# SQL yap

connection = sqlite3.connect("motion_events.db")
cursor = connection.cursor()
cursor.execute("DROP TABLE IF EXISTS LOG")
table = """CREATE TABLE LOG (
            Event_ID INTEGER PRIMARY KEY,
            Time TEXT,
            Camera_ID INTEGER
        );"""
cursor.execute(table)

# More things to learn
out = None
armed = False
max_videos = 5
video_files = []

# Here is where the GUI begins, I tried to use the after() method rather than Threading since I couldn't get the latter to work
root = tk.Tk()
root.title("Motion Detection System Wowsers") # Wow

# These are all of the GUI containers where you can then pack buttons and whatnot into
left_container = tk.Frame(root) # Whats a container :()
left_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
right_container = tk.Frame(root)
right_container.pack(side=tk.RIGHT, fill=tk.Y)

# These are the frames for where the Videos will play in the GUI, notice they go into the containers made above
live_feed_frame = tk.Label(left_container) # Ok
live_feed_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
video_clip_frame = tk.Label(left_container)
video_clip_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

# There is a function for arming and disarming since if you want to make a button do something in Tkinter, it  needs you to assign a function as an event in it
# The variables are global since they need to be accessible outside the function (this took me ages to realise somehow)
def arm_system():
    global armed
    armed = True
    start_video_recording() 

def disarm_system():
    global armed, out
    armed = False
    if out != None:
        out.release()
        out = None

def start_video_recording():
    if armed:
        create_new_video()
        threading.Timer(30, start_video_recording).start() 
# What this is aiming to do is start recording a new video every 30 seconds from when you click the Arm Button        

def create_new_video():
    global count, out, video_files
    if out != None:
        out.release()
    
    # Rather than using the 640, 480 that was in the example sir gave, I replaced it with width and height since it for some reason wouldn't fit on my screen otherwise
    vidname = "video"+str(count)+".avi" # That makes sense thanks
    out = cv.VideoWriter(vidname, fourcc, 30, (frame_width, frame_height))
    if not out.isOpened():
        print("The video output does not work sorry") # its not ok
        out = None
# This is cool, its adding the names of the videos in a list, then it deletes the older videos when there are more than 5 videos
# Rather than using the number 5 I used max videos as a variable so then you could change it if you wanted to (Also it didn't actually work when I used a number like 5, not sure why)
    else: # should use an entry box instead icl
        count += 1
        video_files.append(vidname)
        if len(video_files) > max_videos:
            os.remove(video_files.pop(0)) # poop
# One note is that os is a library that lets you do things with your actual files (as long as they are in the same folder as the code of course)
        update_video_list()

# This lets you select a video file and play it in the Gooey (as Mr Evans would say), displaying each frame in a label 
def play_video():
    video_path = video_entry.get()
    if video_path: # checks if get() which is from tk
        cap_video = cv.VideoCapture(video_path)
        while cap_video.isOpened():
            ret, frame = cap_video.read()
            if not ret:
                break
# Here there is a super hit function used called cv_to_tk that is defined below, it is game changing
            frame_rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
            frame_processed = cv.cvtColor(frame_rgb, cv.COLOR_RGB2BGR)
            imgtk = cv_to_tk(frame_processed) # seems mysterious
            video_clip_frame.imgtk = imgtk
            video_clip_frame.config(image=imgtk)
            video_clip_frame.update()
# You need there to be some delay between each frame being processed otherwise you would be able to fry an egg on your laptop
            time.sleep(0.001)
        cap_video.release()

# Honestly I just found this somewhere and went kapoosh to add it in here, never knew you could convert from OpenCV to TK
def cv_to_tk(frame): # ok
    return tk.PhotoImage(data=cv.imencode('.ppm', frame)[1].tobytes())

# This gets the list of video files and then adds them to the box on the GUI
def update_video_list():
    video_listbox.delete(0, tk.END)
    for filename in video_files:
        video_listbox.insert(tk.END, filename)

# I'm not sure why it can't access the event, though the code still works so I'm not complaining
def on_video_select(event):
    selected_video = video_listbox.get(video_listbox.curselection())
    video_entry.delete(0, tk.END)
    video_entry.insert(0, selected_video)

# This is just boring button defining 
arm_button = tk.Button(right_container, text="Arm", command=arm_system)
arm_button.pack(padx=5, pady=5, fill=tk.X)

disarm_button = tk.Button(right_container, text="Disarm", command=disarm_system)
disarm_button.pack(padx=5, pady=5, fill=tk.X)

video_entry = tk.Entry(right_container, width=50)
video_entry.pack(padx=5, pady=5, fill=tk.X)

play_video_button = tk.Button(right_container, text="Play Video", command=play_video)
play_video_button.pack(padx=5, pady=5, fill=tk.X)

# This is very nice, it lets you create a box that contains a list, the W3Schools was very good for learning this
video_listbox = tk.Listbox(right_container)
video_listbox.pack(padx=5, pady=5, fill=tk.Y)
video_listbox.bind('<<ListboxSelect>>', on_video_select)
update_video_list()

# 
def update_feed():
    global frame_last, gray_last, event_flag, out, armed

    ret, frame = cap.read()
    if not ret:
        root.after(10, update_feed)
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

# This is just when the time of the video being taken is put into the Database, to be fair I didn't end up being able to output these times in the GUI, I would try now, but I would rather play games haha
# can u make ur comments multiple lines please
# im just joking but it is quite nice if you do that
# idek if u can see this mwahaha

    if len(contours) > 0 and armed and not event_flag:
        event_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        cursor.execute("INSERT INTO LOG (Time, Camera_ID) VALUES (?, ?)", (event_time, 1))
        connection.commit()
        event_flag = True
    if event_flag and armed and out is not None:
        out.write(frame)
 
    frame_rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
    frame_processed = cv.cvtColor(frame_rgb, cv.COLOR_RGB2BGR)
    imgtk = cv_to_tk(frame_processed)
    live_feed_frame.imgtk = imgtk
    live_feed_frame.config(image=imgtk)
   
    # The outputs below were only shown before so we could see the processing but we don't need it anymore
    # cv.imshow('frame', frame)
    # cv.imshow('gray', gray)
    # cv.imshow('gray_diff', gray_diff)
    # cv.imshow('mask', mask)

# Making use of the after() method since Threading was too confusing for me here
    root.after(10, update_feed)

update_feed()
root.mainloop()

cap.release()
if out is not None:
    out.release()
cv.destroyAllWindows() # lets all stand together against destroying windows, we should just give them a rest break
connection.close()
