"""
Command executor - Execute system commands based on intents
"""

import subprocess
import os
import psutil
import time
from apps_config import find_application_path, APPLICATIONS
from finance_manager import FinanceManager
from memory_manager import MemoryManager
from tools_manager import ToolsManager  # IMPORT TOOLS

class CommandExecutor:
    def __init__(self, memory_manager):
        """Initialize command executor"""
        self.running_processes = {}
        self.finance = FinanceManager()
        self.memory = memory_manager
        self.tools = ToolsManager() # INIT TOOLS
    
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
            
        # NEW: Smart Search Handler
        elif action == "smart_search":
            return {"success": True, "message": self.tools.search_web(query)}
            
        else:
            return {
                "success": True, # It was likely just chat
                "message": "Conversation processed"
            }
    
    def _open_application(self, app_name, query=None):
        """Open an application"""
        print(f"Opening {app_name}...")
        
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