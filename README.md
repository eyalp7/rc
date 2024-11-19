# Remote Desktop Control

This project is a **Remote Desktop Control System** that allows users to control a remote system in real time. The project includes:
- **Remote Keyboard and Mouse Input Control**: Sends keyboard and mouse events to a server to control the remote machine.
- **Live Screen Streaming**: Streams the screen of the remote machine to the client in real time.

---

## Features

- **Keyboard Control**: Send keyboard input to the remote system.
- **Mouse Control**:
  - Move the mouse pointer.
  - Perform left, right, or middle clicks.
  - Scroll the mouse wheel.
- **Screen Streaming**: View the remote system's screen in real time.
- **Multithreaded Servers**: Separate servers handle screen streaming and input events.
- **Low Latency**: Optimized for efficient data transfer.
- **Cross-Platform**: Compatible with most operating systems running Python.

---

## Requirements

- **Python 3.8+**
- Required Libraries:
  - `socket`
  - `json`
  - `pyautogui`
  - `keyboard`
  - `mouse`
  - `pynput`
  - `mss`
  - `numpy`
  - `cv2`
  - `struct`
  - `threading`

You can install the dependencies using:
```bash
pip install pyautogui keyboard mouse pynput mss numpy opencv-python
```

## Setup

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/remote-desktop-control.git
cd remote-desktop-control
```

### 2. Configure the Server and Client
Update the IP and ports in both the server and client scripts as needed:
- `IP`: The IP address of the machine hosting the server.
- `EVENTS_PORT`: The port for handling keyboard and mouse input events (default: `12345`).
- `SCREENSHOTS_PORT`: The port for handling screen streaming (default: `54321`).

## Usage

### 1. Start the Server
Run the server script on the machine to be controlled remotely:
```bash
python server.py
```
This will start:
- **Events server**: Handles keyboard and mouse input.
- **Screenshots server**: : Streams the screen to the client.

### 2. Run the Client
Run the client script on the controlling machine:

```bash
python client.py
```
The client will:
- Stream the remote screen.
- Allow sending keyboard and mouse inputs.

## File Flow

### 1. Server Side:
- The server listens for incoming client connections on the specified ports (`EVENTS_PORT` and `SCREENSHOTS_PORT`).
- When a connection is established, the server handles two main tasks:
  1. **Event Handling**: Receives and processes keyboard, mouse movements, clicks, and scrolls.
  2. **Screenshot Handling**: Continuously captures the screen and sends it to the client.

### 2. Client Side:
- The client connects to the server's event and screenshot streams.
- **Event Handling**: The client sends mouse and keyboard events to the server, simulating user input on the server side.
- **Screenshot Handling**: The client receives screenshots from the server and displays them in real-time.

### Example Interaction

```python
if cv2.waitKey(1) & 0xFF == ord('q') and keyboard.is_pressed('ctrl'):
    # This checks if 'ctrl' and 'q' are pressed at the same time.
    print("Ctrl + Q is pressed!")
```

## Example Interaction

### Keyboard Input Example:
- **Client presses c.**
- **Event sent as:**
  
```json
{
  "action": "keyboard_press",
  "key": "c"
}
```
**Server simulates the same key press.**

### Mouse Movement Example:
- **Client moves the mouse to position (200, 300).**
- **Event sent as:**
  
```json
{
  "action": "mouse_movement",
  "x": 200,
  "y": 300
}
```
**Server moves the mouse pointer to the specified position.**

### Notes:
- Ensure both the server and client scripts run on machines with Python 3.8+.
- Press `ctrl + q` in the client's screen stream window to quit the stream.
- This project is still in progress. I plan to improve the performane, and adding authorization.
- **Do not run this both of the python scripts on the same machine, it won't work as planned.**
