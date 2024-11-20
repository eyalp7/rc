import socket
import json
import pyautogui
import time
import keyboard
import pynput
import threading
import struct
import cv2
import numpy as np

#Server configuration settings.
IP = "10.0.0.6"
CLICKS_PORT = 12345
SCREENSHOTS_PORT = 54321
MOVEMENTS_PORT = 8080

print(f"Connecting to clicks socket on {IP}:{CLICKS_PORT}")
clicks_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #The clicks socket has to be a global variable. 
clicks_socket.connect((IP, CLICKS_PORT))

#The authentication process.
message = clicks_socket.recv(1024).decode('utf-8')
while message != "SUCCESS":
    #A loop that runs until the password is correct.
    print(message)
    password = input()
    clicks_socket.send(password.encode('utf-8'))
    message = clicks_socket.recv(1024).decode('utf-8')

def new_key(event):
    """Handles a key press."""
    message = json.dumps({"action": "key_press", "key": event.name}).encode('utf-8')
    clicks_socket.send(message)

def on_click(x, y, button, pressed):
    """Handles a mouse click. """
    if pressed:
        message = json.dumps({"action": "mouse_click", "button": str(button)}).encode('utf-8')
        clicks_socket.send(message)

def on_scroll(x, y, dx, dy):
    """Handles a mouse scroll. """
    message = json.dumps({"action": "mouse_scroll", "dy": dy}).encode('utf-8')
    clicks_socket.send(message)

def send_movements():
    "Handles mouse movements. "
    movements_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #A udp socket.

    while True:
        #A loop that sends the current mouse position.
        x, y = pyautogui.position()
        message = json.dumps({"action": "mouse_movement", "x": x, "y": y}).encode('utf-8')
        movements_socket.sendto(message, (IP, MOVEMENTS_PORT))
        time.sleep(0.1)


def handle_keypresses():
    """Listens for key presses. """
    keyboard.on_release(callback=new_key)
    keyboard.wait()

def handle_mouse():
    """Tracks mouse events and handles them"""
    with pynput.mouse.Listener(on_click=on_click, on_scroll=on_scroll) as listener:
        listener.join()

def handle_screenshots(screenshots_socket):
    """Receives screenshots from the server and displays them. """
    while True:
        data_length = screenshots_socket.recv(4) #The first 4 bytes indicate the image size.
        if not data_length:
            break
        data_length = struct.unpack("L", data_length)[0] #Unpacks the first 4 bytes into an integer.
        data = b''
        while len(data) < data_length:
            #The loop receives packets untill the entire image is received.
            packet = screenshots_socket.recv(data_length - len(data))
            if not packet:
                break
            data += packet

        img = np.frombuffer(data, dtype=np.uint8) #Convert the bytes to a numpy array.
        img = cv2.imdecode(img, cv2.IMREAD_COLOR) #Convert the numpy array back to an image.
        cv2.imshow("Server's view: ", img)

        if cv2.waitKey(1) == ord('q'):
            break


def connect_to_screenshots_server():
    """Connects to the screenshots relating socket. """
    print(f"Connecting to the screenshots server in {IP}:{SCREENSHOTS_PORT}")
    screenshots_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    screenshots_socket.connect((IP, SCREENSHOTS_PORT))

    handle_screenshots(screenshots_socket)

#Creating a thread for each neccessary function. 
screenshots_thread = threading.Thread(target=connect_to_screenshots_server).start()
keyboard_thread = threading.Thread(target=handle_keypresses).start()
mouse_thread = threading.Thread(target=handle_mouse).start()
movements_thread = threading.Thread(target=send_movements).start()