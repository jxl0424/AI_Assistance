from src.core.logger_config import get_logger

logger = get_logger(__name__)
"""
Command executor - Execute system commands based on intents
"""

import subprocess
import os
import psutil
import time
from src.utils.apps_config import find_application_path, APPLICATIONS
from src.modules.finance_manager_sql import FinanceManagerSQL as FinanceManager  # UPGRADED: SQLite instead of CSV
from src.modules.reminder_manager import ReminderManager
from datetime import datetime, timedelta
import re
from src.modules.memory_manager import MemoryManager
from src.modules.tools_manager import ToolsManager  # IMPORT TOOLS
from src.modules.vision_manager import VisionManager # IMPORT VISION
from src.modules.knowledge_manager import KnowledgeManager # IMPORT KNOWLEDGE

class CommandExecutor:
    def __init__(self, memory_manager):
        """Initialize command executor"""
        self.running_processes = {}
        self.finance = FinanceManager()
        self.memory = memory_manager
        self.tools = ToolsManager() # INIT TOOLS
        self.reminders = ReminderManager()  # INIT REMINDERS
        self.vision = VisionManager() # INIT VISION
        self.knowledge = KnowledgeManager() # INIT KNOWLEDGE
    
    def execute(self, intent):
        """
        Execute command based on intent
        """
        if not intent.get("success"):
            return {
                "success": False,
                "message": "Could not understand command"
            }
        
        action = intent.get("action")
        target = intent.get("target")
        query = intent.get("query")
        
        # Route to appropriate handler
        if action == "open":
            return self._open_application(target, query)
        elif action == "close":
            return self._close_application(target)
        elif action == "search":
            return self._search_web(query)
        elif action == "system":
            return self._control_system(target)
            
        # NEW: Finance Handler - Analysis
        elif action == "ask_finance":
            return {
                "success": True,
                "message": self.finance.analyze_spending(
                    category=intent.get("category"),
                    timeframe=intent.get("timeframe", "all")
                )
            }
            
        # NEW: Finance Handler
        elif action == "track_expense":
            return self.finance.log_transaction(
                amount=intent.get("amount"),
                currency=intent.get("currency", "$"),
                category=intent.get("category"),
                description=intent.get("description")
            )
            
        # NEW: Memory Handler
        elif action == "remember":
            fact = intent.get("fact")
            if fact:
                self.memory.add_memory(fact)
                return {"success": True, "message": f"I'll remember that: {fact}"}
            return {"success": False, "message": "No fact provided to remember"}
            
        # NEW: Weather Handler
        elif action == "weather":
            city = intent.get("target", "Singapore") # Default to Singapore if no target
            return {"success": True, "message": self.tools.get_weather(city)}
            
        # NEW: Smart Search Handler (Updated with RAG)
        elif action == "smart_search":
            # 1. Check Knowledge Base first
            kb_results = self.knowledge.query(query)
            if kb_results:
                # Found something in local files
                context = "\n\n".join([f"Source: {r['source']}\n{r['content']}" for r in kb_results])
                return {
                    "success": True, 
                    "message": f"Found in Knowledge Base:\n{context}\n\n(I also searched the web if needed, but local data takes priority.)"
                }
            
            # 2. Fallback to Web Search
            return {"success": True, "message": self.tools.search_web(query)}
            
        # NEW: Vision Handler
        elif action == "analyze_screen":
            query = intent.get("query", "Describe what is on my screen")
            return {"success": True, "message": self.vision.analyze_screen(query)}
            
        # Reminder Handler
        elif action == "set_reminder":
            text = intent.get("text") or intent.get("query")
            time_str = intent.get("time")
            recurring = intent.get("recurring")
            
            if not text or not time_str:
                return {"success": False, "message": "Need reminder text and time"}
            
            try:
                reminder_time = self._parse_time(time_str)
                result = self.reminders.add_reminder(text, reminder_time, recurring)
                return result
            except Exception as e:
                return {"success": False, "message": f"Error: {e}"}
        
        # Timer Handler
        elif action == "set_timer":
            duration = intent.get("duration_minutes")
            label = intent.get("label", "Timer")
            
            if not duration:
                return {"success": False, "message": "Need timer duration"}
            
            return self.reminders.add_timer(duration, label)
        
        # List Reminders Handler
        elif action == "list_reminders":
            reminders_list = self.reminders.list_reminders()
            return {"success": True, "message": reminders_list}
        
        else:
            return {
                "success": True, # It was likely just chat
                "message": "Conversation processed"
            }
    
    def _open_application(self, app_name, query=None):
        """Open an application"""
        logger.info(f"Opening {app_name}...")
        
        path = find_application_path(app_name)
        if not path:
            return {"success": False, "message": f"Could not find path for {app_name}"}
            
        try:
            # Start the process
            proc = subprocess.Popen(path)
            self.running_processes[app_name] = proc
            return {"success": True, "message": f"Opened {app_name}"}
        except Exception as e:
            return {"success": False, "message": f"Failed to open {app_name}: {e}"}

    def _close_application(self, app_name):
        """Close an application"""
        # Simple kill implementation for demo
        return {"success": False, "message": "Close function requires os specific implementation"}

    def _search_web(self, query):
        """Open browser with search"""
        import webbrowser
        url = f"https://www.google.com/search?q={query}"
        webbrowser.open(url)
        return {"success": True, "message": f"Searched for {query}"}

    def _control_system(self, command):
        """Basic system controls"""
        try:
            import pyautogui
            if command == "volume_up":
                pyautogui.press("volumeup")
            elif command == "volume_down":
                pyautogui.press("volumedown")
            elif command == "mute":
                pyautogui.press("volumemute")
            elif command == "screenshot":
                pyautogui.screenshot("screenshot.png")
                return {"success": True, "message": "Screenshot saved"}
            
            return {"success": True, "message": f"Executed {command}"}
        except Exception as e:
            return {"success": False, "message": f"System control failed: {e}"}
            
    def cleanup(self):
        pass
    def _parse_time(self, time_str):
        """Parse time string to datetime"""
        # Try ISO format first
        try:
            return datetime.fromisoformat(time_str)
        except:
            pass
        
        # Try common formats
        formats = [
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d %I:%M %p",
            "%m/%d/%Y %H:%M",
            "%m/%d/%Y %I:%M %p"
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(time_str, fmt)
            except:
                continue
        
        # Handle relative times
        if "in" in time_str.lower():
            match = re.search(r'in (\d+) (minute|hour|day)s?', time_str.lower())
            if match:
                amount = int(match.group(1))
                unit = match.group(2)
                
                if unit == "minute":
                    return datetime.now() + timedelta(minutes=amount)
                elif unit == "hour":
                    return datetime.now() + timedelta(hours=amount)
                elif unit == "day":
                    return datetime.now() + timedelta(days=amount)
        
        raise ValueError(f"Could not parse time: {time_str}")
