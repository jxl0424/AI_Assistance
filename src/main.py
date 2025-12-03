import sys
import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

from src.modules.speech_to_text import SpeechToText
from src.core.command_executor import CommandExecutor
from src.modules.wake_word_detector import WakeWordDetector
from src.modules.continuous_listener import ContinuousListener
from src.modules.feedback_system import FeedbackSystem
from src.core.llm_core import LLMCore
from src.modules.tts_engine import TextToSpeech
from src.modules.memory_manager import MemoryManager

class JarvisAgent:
    def __init__(self, use_wake_word=True, feedback_system=None, on_amplitude=None):
        self.feedback = feedback_system if feedback_system else FeedbackSystem()
        self.feedback.print_banner("JARVIS - Agent Mode")
        
        self.feedback.print_status("Init Components...", "info")
        self.memory_manager = MemoryManager() # SHARED MEMORY
        self.stt = SpeechToText()
        self.llm = LLMCore(self.memory_manager)
        self.executor = CommandExecutor(self.memory_manager)
        self.listener = ContinuousListener()
        self.tts = TextToSpeech()
        
        self.use_wake_word = use_wake_word
        self.wake_detector = None
        if use_wake_word:
            try:
                self.wake_detector = WakeWordDetector(
                    wake_words=["jarvis", "hey jarvis"],
                    on_amplitude=on_amplitude
                )
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
            
            # Add execution result to LLM history so it remembers what happened
            self.llm.add_entry("system", f"Action executed. Result: {result_message}")
            
            # RE-PROMPT: If the user asked for analysis/advice (implied by certain actions),
            # we should ask the LLM to generate a follow-up response based on the data.
            if intent.get("action") in ["list_reminders", "ask_finance", "analyze_screen", "weather", "smart_search"]:
                # Generate a new response based on the tool output
                follow_up = self.llm.process("Based on this result, please provide a brief summary or advice to the user.")
                if follow_up.get("response"):
                    response_text = follow_up.get("response")
            
            # Special case for ask_finance: if we didn't re-prompt, use the raw result
            elif intent.get("action") == "ask_finance" and not response_text:
                 response_text = result_message

            # If the action was to remember something, update the LLM context immediately
            if intent.get("action") == "remember":
                self.llm.update_memory_context()

        # 2. Speak Response
        if response_text:
            self.tts.speak(response_text)
        
        if result_message:
            self.feedback.print_status(result_message, "success")


    def _handle_reminder_alert(self, reminder):
        """Handle reminder/timer alert"""
        message = f"Reminder: {reminder['text']}"
        print(f"\n[ALERT] {message}")
        
        # Speak the reminder if TTS is available
        try:
            if hasattr(self, 'tts') and self.tts:
                self.tts.speak(message)
        except Exception as e:
            print(f"[TTS Error] {e}")

    def check_startup_tasks(self):
        """Check for tasks/reminders on startup"""
        try:
            # Get upcoming reminders for the next 24 hours
            upcoming = self.executor.reminders.get_upcoming_reminders(hours=24)
            
            if upcoming:
                # Format for LLM
                tasks_str = "\n".join([f"- {r['text']} at {r['time']}" for r in upcoming])
                
                # Ask LLM to summarize
                prompt = f"""
                The user has just started the system. 
                Here are their upcoming tasks for the next 24 hours:
                {tasks_str}
                
                Please provide a brief, friendly greeting and a summary of these tasks. 
                Prioritize the most urgent ones.
                Keep it under 2 sentences.
                """
                
                response = self.llm.process(prompt)
                if response.get("response"):
                    self.tts.speak(response.get("response"))
                    self.feedback.print_status(response.get("response"), "info")
            else:
                # Optional: Just say hello if no tasks
                # self.tts.speak("No upcoming tasks for today, sir.")
                pass
                
        except Exception as e:
            print(f"Error checking startup tasks: {e}")

    def run(self):
        if self.use_wake_word:
            self.listener.calibrate_vad(duration=1)
            print(f"\nSay 'Jarvis' to activate...\n")
            
            # Check for tasks immediately after calibration/startup
            self.check_startup_tasks()
            
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
            # Check for tasks immediately on startup
            self.check_startup_tasks()
            
            while True:
                input("\nPress Enter to speak...")
                self.feedback.print_status("Listening...", "listening")
                audio_file = self.listener.record_with_vad(max_duration=60)
                if audio_file: self.process_command(audio_file)

if __name__ == "__main__":
    # Initialize logging system
    from src.core.logger_config import init_jarvis_logging
    init_jarvis_logging(debug=False)  # Set to True for verbose logging
    

    jarvis = JarvisAgent(use_wake_word=True)
    jarvis.run()