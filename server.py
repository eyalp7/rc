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

# Server configuration settings.
IP = "10.0.0.4"
KEYBOARD_PORT = 12345
SCREENSHOTS_PORT = 54321
MOUSE_PORT = 12346
PASSWORD = "password123"

special_keys = ['ctrl', 'right ctrl', 'alt', 'right alt', 'shift', 'right shift']  # Special keys that are usually pressed with another key.
last_key = "_"  # The last key that the client pressed.

def authentication(client_socket):
    """Gets the password from the client."""
    client_socket.send("Enter the password: ".encode('utf-8'))
    while True:
        given_password = client_socket.recv(1024).decode('utf-8')
        if(given_password == PASSWORD):
            client_socket.send("SUCCESS".encode('utf-8'))
            break
        client_socket.send("Invalid password. ".encode('utf-8'))

def mouse_click(event):
    """Clicks the mouse at the client's mouse location."""
    if event['button'] == 'Button.left':
        mouse.click('left')
    elif event['button'] == 'Button.right':
        mouse.click('right')
    elif event['button'] == 'Button.middle':
        mouse.click('middle')

def mouse_movement(event):
    """Moves the mouse to the client's mouse location."""
    pyautogui.moveTo(event['x'], event['y'], 0.01)

def mouse_scroll(event):
    """Scrolls the mouse."""
    pyautogui.scroll(event['dy'])

def keyboard_press(event):
    """Presses the key that the client pressed."""
    global last_key
    key = event["key"]
    if last_key in special_keys:  # In case that the last character is a special character.
        key = last_key + "+" + key  # Presses both of the keys at the same time.
    keyboard.press_and_release(key)
    last_key = key

def handle_presses(client_socket):
    """Handles presses received from the client."""
    while True:
        message = client_socket.recv(1024).decode('utf-8')
        event = json.loads(message)  # Deserialization

        action = event['action']
        if action == "mouse_click":
            mouse_click(event)
        elif action == "keyboard_press":
            keyboard_press(event)
        elif action == "mouse_scroll":
            mouse_scroll(event)

def handle_screenshots(client_socket):
    """Takes screenshots and sends them to the client."""
    w, h = pyautogui.size()

    with mss.mss() as sct:
        monitor = {"top": 0, "left": 0, "width": w, "height": h}
        while True:
            img = sct.grab(monitor)
            numpy_img = np.array(img)  # Converting to a numpy array for better processing.

            cursor_x, cursor_y = pyautogui.position()

            # Draw a white dot at the cursor's position
            radius = 5
            color = (255, 255, 255)  # White color in BGR
            thickness = -1  # Solid circle
            numpy_img = cv2.circle(numpy_img, (cursor_x, cursor_y), radius, color, thickness)

            _, encoded_img = cv2.imencode('.jpg', numpy_img)
            data = encoded_img.tobytes()  # Converting the image to bytes.

            client_socket.sendall(struct.pack("L", len(data)) + data)  # Sends the length of the screenshot first as an unsigned long.

            if keyboard.is_pressed('f8'):
                break

def handle_mouse_movements(mouse_socket):
    """Handles the mouse movements of the client."""
    while True:
        message, _ = mouse_socket.recvfrom(1024)
        mouse_movement(json.loads(message.decode('utf-8')))

def start_main_server():
    """Starts the server that handles keyboard and mouse events + authentication."""
    print(f"Starting events server on: {IP}:{KEYBOARD_PORT}...")
    main_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    main_socket.bind((IP, KEYBOARD_PORT))

    main_socket.listen(1)
    client_socket, address = main_socket.accept()
    print(f"Connection established from: {address}")

    authentication(client_socket)

    clicks_thread = threading.Thread(target=handle_presses, args=(client_socket,))
    screenshots_thread = threading.Thread(target=start_screenshots_server)
    movements_thread = threading.Thread(target=start_mouse_server)

    clicks_thread.start()
    screenshots_thread.start()
    movements_thread.start()

    clicks_thread.join()
    screenshots_thread.join()
    movements_thread.join()

def start_screenshots_server():
    """Starts the socket that handles the screenshots taking and sending."""
    print(f"Starting screenshots server on: {IP}:{SCREENSHOTS_PORT}...")
    screenshots_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    screenshots_server.bind((IP, SCREENSHOTS_PORT))
    
    screenshots_server.listen(1)
    client_socket, address = screenshots_server.accept()
    print(f"Connection established from: {address}")

    handle_screenshots(client_socket)

def start_mouse_server():
    """Starts the UDP socket that listens for mouse movements."""
    mouse_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    mouse_socket.bind((IP, MOUSE_PORT))
    print(f"Starting movements server on: {IP}:{MOUSE_PORT}...")

    handle_mouse_movements(mouse_socket)

def main():
    start_main_server()

if __name__ == '__main__':
    main()
