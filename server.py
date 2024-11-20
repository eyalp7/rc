import socket
import keyboard
import mouse
import pyautogui
import threading
import json
import mss
import numpy as np
import struct
import cv2

#Server configuration settings. 
IP = "10.0.0.6"
CLICKS_PORT = 12345
SCREENSHOTS_PORT = 54321
MOVEMENTS_PORT = 8080
PASSWORD = "pass123"

special_keys = ['ctrl', 'right ctrl', 'alt', 'right alt', 'shift', 'right shift'] #These keys are usually paired with another one.
last_key = "_" #Stores the last key that was pressed.

def authentication(client_socket):
    """Gets the correct password from the user. """
    client_socket.send("Enter the password: ".encode('utf-8')) 
    response = client_socket.recv(1024).decode('utf-8')

    while response != PASSWORD:
        #Runs until the password is correct.
        client_socket.send("Wrong password.".encode('utf-8'))
        response = client_socket.recv(1024).decode('utf-8')

    client_socket.send("SUCCESS".encode('utf-8'))

def handle_screenshots(client_socket):
    """Takes screenshots and sends them to the client. """
    w, h = pyautogui.size()

    with mss.mss() as sct:
        monitor = {"top": 0, "left": 0, "width": w, "height": h}
        #An infinite loop that continually captures screenshots and sends them to the user.
        while True:
            img = sct.grab(monitor)
            img = np.array(img) #Converting to a numpy array for better processing.

            cursor_x, cursor_y = pyautogui.position()

            radius = 5
            color = (255, 255, 255)
            thickness = -1
            img = cv2.circle(img, (cursor_x, cursor_y), radius, color, thickness)

            _, encoded_img = cv2.imencode('.jpg', img)
            data = encoded_img.tobytes() #Converting the image to bytes.

            client_socket.sendall(struct.pack("L", len(data)) + data) #Sends the length of the screenshot first as an unsigned long.

            if cv2.waitKey(1) == 2490368: #The key code for 'F8'.
                break

def key_presses(event):
    """Presses the key that the user pressed. """
    global last_key
    key = event["key"]
    if last_key in special_keys: #In case that the last key is a special key.
        keyboard.press_and_release(last_key + "+" + key) #Holding both of the keys together.
    else:
        keyboard.press_and_release(key)
    last_key = key

def mouse_click(event):
    """Clicks the same button that the user clicked. """
    if event['button'] == 'Button.left':
        mouse.click('left')
    elif event['button'] == 'Button.right':
        mouse.click('right')
    elif event['button'] == 'Button.middle':
        mouse.click('middle')

def mouse_scroll(event):
    """Scrolls the mouse. """
    pyautogui.scroll(event['dy'])

def handle_clicks(client_socket):
    """Receives an event from the client and handles it. """
    while True:

        event = json.loads(client_socket.recv(1024).decode('utf-8'))
        action = event['action']

        if action == "key_press":
            key_presses(event)
        elif action == "mouse_click":
            mouse_click(event)
        elif action == "mouse_scroll":
            mouse_scroll(event)

def start_clicks_socket():
    """Starts the clicks socket that is also used for the authentication. """
    print(f"Starting clicks socket on {IP}:{CLICKS_PORT}...")
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((IP, CLICKS_PORT))
    server_socket.listen(1)

    client_socket, address = server_socket.accept()
    print(f"Connection established from {address}")
    return client_socket

def start_movements_socket():
    """Starts the movements socket. """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #A udp socket.
    server_socket.bind((IP, MOVEMENTS_PORT))

    while True:
        #A loop that receives the current mouse position of the user and moves it accordingly.
        event = server_socket.recvfrom(1024)[0]
        event = json.loads(event.decode('utf-8'))
        pyautogui.moveTo(event['x'], event['y'])

def start_screenshots_server():
    """Starts the server that handles the screenshots taking and sending. """
    print(f"Starting screenshots server on: {IP}:{SCREENSHOTS_PORT}")
    screenshots_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    screenshots_server.bind((IP, SCREENSHOTS_PORT))

    screenshots_server.listen(1) 
    client_socket, address = screenshots_server.accept()
    print(f"Connection established from: {address}")

    handle_screenshots(client_socket)

def main():
    """The main function. """
    client_socket = start_clicks_socket()

    authentication(client_socket)

    screenshots_thread = threading.Thread(target=start_screenshots_server).start()
    clicks_thread = threading.Thread(target=handle_clicks, args=(client_socket,)).start()
    movements_thread = threading.Thread(target=start_movements_socket).start()

if __name__ == "__main__":
    main()