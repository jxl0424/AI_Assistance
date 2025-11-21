import pyttsx3
import threading
import sys

class TextToSpeech:
    def __init__(self):
        self.error_logged = False
        try:
            # Test initialization immediately to catch errors early
            test_engine = pyttsx3.init()
            voices = test_engine.getProperty('voices')
            if not voices:
                print("⚠️ TTS Warning: No voices detected on system.")
            del test_engine
        except Exception as e:
            print(f"❌ TTS Initialization Failed: {e}")
            self.error_logged = True

    def speak(self, text):
        """
        Speaks text in a non-blocking way.
        """
        if not text:
            return

        # Print to console so you can read it even if audio fails
        print(f"\n🗣️ JARVIS: {text}\n")
        
        if self.error_logged:
            return

        # Run in a separate thread so the agent keeps listening/working
        thread = threading.Thread(target=self._speak_thread, args=(text,))
        thread.start()

    def _speak_thread(self, text):
        try:
            # Initialize a fresh engine instance for this thread
            # This prevents "COM" errors on Windows
            engine = pyttsx3.init()
            
            # Set properties (optional)
            engine.setProperty('rate', 160) 
            
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            print(f"❌ Audio Error: {e}")