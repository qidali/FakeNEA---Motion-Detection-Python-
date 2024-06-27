import numpy as np
import cv2 as cv
import time
import tkinter as tk
from tkinter import ttk
import threading
import sqlite3


kernel = np.ones((3,3), dtype=np.uint8)
cap = cv.VideoCapture(0)
if not cap.isOpened():
    print("Can't open Camera, simply a skill issue")
    exit()

ret, frame_last = cap.read()
gray_last = cv.cvtColor(frame_last, cv.COLOR_BGR2GRAY)

count = 0
event_flag = False
fourcc = cv.VideoWriter_fourcc(*'MJPG')
on = False
videos = []
anyOutputs = None

''' Le GUI '''

root = tk.Tk()
root.title("chair stealer")


connection = sqlite3.connect("motion_events.db")
cursor = connection.cursor()
cursor.execute("DROP TABLE IF EXISTS LOG")
table = """CREATE TABLE LOG (
            Event_ID INT,
            Time VARCHAR(20),
            Camera_ID INT
        );"""
cursor.execute(table)


while True:
    ret, frame = cap.read()
    if not ret:
        print('can\'t receive frame (maybe you should have done your helper tasks!)')
        break

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


    if cv.waitKey(1) == ord('q'):
         break
    cv.imshow('frame', frame)
    cv.imshow('gray', gray)
    cv.imshow('gray_diff', gray_diff)
    cv.imshow('mask', mask)

    vidname = "video"+str(count)+".avi"
    fourcc = cv.VideoWriter_fourcc(*'MJPG')
    out = cv.VideoWriter(vidname, fourcc, 30,(640,480))
    count+=1
    event_flag=True



