
import pyautogui
import base64
import io
import os
from src.core.logger_config import get_logger
from openai import OpenAI

logger = get_logger(__name__)

class VisionManager:
    def __init__(self):
        self.client = OpenAI(
            base_url="http://localhost:11434/v1",
            api_key="ollama"
        )
        # Default to llava for vision, fall back to user's choice if needed
        self.model = "llava" 

    def capture_screen(self):
        """Capture screenshot and return as base64 string"""
        try:
            # Capture full screen
            screenshot = pyautogui.screenshot()
            
            # Convert to bytes
            buffered = io.BytesIO()
            screenshot.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
            
            return img_str
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            return None

    def analyze_screen(self, query="Describe what is on my screen"):
        """Analyze the current screen content"""
        logger.info(f"Analyzing screen with query: {query}")
        
        image_data = self.capture_screen()
        if not image_data:
            return "Failed to capture screen."

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": query},
                            {
                                "type": "image_url",
                                "image_url": f"data:image/png;base64,{image_data}"
                            }
                        ]
                    }
                ],
                max_tokens=300
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            error_msg = str(e)
            if "model" in error_msg and "not found" in error_msg:
                return "Vision model 'llava' not found. Please run: 'ollama pull llava'"
            
            logger.error(f"Vision analysis failed: {e}")
            return f"Error analyzing screen: {e}"

if __name__ == "__main__":
    # Test
    vision = VisionManager()
    print(vision.analyze_screen("What do you see?"))
