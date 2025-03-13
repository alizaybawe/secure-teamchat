import tkinter as tk
from tkinter import PhotoImage
import os
import sys
import client
import queue
# from tkinter import messagebox
# from relay import start_server

class AppWindow(tk.Tk):
    def __init__(self, client):
        super().__init__() 
        if getattr(sys, 'frozen', False):  # If the app is frozen (packaged)
            icon_path = os.path.join(sys._MEIPASS, 'icon.ico')
        else:
            icon_path = './icon.ico'
        
        # Load client object
        self.client = client
        # Main settings
        background_color = "#121212"
        background_lighter_color = "#1E1E1E"

        self.iconbitmap(icon_path)
        self.configure(bg="#1E1E1E",highlightthickness = 0)
        self.title("Garchat")
        self.geometry("800x600")

        paned_window = tk.PanedWindow(self, orient=tk.HORIZONTAL, bd=0, relief="flat", sashwidth=0, sashrelief="flat")
        paned_window.pack(fill=tk.BOTH, expand=True)


        # Left section (for information)
        left_frame = tk.Frame(paned_window,  width=200, bg=background_lighter_color, bd=0, relief="flat")
        left_frame.pack_propagate(False)  # Prevent it from resizing based on contents
        paned_window.add(left_frame)

        # Right section (for the chat)
        right_frame = tk.Frame(paned_window, bg=background_color, bd=0, relief="flat")
        right_frame.pack_propagate(False)
        paned_window.add(right_frame)

        # Left section content (e.g., information)
        # info_label = tk.Label(left_frame, text="Information and Connections", font=("Arial", 8))
        # info_label.pack(pady=20)

        # Right section content (chat area)
        chat_frame = tk.Frame(right_frame, bg=background_color)
        chat_frame.pack(fill=tk.BOTH, expand=True)

        # Chatbox (for displaying messages)
        self.chatbox = tk.Text(chat_frame, state=tk.DISABLED, wrap=tk.WORD, bg=background_color, fg="white", bd=0, relief="flat")
        self.chatbox.pack(fill=tk.Y, expand=True, padx=10, pady=10)

        # Bottom frame for chat input and send button
        bottom_frame = tk.Frame(right_frame, height=50, bg=background_color)
        bottom_frame.pack(fill=tk.X, side=tk.BOTTOM)

        # Chat input box
        chat_input = tk.Text(bottom_frame, font=("Arial", 12), bg=background_lighter_color, fg="white", height=3, bd=0, relief="flat")
        chat_input.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=5)
        chat_input.bind("<Return>", lambda event: self.send_message(event, chat_input))

        # Send button (with an icon)
        send_button = tk.Button(bottom_frame, text=">", bg="black", fg="white", font=("Arial", 12))
        send_button.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Upload file button (with an icon)
        send_button = tk.Button(bottom_frame, text="Upload file", bg="black", fg="white", font=("Arial", 12))
        send_button.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=5)

    def load_incoming_data(self):
        try:
            data = self.client.recv_queue.get_nowait()
            print(f"GOT DATA {data}")
            self.chatbox.config(state=tk.NORMAL)  # Enable text widget
            self.chatbox.insert(tk.END, data + b"\n")  # Insert message at the end
            self.chatbox.see(tk.END)  # Auto-scroll to the latest message
            self.chatbox.config(state=tk.DISABLED)  # Disable editing again
        except queue.Empty:
            pass
        self.after(100, self.load_incoming_data)

    def send_message(self, event, msgbox):
        msg = msgbox.get("1.0", tk.END).strip()
        if msg:
            self.client.send_queue.put(msg)
        print(f"Inserted message in send_message queue: {msg}")
        # await self.client.send_message(msg)
        # Send via client.py

    # Show it on the chatbox 
    
    # Erase message box

    