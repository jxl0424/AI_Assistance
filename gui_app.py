import customtkinter as ctk
import threading
import queue
import sys
import time
from main import JarvisAgent
from feedback_system import FeedbackSystem

# Configuration
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class GuiFeedback(FeedbackSystem):
    def __init__(self, update_queue):
        super().__init__()
        self.update_queue = update_queue
        
    def print_status(self, message, status="info"):
        self.update_queue.put(("status", message, status))
        super().print_status(message, status)

    def print_command(self, text):
        self.update_queue.put(("user", text))
        super().print_command(text)

    def print_action(self, action, target):
        self.update_queue.put(("action", f"{action} -> {target}"))
        super().print_action(action, target)
        
    def show_thinking(self):
        self.update_queue.put(("state", "Thinking..."))
        super().show_thinking()
        
    def clear_thinking(self):
        self.update_queue.put(("state", "Idle"))
        super().clear_thinking()

    def activation_beep(self):
        self.update_queue.put(("state", "Listening..."))
        super().activation_beep()

class JarvisGui(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("JARVIS AI Assistant")
        self.geometry("600x700")
        
        # Grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header
        self.header_frame = ctk.CTkFrame(self, height=60)
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        self.title_label = ctk.CTkLabel(self.header_frame, text="JARVIS SYSTEM", font=("Roboto", 24, "bold"))
        self.title_label.pack(pady=10)
        
        self.status_label = ctk.CTkLabel(self.header_frame, text="Offline", text_color="gray")
        self.status_label.pack(pady=5)

        # Chat Area
        self.chat_frame = ctk.CTkScrollableFrame(self)
        self.chat_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        
        # Controls
        self.control_frame = ctk.CTkFrame(self, height=80)
        self.control_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        
        self.start_button = ctk.CTkButton(self.control_frame, text="Start System", command=self.start_system)
        self.start_button.pack(side="left", padx=20, pady=20)
        
        self.listen_button = ctk.CTkButton(self.control_frame, text="Listen Now", command=self.manual_listen, state="disabled")
        self.listen_button.pack(side="right", padx=20, pady=20)

        # Queue for thread communication
        self.update_queue = queue.Queue()
        self.agent = None
        self.agent_thread = None
        
        # Start polling queue
        self.after(100, self.check_queue)

    def start_system(self):
        self.start_button.configure(state="disabled", text="System Running")
        self.status_label.configure(text="Initializing...", text_color="yellow")
        
        # Start Agent in Thread
        self.agent_thread = threading.Thread(target=self.run_agent, daemon=True)
        self.agent_thread.start()

    def run_agent(self):
        # Initialize Custom Feedback
        feedback = GuiFeedback(self.update_queue)
        
        try:
            self.agent = JarvisAgent(use_wake_word=True, feedback_system=feedback)
            
            # Enable manual listen button once initialized
            self.update_queue.put(("ready", True))
            
            # Run the agent loop
            self.agent.run()
        except Exception as e:
            self.update_queue.put(("error", str(e)))

    def manual_listen(self):
        # This is tricky because the agent loop is blocking.
        # For now, we rely on the wake word, but we could implement a trigger.
        pass

    def add_message(self, text, sender="system"):
        if sender == "user":
            bubble = ctk.CTkLabel(self.chat_frame, text=f"You: {text}", anchor="e", justify="right", fg_color="#2B2B2B", corner_radius=10, padx=10, pady=5)
            bubble.pack(anchor="e", pady=5, padx=5, fill="x")
        elif sender == "jarvis":
            bubble = ctk.CTkLabel(self.chat_frame, text=f"JARVIS: {text}", anchor="w", justify="left", fg_color="#1F6AA5", corner_radius=10, padx=10, pady=5)
            bubble.pack(anchor="w", pady=5, padx=5, fill="x")
        elif sender == "action":
            bubble = ctk.CTkLabel(self.chat_frame, text=f"⚙️ {text}", text_color="gray", font=("Arial", 12, "italic"))
            bubble.pack(anchor="center", pady=2)
            
    def check_queue(self):
        try:
            while True:
                msg_type, *data = self.update_queue.get_nowait()
                
                if msg_type == "status":
                    msg, status = data
                    self.status_label.configure(text=msg)
                    if status == "success":
                        self.add_message(msg, "jarvis")
                    elif status == "listening":
                        self.status_label.configure(text_color="#00FF00")
                    elif status == "wake":
                        self.status_label.configure(text_color="cyan")
                        
                elif msg_type == "user":
                    self.add_message(data[0], "user")
                    
                elif msg_type == "action":
                    self.add_message(data[0], "action")
                    
                elif msg_type == "state":
                    self.status_label.configure(text=data[0])
                    
                elif msg_type == "ready":
                    self.listen_button.configure(state="normal")
                    
                elif msg_type == "error":
                    self.add_message(f"Error: {data[0]}", "system")
                    
        except queue.Empty:
            pass
        
        self.after(100, self.check_queue)

if __name__ == "__main__":
    app = JarvisGui()
    app.mainloop()
