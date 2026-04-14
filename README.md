# Remote Desktop Project

This is a simple client-server application that allows one computer to view the screen of another computer in real-time using Python.

## How It Works
* **Connection:** The server and client connect to each other using TCP sockets on port 9999.
* **Security:** A password is required to connect. The system uses SHA-256 hashing to check the password securely.
* **Streaming:** The server takes screenshots, compresses them as JPEGs to keep the data small, and sends them to the client.
* **Display:** The client receives the data and uses OpenCV to show the live video stream.

## Requirements
You need to install these libraries before running the code:
```bash
pip install pyautogui opencv-python pillow
