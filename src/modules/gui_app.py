import customtkinter as ctk
import threading
import queue
import sys
import time
from datetime import datetime
from main import JarvisAgent
from src.modules.feedback_system import FeedbackSystem

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
        self.update_queue.put(("state", "Ready"))
        super().clear_thinking()

    def activation_beep(self):
        self.update_queue.put(("state", "Listening..."))
        super().activation_beep()

class JarvisGui(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("JARVIS AI Assistant")
        self.geometry("700x800")
        
        # Grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Header with improved styling
        self.header_frame = ctk.CTkFrame(self, height=100, fg_color="#1a1a2e")
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        self.header_frame.grid_propagate(False)
        
        self.title_label = ctk.CTkLabel(
            self.header_frame, 
            text="J.A.R.V.I.S.", 
            font=("Roboto", 32, "bold"),
            text_color="#00d9ff"
        )
        self.title_label.pack(pady=(15, 5))
        
        self.subtitle_label = ctk.CTkLabel(
            self.header_frame,
            text="Just A Rather Very Intelligent System",
            font=("Roboto", 11),
            text_color="#888888"
        )
        self.subtitle_label.pack()
        
        # Status bar with indicators
        self.status_bar = ctk.CTkFrame(self, height=50, fg_color="#16213e")
        self.status_bar.grid(row=1, column=0, sticky="ew", padx=0, pady=0)
        self.status_bar.grid_propagate(False)
        
        # Status indicators
        status_container = ctk.CTkFrame(self.status_bar, fg_color="transparent")
        status_container.pack(expand=True)
        
        self.system_status = ctk.CTkLabel(
            status_container,
            text="● Offline",
            font=("Roboto", 12),
            text_color="#888888"
        )
        self.system_status.pack(side="left", padx=20)
        
        self.mic_status = ctk.CTkLabel(
            status_container,
            text="🎤 Inactive",
            font=("Roboto", 12),
            text_color="#888888"
        )
        self.mic_status.pack(side="left", padx=20)
        
        self.state_label = ctk.CTkLabel(
            status_container,
            text="Waiting",
            font=("Roboto", 12, "italic"),
            text_color="#888888"
        )
        self.state_label.pack(side="left", padx=20)

        # Chat Area with improved styling
        self.chat_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="#0f1419",
            scrollbar_button_color="#2a2a3e",
            scrollbar_button_hover_color="#3a3a4e"
        )
        self.chat_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
        
        # Welcome message
        self.add_system_message("JARVIS initialized. Click 'Start System' to begin.")
        
        # Controls with improved layout
        self.control_frame = ctk.CTkFrame(self, height=100, fg_color="#16213e")
        self.control_frame.grid(row=3, column=0, sticky="ew", padx=0, pady=0)
        self.control_frame.grid_propagate(False)
        
        # Button container
        button_container = ctk.CTkFrame(self.control_frame, fg_color="transparent")
        button_container.pack(expand=True, fill="x", padx=20)
        
        self.start_button = ctk.CTkButton(
            button_container,
            text="▶ Start System",
            command=self.start_system,
            font=("Roboto", 14, "bold"),
            height=40,
            fg_color="#00d9ff",
            hover_color="#00b8d4",
            text_color="#000000"
        )
        self.start_button.pack(side="left", padx=10, pady=20)
        
        self.mute_button = ctk.CTkButton(
            button_container,
            text="🔇 Mute",
            command=self.toggle_mute,
            font=("Roboto", 12),
            height=40,
            width=100,
            state="disabled",
            fg_color="#444444",
            hover_color="#555555"
        )
        self.mute_button.pack(side="left", padx=10, pady=20)
        
        self.theme_button = ctk.CTkButton(
            button_container,
            text="☀ Light",
            command=self.toggle_theme,
            font=("Roboto", 12),
            height=40,
            width=100,
            fg_color="#444444",
            hover_color="#555555"
        )
        self.theme_button.pack(side="left", padx=10, pady=20)
        
        self.clear_button = ctk.CTkButton(
            button_container,
            text="🗑 Clear",
            command=self.clear_chat,
            font=("Roboto", 12),
            height=40,
            width=100,
            fg_color="#444444",
            hover_color="#555555"
        )
        self.clear_button.pack(side="right", padx=10, pady=20)

        # Visualizer
        self.visualizer_canvas = ctk.CTkCanvas(
            self.status_bar, 
            width=100, 
            height=30, 
            bg="#16213e", 
            highlightthickness=0
        )
        self.visualizer_canvas.pack(side="right", padx=20)
        self.visualizer_bar = self.visualizer_canvas.create_rectangle(
            0, 10, 0, 20, 
            fill="#00d9ff", 
            outline=""
        )

        # Queue for thread communication
        self.update_queue = queue.Queue()
        self.agent = None
        self.agent_thread = None
        self.is_muted = False
        self.message_count = 0
        
        # Keyboard shortcuts
        self.bind("<Control-m>", lambda e: self.toggle_mute())
        self.bind("<Control-l>", lambda e: self.toggle_theme())
        self.bind("<Control-c>", lambda e: self.clear_chat())
        
        # Start polling queue
        self.after(50, self.check_queue) # Poll faster for visualizer

    def add_system_message(self, text):
        """Add system message to chat"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        msg_frame = ctk.CTkFrame(self.chat_frame, fg_color="transparent")
        msg_frame.pack(fill="x", pady=5, padx=10)
        
        time_label = ctk.CTkLabel(
            msg_frame,
            text=timestamp,
            font=("Roboto", 9),
            text_color="#555555"
        )
        time_label.pack(anchor="w")
        
        bubble = ctk.CTkLabel(
            msg_frame,
            text=f"⚙ {text}",
            font=("Roboto", 11),
            text_color="#888888",
            anchor="w",
            justify="left"
        )
        bubble.pack(anchor="w", pady=2)

    def start_system(self):
        self.start_button.configure(state="disabled", text="⏸ System Running")
        self.mute_button.configure(state="normal")
        self.system_status.configure(text="● Initializing...", text_color="#ffaa00")
        self.add_system_message("Starting JARVIS system...")
        
        # Start Agent in Thread
        self.agent_thread = threading.Thread(target=self.run_agent, daemon=True)
        self.agent_thread.start()

    def on_amplitude_update(self, amplitude):
        """Callback for audio amplitude"""
        try:
            self.update_queue.put(("amplitude", amplitude))
        except:
            pass

    def run_agent(self):
        # Initialize Custom Feedback
        feedback = GuiFeedback(self.update_queue)
        
        try:
            self.agent = JarvisAgent(
                use_wake_word=True, 
                feedback_system=feedback,
                on_amplitude=self.on_amplitude_update
            )
            
            # Enable manual listen button once initialized
            self.update_queue.put(("ready", True))
            
            # Run the agent loop
            self.agent.run()
        except Exception as e:
            self.update_queue.put(("error", str(e)))

    def toggle_mute(self):
        """Toggle microphone mute"""
        self.is_muted = not self.is_muted
        
        if self.is_muted:
            self.mute_button.configure(
                text="🔊 Unmute",
                fg_color="#ff4444",
                hover_color="#ff6666"
            )
            self.mic_status.configure(text="🔇 Muted", text_color="#ff4444")
            self.add_system_message("Microphone muted")
        else:
            self.mute_button.configure(
                text="🔇 Mute",
                fg_color="#444444",
                hover_color="#555555"
            )
            self.mic_status.configure(text="🎤 Active", text_color="#00ff88")
            self.add_system_message("Microphone active")

    def toggle_theme(self):
        """Toggle between dark and light theme"""
        current = ctk.get_appearance_mode()
        
        if current == "Dark":
            ctk.set_appearance_mode("Light")
            self.theme_button.configure(text="🌙 Dark")
            self.add_system_message("Switched to light theme")
        else:
            ctk.set_appearance_mode("Dark")
            self.theme_button.configure(text="☀ Light")
            self.add_system_message("Switched to dark theme")

    def clear_chat(self):
        """Clear chat history"""
        for widget in self.chat_frame.winfo_children():
            widget.destroy()
        self.message_count = 0
        self.add_system_message("Chat cleared")

    def add_message(self, text, sender="system"):
        """Add message to chat with improved styling"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.message_count += 1
        
        msg_frame = ctk.CTkFrame(self.chat_frame, fg_color="transparent")
        msg_frame.pack(fill="x", pady=5, padx=10)
        
        time_label = ctk.CTkLabel(
            msg_frame,
            text=timestamp,
            font=("Roboto", 9),
            text_color="#555555"
        )
        
        if sender == "user":
            time_label.pack(anchor="e")
            bubble = ctk.CTkFrame(msg_frame, fg_color="#00d9ff", corner_radius=15)
            bubble.pack(anchor="e", padx=5)
            
            label = ctk.CTkLabel(
                bubble,
                text=f"You: {text}",
                font=("Roboto", 12),
                text_color="#000000",
                wraplength=400,
                justify="right"
            )
            label.pack(padx=15, pady=10)
            
        elif sender == "jarvis":
            time_label.pack(anchor="w")
            bubble = ctk.CTkFrame(msg_frame, fg_color="#2a2a3e", corner_radius=15)
            bubble.pack(anchor="w", padx=5)
            
            label = ctk.CTkLabel(
                bubble,
                text=f"JARVIS: {text}",
                font=("Roboto", 12),
                text_color="#ffffff",
                wraplength=400,
                justify="left"
            )
            label.pack(padx=15, pady=10)
            
        elif sender == "action":
            time_label.pack(anchor="center")
            label = ctk.CTkLabel(
                msg_frame,
                text=f"⚡ {text}",
                font=("Roboto", 10, "italic"),
                text_color="#888888"
            )
            label.pack(anchor="center", pady=2)
        
        # Auto-scroll to bottom
        self.chat_frame._parent_canvas.yview_moveto(1.0)

    def check_queue(self):
        try:
            while True:
                msg_type, *data = self.update_queue.get_nowait()
                
                if msg_type == "status":
                    msg, status = data
                    self.state_label.configure(text=msg)
                    
                    if status == "success":
                        self.add_message(msg, "jarvis")
                    elif status == "listening":
                        self.state_label.configure(text_color="#00ff88")
                        self.mic_status.configure(text="🎤 Listening", text_color="#00ff88")
                    elif status == "wake":
                        self.state_label.configure(text_color="#00d9ff")
                        self.mic_status.configure(text="🎤 Waiting", text_color="#888888")
                        
                elif msg_type == "user":
                    self.add_message(data[0], "user")
                    
                elif msg_type == "action":
                    self.add_message(data[0], "action")
                    
                elif msg_type == "state":
                    self.state_label.configure(text=data[0])
                    
                    if data[0] == "Thinking...":
                        self.state_label.configure(text_color="#ffaa00")
                    elif data[0] == "Listening...":
                        self.state_label.configure(text_color="#00ff88")
                        self.mic_status.configure(text="🎤 Listening", text_color="#00ff88")
                    else:
                        self.state_label.configure(text_color="#888888")
                    
                elif msg_type == "ready":
                    self.system_status.configure(text="● Online", text_color="#00ff88")
                    self.add_system_message("JARVIS is now online. Say 'JARVIS' to activate.")
                    
                elif msg_type == "error":
                    self.add_system_message(f"Error: {data[0]}")
                    self.system_status.configure(text="● Error", text_color="#ff4444")
                    
                elif msg_type == "amplitude":
                    amp = data[0]
                    # Update visualizer bar
                    # Canvas width is 100
                    width = int(amp) # amp is 0-100
                    self.visualizer_canvas.coords(self.visualizer_bar, 0, 10, width, 20)
                    
                    # Change color based on intensity
                    color = "#00d9ff"
                    if amp > 70: color = "#ff4444"
                    elif amp > 40: color = "#00ff88"
                    self.visualizer_canvas.itemconfig(self.visualizer_bar, fill=color)
                    
        except queue.Empty:
            pass
        
        self.after(100, self.check_queue)

if __name__ == "__main__":
    app = JarvisGui()
    app.mainloop()
