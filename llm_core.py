import json
import os
from openai import OpenAI
try:
    from apps_config import list_available_apps, APPLICATIONS
    INSTALLED_APPS = list(APPLICATIONS.keys())
except ImportError:
    INSTALLED_APPS = ["chrome", "notepad", "calculator"] 

from memory_manager import MemoryManager

class LLMCore:
    def __init__(self):
        self.client = OpenAI(
            base_url="http://localhost:11434/v1",
            api_key="ollama"
        )
        self.model = "llama3.2" 
        self.memory_manager = MemoryManager()
        self.conversation_history = [
            {"role": "system", "content": self._get_system_prompt()}
        ]

    def _get_system_prompt(self):
        apps_str = ", ".join(INSTALLED_APPS)
        memories = self.memory_manager.get_memory_string()
        
        return f"""
        You are JARVIS. Output JSON only.
        
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
        
        7. "chat": General conversation.
        
        RESPONSE FORMAT:
        {{
            "response": "Spoken response to user",
            "intent": {{
                "action": "open|system|search|track_expense|ask_finance|remember|chat",
                "target": "val", "amount": 0, "currency": "$",
                "category": "val", "description": "val", 
                "timeframe": "today|month|all",
                "query": "val", "fact": "val",
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
            print(f"LLM Error: {e}")
            with open("llm_debug_error.txt", "w") as f:
                f.write(str(e))
            return {"response": "Error processing.", "intent": {"success": False}}

    def add_entry(self, role, content):
        """Manually add an entry to conversation history"""
        self.conversation_history.append({"role": role, "content": content})