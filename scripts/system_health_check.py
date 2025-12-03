
import sys
import os
import time
import json
import asyncio
import threading
from colorama import init, Fore, Style

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Initialize colorama
init(autoreset=True)

def print_status(component, status, message=""):
    log_line = f"[{status}] {component:<20} {message}"
    
    # Print to console with color
    if status == "PASS":
        print(f"{Fore.GREEN}[PASS] {component:<20} {message}")
    elif status == "FAIL":
        print(f"{Fore.RED}[FAIL] {component:<20} {message}")
    elif status == "WARN":
        print(f"{Fore.YELLOW}[WARN] {component:<20} {message}")
    else:
        print(f"{Fore.CYAN}[INFO] {component:<20} {message}")
        
    # Write to file
    with open("system_check_report.txt", "a", encoding="utf-8") as f:
        f.write(log_line + "\n")

def check_environment():
    # Clear log file
    with open("system_check_report.txt", "w", encoding="utf-8") as f:
        f.write("SYSTEM HEALTH CHECK REPORT\n==========================\n")

    print_status("Environment", "INFO", "Checking Python environment...")
    try:
        import numpy
        import sounddevice
        import vosk
        import faster_whisper
        import edge_tts
        import openai
        print_status("Dependencies", "PASS", "Critical packages installed")
    except ImportError as e:
        print_status("Dependencies", "FAIL", f"Missing package: {e}")
        return False
    return True

def check_wake_word():
    print_status("Wake Word", "INFO", "Initializing WakeWordDetector...")
    try:
        from src.modules.wake_word_detector import WakeWordDetector
        # Initialize with dummy wake words to test model loading
        detector = WakeWordDetector(wake_words=["test"])
        print_status("Wake Word", "PASS", "Model loaded successfully (Optimized)")
        return True
    except Exception as e:
        print_status("Wake Word", "FAIL", f"Error: {e}")
        return False

def check_stt():
    print_status("Speech-to-Text", "INFO", "Initializing Whisper Model...")
    try:
        from src.modules.speech_to_text import SpeechToText
        # Initialize model (this might take a moment)
        stt = SpeechToText(model_size="tiny") # Use tiny for quick check
        print_status("Speech-to-Text", "PASS", "Whisper model loaded")
        return True
    except Exception as e:
        print_status("Speech-to-Text", "FAIL", f"Error: {e}")
        return False

def check_tts():
    print_status("Text-to-Speech", "INFO", "Initializing TTS Engine...")
    try:
        from src.modules.tts_engine import TextToSpeech
        tts = TextToSpeech()
        if tts.audio_enabled:
            print_status("Text-to-Speech", "PASS", "Audio output available")
        else:
            print_status("Text-to-Speech", "WARN", "Audio output NOT available (headless?)")
        return True
    except Exception as e:
        print_status("Text-to-Speech", "FAIL", f"Error: {e}")
        return False

def check_memory():
    print_status("Memory Manager", "INFO", "Checking Database Connection...")
    try:
        from src.modules.memory_manager import MemoryManager
        memory = MemoryManager()
        # Try a simple read
        memories = memory.get_all_memories()
        print_status("Memory Manager", "PASS", f"Database connected. {len(memories)} memories found.")
        return True, memory
    except Exception as e:
        print_status("Memory Manager", "FAIL", f"Error: {e}")
        return False, None

def check_llm(memory_manager):
    print_status("LLM Core", "INFO", "Connecting to Ollama...")
    try:
        from src.core.llm_core import LLMCore
        llm = LLMCore(memory_manager)
        
        # Simple ping
        print_status("LLM Core", "INFO", "Sending test prompt...")
        response = llm.client.chat.completions.create(
            model=llm.model,
            messages=[{"role": "user", "content": "Say 'OK' in JSON format: {'status': 'OK'}"}],
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        if "OK" in content:
            print_status("LLM Core", "PASS", f"Ollama responded: {content}")
            return True
        else:
            print_status("LLM Core", "WARN", f"Unexpected response: {content}")
            return True
    except Exception as e:
        print_status("LLM Core", "FAIL", f"Connection failed. Is Ollama running? Error: {e}")
        return False

def main():
    print(f"{Style.BRIGHT}Starting System Health Check...{Style.RESET_ALL}\n")
    
    if not check_environment():
        print("\nSystem Check Aborted due to environment issues.")
        return

    check_wake_word()
    check_stt()
    check_tts()
    
    memory_ok, memory_manager = check_memory()
    
    if memory_ok:
        check_llm(memory_manager)
    else:
        print_status("LLM Core", "WARN", "Skipping LLM check due to Memory failure")

    print(f"\n{Style.BRIGHT}System Check Complete.{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
