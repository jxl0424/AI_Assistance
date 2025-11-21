import json
import os

MEMORY_FILE = "memory.json"

class MemoryManager:
    def __init__(self):
        self.file_path = MEMORY_FILE
        self.memories = self._load_memories()

    def _load_memories(self):
        if not os.path.exists(self.file_path):
            return []
        try:
            with open(self.file_path, "r") as f:
                return json.load(f)
        except:
            return []

    def save_memories(self):
        with open(self.file_path, "w") as f:
            json.dump(self.memories, f, indent=4)

    def add_memory(self, text):
        """Add a new fact to memory if it doesn't exist"""
        if text not in self.memories:
            self.memories.append(text)
            self.save_memories()
            return True
        return False

    def get_all_memories(self):
        return self.memories

    def get_memory_string(self):
        """Returns a formatted string of all memories for the LLM prompt"""
        if not self.memories:
            return "No known facts yet."
        return "\n".join([f"- {mem}" for mem in self.memories])
