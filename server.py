import socket
import json
import mouse
import pyautogui
import keyboard
import mss
import numpy as np
import cv2
import struct
import threading

#Server configuration settings.
IP = "10.0.0.7"
EVENTS_PORT = 12345
SCREENSHOTS_PORT = 54321
special_keys = ['ctrl', 'right ctrl', 'alt', 'right alt', 'shift', 'right shift'] #Special keys that are usually pressed with another key.
last_key = "_" #The last key that the client pressed.


def mouse_click(event):
    """Clicks the mouse at the client's mouse location. """
    pyautogui.moveTo(event['x'], event['y'], 0.1)
    if(event['button'] == 'Button.left'):
        mouse.click('left')
    elif(event['button'] == 'Button.right'):
        mouse.click('right')
    elif(event['button'] == 'Button.middle'):
        mouse_click('middle')

def mouse_movement(event):
    """Moves the mouse to the client's mouse location. """
    pyautogui.moveTo(event['x'], event['y'], 0.1)

def mouse_scroll(event):
    """Scrolls the mouse."""
    pyautogui.scroll(event['dy'])

def keyboard_press(event):
    """Presses the key that the client pressed. """
    global last_key
    key = event["key"]
    if(last_key in special_keys): #In case that the last character is a special character.
        key = last_key + "+" + key #Presses both of the keys at the same time.
    keyboard.press_and_release(key)
    last_key = key

def handle_events(client_socket):
    """Handles events received from the client."""
    while True:
        message = client_socket.recv(1024).decode('utf-8')
        event = json.loads(message) #Deserialization

        action = event['action']
        if(action == "mouse_click"):
            mouse_click(event)
        elif(action == "keyboard_press"): 
            keyboard_press(event)
        elif(action == "mouse_movement"):
            mouse_movement(event)
        elif(action == "mouse_scroll"):
            mouse_scroll(event)
        print(event)

def handle_screenshots(client_socket):
    """Takes screenshots and sends them to the client. """
    w, h = pyautogui.size()

    with mss.mss() as sct:
        monitor = {"top": 0, "left": 0, "width": w, "height": h}
        #An infinite loop that continually captures screenshots and sends them to the client.
        while True:
            img = sct.grab(monitor)
            numpy_img = np.array(img) #Converting to a numpy array for better processing.

            cursor_x, cursor_y = pyautogui.position()

            radius = 5
            color = (255, 255, 255)
            thickness = -1
            numpy_img = cv2.circle(numpy_img, (cursor_x, cursor_y), radius, color, thickness)

            _, encoded_img = cv2.imencode('.jpg', numpy_img)
            data = encoded_img.tobytes() #Converting the image to bytes.

            client_socket.sendall(struct.pack("L", len(data)) + data) #Sends the length of the screenshot first as an unsigned long.

            if cv2.waitKey(1) == ord('q'):
                break

def start_events_server():
    """Starts the server that handles keyboard and mouse events. """
    print(f"Starting events server on: {IP}:{EVENTS_PORT}...")
    event_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    event_socket.bind((IP, EVENTS_PORT))

    event_socket.listen(1)
    client_socket, address = event_socket.accept()
    print(f"Connection established from: {address}")

    handle_events(client_socket)

def start_screenshots_server():
    """Starts the server that handles the screenshots taking and sending. """
    print(f"Starting screenshots server on: {IP}:{SCREENSHOTS_PORT}")
    screenshots_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    screenshots_server.bind((IP, SCREENSHOTS_PORT))

    screenshots_server.listen(1)
    client_socket, address = screenshots_server.accept()
    print(f"Connection established from: {address}")

    handle_screenshots(client_socket)

if __name__ == '__main__':
    events_thread = threading.Thread(target=start_events_server).start()
    screenshots_thread = threading.Thread(target=start_screenshots_server).start()