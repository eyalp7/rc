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

#Server configuration settings
IP = "127.0.0.1"
EVENTS_PORT = 12345
SCREENSHOTS_PORT = 54321

print(f"Connecting to the events socket in {IP}:{EVENTS_PORT}... ")
events_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #The socket has to be a global variable so it can be used in the different functions.
events_socket.connect((IP, EVENTS_PORT))

def new_key(event):
    """ Sends keyboard presses to the server."""
    button = event.name
    message = json.dumps({"action": "keyboard_press", "key": button}).encode()
    events_socket.send(message)

def on_move(x, y):
    """ Sends mouse movement information to the server."""
    message =json.dumps({"action": "mouse_movement", "x": x, "y": y}).encode() #Serialization
    events_socket.send(message)
    time.sleep(0.05)

def on_click(x, y, button, pressed):
    """ Sends a mouse click to the server."""
    if pressed:
        message = json.dumps({"action": "mouse_click", "x": x, "y": y, "button": str(button)}).encode() #Serialization
        events_socket.send(message)
        time.sleep(0.05)

def on_scroll(x, y, dx, dy):
    """ Sends a mouse scroll to the server."""
    message = json.dumps({"action": "mouse_scroll", "x": x, "y": y, "dx": dx, "dy": dy}).encode() #Serialization
    events_socket.send(message)
    time.sleep(0.05)

def handle_keyboard():
    """Listens for keyboard presses. """
    keyboard.on_release(callback=new_key)
    keyboard.wait()

def handle_mouse():
    """Tracks mouse events and handles them"""
    with pynput.mouse.Listener(on_click=on_click, on_scroll=on_scroll) as listener:
        listener.join() #Starts tracking mouse events.

def handle_mouse_movements():
    """Sends 4 times every second information about the mouse movement"""
    while True:
        x, y = pyautogui.position()
        message =json.dumps({"action": "mouse_movement", "x": x, "y": y}).encode() #Serialization
        events_socket.send(message)
        time.sleep(0.25)

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
        
        
        numpy_img = np.frombuffer(data, dtype=np.uint8) #Convert the bytes to a numpy array.
        img = cv2.imdecode(numpy_img, cv2.IMREAD_COLOR) #Convert the numpy array back to an image.

        cv2.imshow("Server's view: ", img)

        if cv2.waitKey(1) == ord('q') and keyboard.is_pressed('ctrl'):
            break

def connect_to_screenshots_server():
    """Connects to the screenshots relating socket. """
    print(f"Connecting to the screenshots server in {IP}:{SCREENSHOTS_PORT}")
    screenshots_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    screenshots_socket.connect((IP, SCREENSHOTS_PORT))

    screenshots_thread = threading.Thread(target=handle_screenshots, args=(screenshots_socket,)).start()



def main():
    """The main function that calls all of the needes function. """
    threading.Thread(target=connect_to_screenshots_server).start()
    mouse_thread = threading.Thread(target=handle_mouse).start()
    keyboard_thread = threading.Thread(target=handle_keyboard).start()
    movement_thread = threading.Thread(target=handle_mouse_movements).start()

if __name__ == '__main__':
    main()