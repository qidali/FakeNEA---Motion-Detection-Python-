import numpy as np
import cv2 as cv
import time
import PySimpleGUI as sg
import threading
import sqlite3

kernel = np.ones((3,3), dtype=np.uint8)
cap = cv.VideoCapture(0)
if not cap.isOpened():
    sg.popup_error("walking skill issue icl")
    exit()

ret, frame_last = cap.read()
if ret:
    gray_last = cv.cvtColor(frame_last, cv.COLOR_BGR2GRAY)
else:
    sg.popup_error("walking skill issue")
    cap.release()
    exit()

count = 0
event = None
fourcc = cv.VideoWriter_fourcc(*'MJPG')
on = False
videos = []
anyOutputs = None

sg.theme('DarkBlue5')
layout = [
    [sg.Button('Start', key='Start')],
    [sg.Button('Stop', key='Stop')],
    [sg.Image(filename="", key="image")],
    ]


window = sg.Window('chair stealer', layout,size=(1000,800))



connection = sqlite3.connect("motion_events.db")
cursor = connection.cursor()
cursor.execute("DROP TABLE IF EXISTS LOG")
table = """CREATE TABLE LOG (
            Event_ID INT,
            Time VARCHAR(20),
            Camera_ID INT
        );"""
cursor.execute(table)

capturing = False

while True:
    event, values = window.read(timeout=20)
    if event == sg.WIN_CLOSED:
        break
    elif event == 'Start':
        capturing = True
    elif event == 'Stop':
        capturing = False
    if capturing:
        ret, frame = cap.read()
        if ret:
            imgbytes = convert_frame_to_display(frame)
            window['image'].update(data=imgbytes)
            gray_last = cv.cvtColor(frame_last, cv.COLOR_BGR2GRAY)
            gray=cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
            gray_diff=cv.subtract(gray,gray_last)
            gray_diff = cv.medianBlur(gray_diff, 5)
            mask = cv.adaptiveThreshold(gray_diff, 255, cv.ADAPTIVE_THRESH_GAUSSIAN_C, cv.THRESH_BINARY_INV, 9, 3)
            mask = cv.medianBlur(mask, 3)
            mask = cv.morphologyEx(mask, cv.MORPH_CLOSE, kernel, iterations=1)

            contours,_ = cv.findContours(mask, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
            frame_last=frame
            gray_last=gray
            cv.drawContours(frame, contours, -1, (0,255,0), 3)

        else:
            sg.popup_error("walking skill issue")
            break

    if cv.waitKey(1) == ord('q'):
         break

    vidname = "video"+str(count)+".avi"
    fourcc = cv.VideoWriter_fourcc(*'MJPG')
    out = cv.VideoWriter(vidname, fourcc, 30,(640,480))
    count+=1
    event_flag=True

cap.release()
cv.destroyAllWindows() # violence




