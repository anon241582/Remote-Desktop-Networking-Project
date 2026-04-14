import socket, pyautogui, struct, threading, time, hashlib
import tkinter as tk
from tkinter import scrolledtext
from datetime import datetime
from io import BytesIO

# CONFIGURATION
SERVER_HOST = '0.0.0.0'     # Listen on all available network interfaces
SERVER_PORT = 9999          # Custom port for application traffic
SERVER_PASSWORD = 'cnproject'

BG_COLOR = "#FFFFFF"      
SIDEBAR_COLOR = "#F5F3FF" 
ACCENT_PURPLE = "#7C3AED" 
TEXT_COLOR = "#1E1B4B"    

class AnonRemoteServer:
    def __init__(self):
        # Setup the main window properties
        self.root = tk.Tk()
        self.root.title("Anon Server Console")
        self.root.geometry("850x600")
        self.root.configure(bg=BG_COLOR)
        
        self.running = False
        self.client_socket = None
        self.client_quality = 70
        self.create_gui()
        
    def create_gui(self):
        # Build the sidebar and main logging area
        sidebar = tk.Frame(self.root, bg=SIDEBAR_COLOR, width=260)
        sidebar.pack(side='left', fill='y')
        sidebar.pack_propagate(False)
        
        tk.Label(sidebar, text="SERVER PANEL", font=('Arial', 14, 'bold'), 
                 fg=ACCENT_PURPLE, bg=SIDEBAR_COLOR).pack(pady=40)
        
        self.status_label = tk.Label(sidebar, text="● SYSTEM OFFLINE", 
                                     fg='#9F7AEA', bg=SIDEBAR_COLOR, font=('Arial', 10, 'bold'))
        self.status_label.pack(pady=10)
        
        # Start button to trigger the socket listener
        self.start_btn = tk.Button(sidebar, text="START SERVER", bg=ACCENT_PURPLE, fg='white', 
                                  relief='flat', width=18, font=('Arial', 11, 'bold'),
                                  cursor='hand2', command=self.start_server)
        self.start_btn.pack(pady=30, ipady=10)

        main_content = tk.Frame(self.root, bg=BG_COLOR)
        main_content.pack(side='right', fill='both', expand=True, padx=25, pady=25)

        tk.Label(main_content, text="Network Activity Logs", font=('Arial', 13, 'bold'), 
                 fg=TEXT_COLOR, bg=BG_COLOR).pack(anchor='w')
        
        # Real-time network log area
        self.log_area = scrolledtext.ScrolledText(main_content, bg='#FAF9FF', fg=TEXT_COLOR, 
                                                font=('Consolas', 10), relief='flat', borderwidth=0)
        self.log_area.pack(fill='both', expand=True, pady=15)
        self.log_msg("Ready to host session...")

    def log_msg(self, msg):
        # Adds messages to the UI with a current timestamp
        time_str = datetime.now().strftime("%H:%M:%S")
        self.log_area.insert('end', f"[{time_str}] {msg}\n")
        self.log_area.see('end')

    def start_server(self):
        # Initialize the TCP socket and start listening
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.bind((SERVER_HOST, SERVER_PORT))
            self.server_socket.listen(1)
            
            self.running = True
            self.status_label.config(text="● SYSTEM ONLINE", fg=ACCENT_PURPLE)
            self.start_btn.config(state='disabled', bg="#E2E8F0", fg="#94A3B8")
            self.log_msg("Server active. Listening for remote connection...")
            
            # Use threading so the GUI doesn't freeze while waiting for connections
            threading.Thread(target=self.accept_conn, daemon=True).start()
        except Exception as e:
            self.log_msg(f"Error: {e}")

    def accept_conn(self):
        # Handle connection requests and password verification
        while self.running:
            try:
                self.client_socket, addr = self.server_socket.accept()
                self.log_msg(f"Incoming connection from {addr[0]}")
                
                # Check the hashed password sent by the client
                client_pw = self.client_socket.recv(1024).decode('utf-8')
                server_pw_hash = hashlib.sha256(SERVER_PASSWORD.encode()).hexdigest()
                
                if client_pw == server_pw_hash:
                    self.client_socket.send(b"SUCCESS")
                    self.log_msg("Handshake verified. Access granted.")
                    
                    # Set image quality preference
                    quality_data = self.client_socket.recv(1024).decode('utf-8')
                    self.client_quality = int(quality_data)
                    
                    # Start sending the screen data
                    threading.Thread(target=self.stream_screen, daemon=True).start()
                else:
                    self.client_socket.send(b"FAILED")
                    self.client_socket.close()
            except: 
                break

    def stream_screen(self):
        # Main loop to capture and send screenshots
        while self.running:
            try:
                # Take the screenshot
                screen = pyautogui.screenshot()
                
                # Convert to JPEG and compress to save bandwidth
                buf = BytesIO()
                screen.save(buf, format='JPEG', quality=self.client_quality)
                data = buf.getvalue()
                
                # Send image size first so the client knows how many bytes to read
                header = struct.pack("Q", len(data)) 
                self.client_socket.sendall(header + data)
                
                # Control the frame rate (approx 25 FPS)
                time.sleep(0.04)
            except: 
                break
        self.log_msg("Session terminated.")

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    AnonRemoteServer().run()