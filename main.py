import sys
import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

from speech_to_text import SpeechToText
from command_executor import CommandExecutor
from wake_word_detector import WakeWordDetector
from continuous_listener import ContinuousListener
from feedback_system import FeedbackSystem
from llm_core import LLMCore
from tts_engine import TextToSpeech

class JarvisAgent:
    def __init__(self, use_wake_word=True, feedback_system=None):
        self.feedback = feedback_system if feedback_system else FeedbackSystem()
        self.feedback.print_banner("JARVIS - Agent Mode")
        
        self.feedback.print_status("Init Components...", "info")
        self.stt = SpeechToText()
        self.llm = LLMCore()
        self.executor = CommandExecutor()
        self.listener = ContinuousListener()
        self.tts = TextToSpeech()
        
        self.use_wake_word = use_wake_word
        self.wake_detector = None
        if use_wake_word:
            try:
                self.wake_detector = WakeWordDetector(wake_words=["jarvis", "hey jarvis"])
            except:
                print("Wake word model missing. Run setup_resources.py")
                self.use_wake_word = False
        
        self.feedback.print_status("JARVIS Online", "success")
        self.tts.speak("System online, sir.")

    def process_command(self, audio_file):
        self.feedback.show_thinking()
        transcription = self.stt.transcribe_simple(audio_file)
        
        if not transcription:
            self.feedback.clear_thinking()
            return
        
        self.feedback.print_command(transcription)
        self.feedback.print_status("Thinking...", "info")
        
        # Get decision from Brain
        decision = self.llm.process(transcription)
        self.feedback.clear_thinking()
        
        intent = decision.get("intent", {})
        response_text = decision.get("response", "")
        
        # 1. Execute Action First (to get data)
        result_message = ""
        if intent.get("success") and intent.get("action") != "chat":
            self.feedback.print_action(intent.get("action"), intent.get("target"))
            result = self.executor.execute(intent)
            result_message = result["message"]
            
            # If the user asked for finance data, override the LLM's generic response
            # with the actual data we found in the file.
            if intent.get("action") == "ask_finance":
                response_text = result_message
            
            # Add execution result to LLM history so it remembers what happened
            self.llm.add_entry("system", f"Action executed. Result: {result_message}")

        # 2. Speak Response
        if response_text:
            self.tts.speak(response_text)
        
        if result_message:
            self.feedback.print_status(result_message, "success")

    def run(self):
        if self.use_wake_word:
            self.listener.calibrate_vad(duration=1)
            print(f"\nSay 'Jarvis' to activate...\n")
            try:
                while True:
                    if self.wake_detector.start_listening():
                        self.feedback.activation_beep()
                        self.feedback.print_status("Listening...", "listening")
                        audio_file = self.listener.record_with_vad(max_duration=60)
                        if audio_file: self.process_command(audio_file)
                        self.feedback.print_status("Waiting...", "wake")
            except KeyboardInterrupt: pass
        else:
            while True:
                input("\nPress Enter to speak...")
                self.feedback.print_status("Listening...", "listening")
                audio_file = self.listener.record_with_vad(max_duration=60)
                if audio_file: self.process_command(audio_file)

if __name__ == "__main__":
    jarvis = JarvisAgent(use_wake_word=True)
    jarvis.run()