import pynput
import threading
import socket
import json
import time
import pyautogui
import numpy as np
import cv2
import struct
import keyboard

# Server configuration settings
IP = "10.0.0.7"
CLICKS_PORT = 12345
SCREENSHOTS_PORT = 54321
MOUSE_PORT = 12346

print(f"Connecting to the events socket in {IP}:{CLICKS_PORT}... ")
clicks_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # The socket must be a global variable for use in different functions.
clicks_socket.connect((IP, CLICKS_PORT))

def authentication(client_socket):
    """Logs into the server with the password."""
    message = client_socket.recv(1024).decode('utf-8')
    print(message)

    while(message != "SUCCESS"):
        # Loop until the server sends SUCCESS (meaning password was correct)
        password = input("Enter password: ")
        client_socket.send(password.encode('utf-8'))
        message = client_socket.recv(1024).decode('utf-8')
        print(message)

def new_key(event):
    """ Sends keyboard presses to the server."""
    button = event.name
    message = json.dumps({"action": "keyboard_press", "key": button}).encode()
    clicks_socket.send(message)

def on_click(x, y, button, pressed):
    """ Sends a mouse click to the server."""
    if pressed:
        message = json.dumps({"action": "mouse_click", "x": x, "y": y, "button": str(button)}).encode()  # Serialization
        clicks_socket.send(message)

def on_scroll(x, y, dx, dy):
    """ Sends a mouse scroll to the server."""
    message = json.dumps({"action": "mouse_scroll", "x": x, "y": y, "dx": dx, "dy": dy}).encode()  # Serialization
    clicks_socket.send(message)

def handle_keyboard():
    """Listens for keyboard presses."""
    keyboard.on_release(callback=new_key)
    keyboard.wait()

def handle_mouse():
    """Tracks mouse events and handles them."""
    with pynput.mouse.Listener(on_click=on_click, on_scroll=on_scroll) as listener:
        listener.join()  # Starts tracking mouse events.

def handle_mouse_movements():
    """Sends the current mouse location to the server."""
    mouse_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    address = (IP, MOUSE_PORT)
    while True:
        x, y = pyautogui.position()
        message = json.dumps({"action": "mouse_movement", "x": x, "y": y}).encode()  # Serialization
        mouse_socket.sendto(message, address)
        time.sleep(0.05)

def handle_screenshots(screenshots_socket):
    """Receives screenshots from the server and displays them."""
    while True:
        data_length = screenshots_socket.recv(4)  # The first 4 bytes indicate the image size.
        if not data_length:
            break
        data_length = struct.unpack("L", data_length)[0]  # Unpacks the first 4 bytes into an integer.

        data = b''
        while len(data) < data_length:
            # The loop receives packets until the entire image is received.
            packet = screenshots_socket.recv(data_length - len(data))
            if not packet:
                break
            data += packet
        
        numpy_img = np.frombuffer(data, dtype=np.uint8)  # Convert the bytes to a numpy array.
        img = cv2.imdecode(numpy_img, cv2.IMREAD_COLOR)  # Convert the numpy array back to an image.

        if img is not None:
            cv2.imshow("Server's view: ", img)

        if cv2.waitKey(1) == 2490368:  # The keycode for 'f8'.
            break

def connect_to_screenshots_server():
    """Connects to the screenshots socket."""
    print(f"Connecting to the screenshots server in {IP}:{SCREENSHOTS_PORT}")
    screenshots_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    screenshots_socket.connect((IP, SCREENSHOTS_PORT))
    print("Connected.")

    handle_screenshots(screenshots_socket)

def main():
    """The main function that calls all of the needed functions."""
    authentication(clicks_socket)
    
    # Start threads for handling various tasks
    screenshots_thread = threading.Thread(target=connect_to_screenshots_server)
    mouse_thread = threading.Thread(target=handle_mouse)
    keyboard_thread = threading.Thread(target=handle_keyboard)
    movement_thread = threading.Thread(target=handle_mouse_movements)

    screenshots_thread.start()
    mouse_thread.start()
    keyboard_thread.start()
    movement_thread.start()

    # Wait for all threads to finish
    screenshots_thread.join()
    mouse_thread.join()
    keyboard_thread.join()
    movement_thread.join()

if __name__ == '__main__':
    main()
