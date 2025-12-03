import json
import os
from openai import OpenAI
from src.core.logger_config import get_logger
from datetime import datetime

logger = get_logger(__name__)
try:
    from src.utils.apps_config import list_available_apps, APPLICATIONS
    INSTALLED_APPS = list(APPLICATIONS.keys())
except ImportError:
    INSTALLED_APPS = ["chrome", "notepad", "calculator"] 

class LLMCore:
    def __init__(self, memory_manager):
        self.client = OpenAI(
            base_url="http://localhost:11434/v1",
            api_key="ollama"
        )
        self.model = "llama3.2" 
        self.memory_manager = memory_manager
        self.conversation_history = [
            {"role": "system", "content": self._get_system_prompt()}
        ]

    def update_memory_context(self):
        """Update the system prompt with latest memories"""
        self.conversation_history[0] = {"role": "system", "content": self._get_system_prompt()}

    def _get_system_prompt(self):
        apps_str = ", ".join(INSTALLED_APPS)
        memories = self.memory_manager.get_memory_string()
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        day_of_week = datetime.now().strftime("%A")
        
        return f"""
        You are JARVIS. Output JSON only.
        
        CURRENT DATE AND TIME: {current_time} ({day_of_week})
        
        USER MEMORY (Facts you know about the user):
        {memories}
        
        AVAILABLE ACTIONS:
        1. "open": Open app (target: {apps_str})
        2. "system": volume_up, volume_down, mute, screenshot
        3. "search": Web search (query)
        
        4. "track_expense": Log spending.
           - User: "Spent $50 on food"
           - Params: amount, currency, category, description
        
        5. "ask_finance": Analyze spending.
           - User: "How much did I spend on food?" or "Total spending today"
           - Params: 
             * category (optional string, e.g. "food")
             * timeframe (enum: "today", "month", "all")
             
        6. "remember": Store a fact about the user.
           - User: "My name is Brendan" or "I like coding"
           - Params: fact (string)
           
        7. "weather": Get weather.
           - User: "Weather in Tokyo"
           - Params: target (city name, default "Singapore")
           
        8. "smart_search": Search web for answer.
           - User: "Who is the president of France?" or "Stock price of NVDA"
           - Params: query (string)
        
        9. "set_reminder": Set a reminder.
           - User: "Remind me to call John at 3pm" or "Remind me to exercise tomorrow at 7am"
           - Params: 
             * text (string, what to remind)
             * time (string, when to remind in format "YYYY-MM-DD HH:MM")
             * recurring (optional: "daily", "weekly", "monthly")
        
        10. "set_timer": Set a countdown timer.
            - User: "Set a timer for 10 minutes" or "Timer for 30 minutes"
            - Params: 
              * duration_minutes (number)
              * label (optional string, default "Timer")
        
        11. "list_reminders": List all active reminders.
            - User: "What are my reminders?" or "Show my reminders"
            - No params needed
        
        12. "chat": General conversation.
        
        13. "analyze_screen": See what is on the user's screen.
            - User: "What is on my screen?" or "Explain this error" or "Summarize this text"
            - Params: query (string, what to look for)
        
        RESPONSE FORMAT:
        {{
            "response": "Spoken response to user",
            "intent": {{
                "action": "open|system|search|track_expense|ask_finance|remember|weather|smart_search|set_reminder|set_timer|list_reminders|analyze_screen|chat",
                "target": "val", "amount": 0, "currency": "$",
                "category": "val", "description": "val", 
                "timeframe": "today|month|all",
                "query": "val", "fact": "val",
                "text": "val", "time": "YYYY-MM-DD HH:MM", "recurring": "daily|weekly|monthly",
                "duration_minutes": 0, "label": "val",
                "success": true
            }}
        }}
        """

    def process(self, user_text):
        self.conversation_history.append({"role": "user", "content": user_text})
        if len(self.conversation_history) > 10:
            self.conversation_history = [self.conversation_history[0]] + self.conversation_history[-5:]

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=self.conversation_history,
                response_format={"type": "json_object"},
                temperature=0.1
            )
            response_content = completion.choices[0].message.content
            self.conversation_history.append({"role": "assistant", "content": response_content})
            
            try:
                return json.loads(response_content)
            except json.JSONDecodeError:
                clean = response_content.replace("```json", "").replace("```", "").strip()
                return json.loads(clean)
        except Exception as e:
            logger.error(f"LLM Error: {e}")
            with open("llm_debug_error.txt", "w") as f:
                f.write(str(e))
            return {"response": "Error processing.", "intent": {"success": False}}

    def add_entry(self, role, content):
        """Manually add an entry to conversation history"""
        self.conversation_history.append({"role": role, "content": content})