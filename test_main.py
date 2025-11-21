
import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

# Mock dependencies that might be missing
sys.modules['faster_whisper'] = MagicMock()
sys.modules['sounddevice'] = MagicMock()
sys.modules['numpy'] = MagicMock()
sys.modules['pvporcupine'] = MagicMock()
sys.modules['pyaudio'] = MagicMock()
sys.modules['pyttsx3'] = MagicMock()
sys.modules['openai'] = MagicMock()
sys.modules['vosk'] = MagicMock()

from main import JarvisAgent

class TestJarvisAgent(unittest.TestCase):
    @patch('main.SpeechToText')
    @patch('main.CommandExecutor')
    @patch('main.WakeWordDetector')
    @patch('main.ContinuousListener')
    @patch('main.FeedbackSystem')
    @patch('main.LLMCore')
    @patch('main.TextToSpeech')
    def setUp(self, MockTTS, MockLLM, MockFeedback, MockListener, MockWake, MockExecutor, MockSTT):
        self.mock_tts = MockTTS.return_value
        self.mock_llm = MockLLM.return_value
        self.mock_feedback = MockFeedback.return_value
        self.mock_listener = MockListener.return_value
        self.mock_wake = MockWake.return_value
        self.mock_executor = MockExecutor.return_value
        self.mock_stt = MockSTT.return_value
        
        self.agent = JarvisAgent(use_wake_word=True)

    def test_init(self):
        """Test initialization"""
        self.mock_feedback.print_banner.assert_called()
        self.mock_tts.speak.assert_called_with("System online, sir.")

    def test_process_command_chat(self):
        """Test processing a simple chat command"""
        # Setup mocks
        self.mock_stt.transcribe_simple.return_value = "Hello Jarvis"
        self.mock_llm.process.return_value = {
            "intent": {"success": True, "action": "chat"},
            "response": "Hello sir"
        }
        self.mock_executor.execute.return_value = {
            "success": True,
            "message": "Conversation processed"
        }
        
        # Run
        self.agent.process_command("dummy_audio.wav")
        
        # Verify
        self.mock_stt.transcribe_simple.assert_called_with("dummy_audio.wav")
        self.mock_llm.process.assert_called()
        # Executor should NOT be called for chat if logic is correct? 
        # Let's check main.py: 
        # if intent.get("success") and intent.get("action") != "chat":
        #     self.executor.execute(intent)
        self.mock_executor.execute.assert_not_called()
        self.mock_tts.speak.assert_called_with("Hello sir")

    def test_process_command_open_app(self):
        """Test processing an open app command"""
        self.mock_stt.transcribe_simple.return_value = "Open calculator"
        self.mock_llm.process.return_value = {
            "intent": {"success": True, "action": "open", "target": "calculator"},
            "response": "Opening calculator"
        }
        self.mock_executor.execute.return_value = {
            "success": True,
            "message": "Opened calculator"
        }
        
        self.agent.process_command("dummy_audio.wav")
        
        self.mock_executor.execute.assert_called()
        self.mock_tts.speak.assert_called_with("Opening calculator")
        self.mock_feedback.print_status.assert_called_with("Opened calculator", "success")

    def test_process_command_ask_finance(self):
        """Test processing ask_finance command"""
        self.mock_stt.transcribe_simple.return_value = "How much did I spend?"
        self.mock_llm.process.return_value = {
            "intent": {"success": True, "action": "ask_finance", "timeframe": "today"},
            "response": "Checking finance..." # LLM placeholder
        }
        # Mocking what the executor SHOULD return if it was working, 
        # or what it DOES return to verify main.py logic handling the result.
        
        # If executor returns a message, main.py should use it.
        self.mock_executor.execute.return_value = {
            "success": True,
            "message": "You spent $50 today."
        }
        
        self.agent.process_command("dummy_audio.wav")
        
        self.mock_executor.execute.assert_called()
        # main.py logic:
        # if intent.get("action") == "ask_finance":
        #     response_text = result_message
        self.mock_tts.speak.assert_called_with("You spent $50 today.")

if __name__ == '__main__':
    unittest.main()
