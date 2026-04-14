import socket, struct, cv2, numpy as np, hashlib, threading, time, os
import tkinter as tk
from tkinter import messagebox
from PIL import Image
from io import BytesIO
from datetime import datetime

BG_COLOR = "#FFFFFF"
INPUT_BG = "#FDFCFE"
ACCENT_PURPLE = "#7C3AED" 
TEXT_COLOR = "#1E1B4B"

class AnonRemoteClient:
    def __init__(self):
        # Setup the main window
        self.root = tk.Tk()
        self.root.title("Anon Remote Client")
        self.root.geometry("450x700")
        self.root.configure(bg=BG_COLOR)
        
        self.running = False
        self.recording = False
        self.video_writer = None
        self.first_frame_received = False
        self.create_gui()

    def create_gui(self):
        # Build the login and connection screen
        header = tk.Frame(self.root, bg=BG_COLOR)
        header.pack(pady=35)
        tk.Label(header, text="ANON REMOTE", font=('Arial', 20, 'bold'), fg=ACCENT_PURPLE, bg=BG_COLOR).pack()
        tk.Label(header, text="Team: Adeen | Manahil | Abeeha", font=('Arial', 9), fg="#9F7AEA", bg=BG_COLOR).pack()

        self.fields_frame = tk.Frame(self.root, bg=BG_COLOR)
        self.fields_frame.pack(padx=45, fill='x')

        # Target Server details
        self.ip_entry = self.add_input("Target IP Address", "")
        self.port_entry = self.add_input("Target Port", "")
        self.pass_entry = self.add_input("Security Key", "", is_pass=True)

        # Quality slider for bandwidth control
        tk.Label(self.fields_frame, text="VIDEO QUALITY", font=('Arial', 8, 'bold'), fg=TEXT_COLOR, bg=BG_COLOR).pack(anchor='w', pady=(20,0))
        self.quality_var = tk.IntVar(value=70)
        tk.Scale(self.fields_frame, from_=30, to=100, orient='horizontal', variable=self.quality_var, 
                 bg=BG_COLOR, highlightthickness=0, troughcolor="#F5F3FF", activebackground=ACCENT_PURPLE).pack(fill='x')

        self.conn_status = tk.Label(self.root, text="System Ready", font=('Arial', 9, 'italic'), fg="#94A3B8", bg=BG_COLOR)
        self.conn_status.pack(pady=5)

        self.connect_btn = tk.Button(self.root, text="CONNECT", font=('Arial', 11, 'bold'), 
                                   bg=ACCENT_PURPLE, fg='white', relief='flat', cursor='hand2', command=self.connect)
        self.connect_btn.pack(pady=10, padx=45, fill='x', ipady=12)

        self.record_btn = tk.Button(self.root, text="🔴 START RECORDING", font=('Arial', 10, 'bold'), 
                                   bg="#F5F3FF", fg=ACCENT_PURPLE, relief='flat', cursor='hand2', 
                                   state='disabled', command=self.toggle_recording)
        self.record_btn.pack(pady=5, padx=45, fill='x', ipady=10)

    def add_input(self, label, default, is_pass=False):
        # Helper to create text entry boxes
        tk.Label(self.fields_frame, text=label.upper(), font=('Arial', 8, 'bold'), fg=TEXT_COLOR, bg=BG_COLOR).pack(anchor='w', pady=(15, 0))
        entry = tk.Entry(self.fields_frame, font=('Arial', 11), bg=INPUT_BG, relief='flat', highlightbackground="#EDE9FE", highlightthickness=1)
        if is_pass: entry.config(show="●")
        entry.insert(0, default)
        entry.pack(fill='x', ipady=8, pady=5)
        return entry

    def toggle_recording(self):
        # Start or stop the screen recording
        if not self.recording:
            self.recording = True
            self.record_btn.config(text="⏹ STOP RECORDING", bg="#EF4444", fg="white")
        else:
            self.recording = False
            if self.video_writer:
                self.video_writer.release() # Save file
                self.video_writer = None
            self.first_frame_received = False
            self.record_btn.config(text="🔴 START RECORDING", bg="#F5F3FF", fg=ACCENT_PURPLE)
            messagebox.showinfo("Saved", "Recording successfully saved in high resolution.")

    def connect(self):
        # Validate inputs before connecting
        ip = self.ip_entry.get().strip()
        port = self.port_entry.get().strip()
        if not ip or not port:
            messagebox.showwarning("Warning", "Enter Connection Details")
            return
        self.connect_btn.config(state='disabled', text="Connecting...")
        # Start connection in a separate thread so the UI doesn't freeze
        threading.Thread(target=self.do_connect, args=(ip, int(port), self.pass_entry.get()), daemon=True).start()

    def do_connect(self, ip, port, password):
        # Create socket and handle password check
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((ip, port))
            
            # Send hashed password for security
            self.client_socket.send(hashlib.sha256(password.encode()).hexdigest().encode())
            
            if self.client_socket.recv(1024).decode() == "SUCCESS":
                self.client_socket.send(str(self.quality_var.get()).encode())
                self.running = True
                self.root.after(0, lambda: [self.record_btn.config(state='normal'), self.conn_status.config(text="CONNECTED", fg=ACCENT_PURPLE)])
                self.receive_stream()
            else:
                self.root.after(0, lambda: messagebox.showerror("Error", "Auth Failed"))
                self.root.after(0, self.reset_ui)
        except:
            self.root.after(0, self.reset_ui)

    def reset_ui(self):
        # Reset buttons if disconnected
        self.connect_btn.config(state='normal', text="CONNECT")
        self.record_btn.config(state='disabled')
        self.conn_status.config(text="Disconnected", fg="#94A3B8")

    def receive_stream(self):
        # Main loop to receive and display video data
        cv2.namedWindow("Anon Remote Session", cv2.WINDOW_NORMAL)
        data = b""
        payload_size = struct.calcsize("Q") # Size of the header
        
        while self.running:
            try:
                # Get the image size first
                while len(data) < payload_size:
                    data += self.client_socket.recv(8192)
                packed_size = data[:payload_size]
                data = data[payload_size:]
                msg_size = struct.unpack("Q", packed_size)[0]
                
                # Get the actual image data
                while len(data) < msg_size:
                    data += self.client_socket.recv(8192)
                
                frame_data = data[:msg_size]
                data = data[msg_size:]
                
                # Convert bytes back to an image
                image = Image.open(BytesIO(frame_data))
                frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

                # Handle video recording
                if self.recording:
                    if not self.first_frame_received:
                        h, w, _ = frame.shape
                        timestamp = datetime.now().strftime('%H%M%S')
                        filename = f"Anon_HD_{timestamp}.mp4"
                        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                        self.video_writer = cv2.VideoWriter(filename, fourcc, 15.0, (w, h))
                        self.first_frame_received = True
                    
                    if self.video_writer:
                        self.video_writer.write(frame)
                        # Show red dot when recording
                        cv2.circle(frame, (25, 25), 7, (0, 0, 255), -1)

                # Show the stream
                cv2.imshow("Anon Remote Session", frame)
                if cv2.waitKey(1) == ord('q'): break
            except: break
        
        # Close everything
        self.running = False
        if self.video_writer: self.video_writer.release()
        cv2.destroyAllWindows()
        self.root.after(0, self.reset_ui)

if __name__ == "__main__":
    AnonRemoteClient().root.mainloop()