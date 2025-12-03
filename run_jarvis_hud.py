import customtkinter as ctk
import time
import math
import psutil
import threading
import random
import queue
import sys
import os
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from main import JarvisAgent
from src.modules.feedback_system import FeedbackSystem

class HudFeedback(FeedbackSystem):
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

class JarvisHUD(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Window Setup
        self.title("JARVIS HUD")
        
        # Fullscreen and Transparent
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        self.geometry(f"{screen_width}x{screen_height}+0+0")
        self.overrideredirect(True) # Remove borders
        self.wm_attributes("-topmost", True) # Always on top
        self.wm_attributes("-transparentcolor", "#000001") # Transparency key
        self.config(bg="#000001") # Set background to transparency key
        
        # Colors
        self.color_primary = "#00d9ff" # Cyan
        self.color_secondary = "#005577" # Dark Cyan
        self.color_alert = "#ff4444" # Red
        self.color_success = "#00ff88" # Green
        self.color_bg = "#000001" # Transparent
        
        # Canvas for drawing
        self.canvas = ctk.CTkCanvas(
            self, 
            width=screen_width, 
            height=screen_height,
            bg=self.color_bg,
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)
        
        # State
        self.running = True
        self.angle = 0
        self.amplitude = 0
        self.status_text = "SYSTEM ONLINE"
        self.status_color = self.color_primary
        self.last_user_text = ""
        self.last_jarvis_text = ""
        
        # Agent Integration
        self.update_queue = queue.Queue()
        self.agent_thread = threading.Thread(target=self.run_agent, daemon=True)
        self.agent_thread.start()
        
        # Start Animations
        self.animate()
        self.check_queue()
        
        # Bind escape to quit
        self.bind("<Escape>", lambda e: self.destroy())

    def on_amplitude_update(self, amplitude):
        try:
            self.update_queue.put(("amplitude", amplitude))
        except:
            pass

    def run_agent(self):
        feedback = HudFeedback(self.update_queue)
        try:
            self.agent = JarvisAgent(
                use_wake_word=True, 
                feedback_system=feedback,
                on_amplitude=self.on_amplitude_update
            )
            self.agent.run()
        except Exception as e:
            self.update_queue.put(("error", str(e)))

    def check_queue(self):
        try:
            while True:
                msg_type, *data = self.update_queue.get_nowait()
                
                if msg_type == "amplitude":
                    self.amplitude = data[0]
                    
                elif msg_type == "state":
                    self.status_text = data[0].upper()
                    if "LISTENING" in self.status_text:
                        self.status_color = self.color_success
                    elif "THINKING" in self.status_text:
                        self.status_color = "#ffaa00" # Orange
                    else:
                        self.status_color = self.color_primary
                        
                elif msg_type == "user":
                    self.last_user_text = f"YOU: {data[0]}"
                    
                elif msg_type == "status":
                    msg, status = data
                    if status == "success":
                        self.last_jarvis_text = f"JARVIS: {msg}"
                        
        except queue.Empty:
            pass
        
        self.after(50, self.check_queue)

    def draw_circle_progress(self, x, y, radius, percentage, color, width=2):
        self.canvas.create_oval(
            x-radius, y-radius, x+radius, y+radius,
            outline=self.color_secondary, width=width
        )
        extent = -(percentage / 100) * 360
        self.canvas.create_arc(
            x-radius, y-radius, x+radius, y+radius,
            start=90, extent=extent,
            outline=color, width=width, style="arc"
        )

    def draw_arc_reactor(self, cx, cy):
        radius = 60
        
        # Color based on status
        color = self.status_color
        
        self.canvas.create_oval(
            cx-radius, cy-radius, cx+radius, cy+radius,
            outline=color, width=2
        )
        
        inner_r = 45
        
        # Rotate faster if active
        rotation_speed = 5
        if "LISTENING" in self.status_text: rotation_speed = 15
        if "THINKING" in self.status_text: rotation_speed = 25
        
        self.angle = (self.angle + rotation_speed) % 360
        
        for i in range(3):
            start_angle = self.angle + (i * 120)
            self.canvas.create_arc(
                cx-inner_r, cy-inner_r, cx+inner_r, cy+inner_r,
                start=start_angle, extent=60,
                outline=color, width=5, style="arc"
            )
            
        self.canvas.create_oval(
            cx-10, cy-10, cx+10, cy+10,
            fill=color, outline=""
        )
        
        self.canvas.create_text(
            cx, cy+80,
            text=self.status_text,
            fill=color,
            font=("Consolas", 12, "bold")
        )

    def draw_system_stats(self):
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        x, y = 100, 100
        self.draw_circle_progress(x, y, 40, cpu, self.color_primary)
        self.canvas.create_text(x, y, text=f"CPU\n{int(cpu)}%", fill=self.color_primary, font=("Consolas", 10))
        self.draw_circle_progress(x+100, y, 40, ram, self.color_primary)
        self.canvas.create_text(x+100, y, text=f"RAM\n{int(ram)}%", fill=self.color_primary, font=("Consolas", 10))

    def draw_clock(self):
        now = datetime.now()
        time_str = now.strftime("%H:%M:%S")
        date_str = now.strftime("%Y-%m-%d")
        w = self.winfo_screenwidth()
        x = w - 150
        y = 80
        self.canvas.create_text(x, y, text=time_str, fill=self.color_primary, font=("Consolas", 32, "bold"))
        self.canvas.create_text(x, y+30, text=date_str, fill=self.color_secondary, font=("Consolas", 14))

    def draw_visualizer(self):
        w = self.winfo_screenwidth()
        h = self.winfo_screenheight()
        cx = w // 2
        cy = h - 100
        
        points = []
        # Use real amplitude to modulate wave height
        base_height = 5 + (self.amplitude * 1.5) # Scale amplitude
        
        for i in range(-30, 31):
            x = cx + (i * 10)
            # Sine wave with noise
            noise = random.uniform(0.8, 1.2)
            height = base_height * math.sin((self.angle + i*10) * 0.1) * noise
            points.append(x)
            points.append(cy + height)
            
        if len(points) > 4:
            self.canvas.create_line(points, fill=self.status_color, width=2, smooth=True)

    def draw_messages(self):
        # Display last user and jarvis messages
        w = self.winfo_screenwidth()
        h = self.winfo_screenheight()
        cx = w // 2
        
        if self.last_user_text:
            self.canvas.create_text(
                cx, h - 200,
                text=self.last_user_text,
                fill=self.color_primary,
                font=("Consolas", 14),
                width=600, justify="center"
            )
            
        if self.last_jarvis_text:
            self.canvas.create_text(
                cx, h - 170,
                text=self.last_jarvis_text,
                fill="#ffffff",
                font=("Consolas", 14, "italic"),
                width=600, justify="center"
            )

    def animate(self):
        if not self.running: return
        self.canvas.delete("all")
        
        w = self.winfo_screenwidth()
        h = self.winfo_screenheight()
        
        self.draw_arc_reactor(100, h-100)
        self.draw_system_stats()
        self.draw_clock()
        self.draw_visualizer()
        self.draw_messages()
        
        self.canvas.create_line(0, 50, w, 50, fill=self.color_secondary, width=1)
        self.canvas.create_line(0, h-50, w, h-50, fill=self.color_secondary, width=1)
        
        self.after(50, self.animate)

if __name__ == "__main__":
    app = JarvisHUD()
    app.mainloop()
