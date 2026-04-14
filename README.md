Remote Desktop Project
This is a simple client-server application that allows one computer to view the screen of another computer in real-time using Python.

How It Works
Connection: The server and client connect to each other using TCP sockets on port 9999.
Security: A password is required to connect. The system uses SHA-256 hashing to check the password securely.
Streaming: The server takes screenshots, compresses them as JPEGs to keep the data small, and sends them to the client.
Display: The client receives the data and uses OpenCV to show the live video stream.

Requirements
Install these libraries before running the code:
pip install pyautogui opencv-python pillow

How to Use
Run the Server: Open server.py and click the "START SERVER" button.
Run the Client: Open client.py in a different terminal.
Connect: Enter the IP address of the server (use 127.0.0.1 if testing on the same computer) and enter the password cnproject.

Files in this Project
server.py: The host application with a GUI to manage the connection.
client.py: The viewer application that displays the remote screen.
