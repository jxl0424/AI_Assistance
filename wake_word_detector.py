"""
Wake word detection using Vosk
"""

import json
import queue
import sounddevice as sd
import vosk
import os
import time

class WakeWordDetector:
    def __init__(self, 
                 wake_words=["jarvis", "hey jarvis"],
                 model_path=None,
                 sample_rate=16000):
        """
        Initialize wake word detector with Vosk
        
        Args:
            wake_words: List of wake words to detect
            model_path: Path to Vosk model (will auto-download if not provided)
            sample_rate: Audio sample rate
        """
        self.wake_words = [w.lower() for w in wake_words]
        self.sample_rate = sample_rate
        self.audio_queue = queue.Queue()
        self.is_listening = False
        
        # Initialize Vosk model
        print("Loading Vosk model for wake word detection...")
        
        if model_path and os.path.exists(model_path):
            self.model = vosk.Model(model_path)
        else:
            # Try to find model in common locations
            possible_paths = [
                "models/vosk-model-small-en-us-0.15",
                "../models/vosk-model-small-en-us-0.15",
            ]
            
            model_found = False
            for path in possible_paths:
                if os.path.exists(path):
                    self.model = vosk.Model(path)
                    model_found = True
                    print(f"Loaded model from: {path}")
                    break
            
            if not model_found:
                print("Vosk model not found!")
                print("Download a model from: https://alphacephei.com/vosk/models")
                print("   Recommended: vosk-model-small-en-us-0.15 (~40MB)")
                print("   Extract to: models/vosk-model-small-en-us-0.15/")
                raise FileNotFoundError("Vosk model not found")
        
        self.recognizer = vosk.KaldiRecognizer(self.model, sample_rate)
        self.recognizer.SetWords(True)
        
        print("Wake word detector ready!")
        print(f"Listening for: {', '.join(self.wake_words)}")
    
    def audio_callback(self, indata, frames, time, status):
        """Callback for audio stream"""
        if status:
            print(f"Audio status: {status}")
        self.audio_queue.put(bytes(indata))
    
    def start_listening(self):
        """Start listening for wake word"""
        self.is_listening = True
        
        with sd.RawInputStream(samplerate=self.sample_rate, 
                              blocksize=2000,
                              dtype='int16',
                              channels=1,
                              callback=self.audio_callback):
            
            print("\nListening for wake word...")
            print(f"Say: '{self.wake_words[0]}' to activate\n")
            
            while self.is_listening:
                try:
                    data = self.audio_queue.get(timeout=1)
                    
                    if self.recognizer.AcceptWaveform(data):
                        result = json.loads(self.recognizer.Result())
                        text = result.get('text', '').lower()
                        
                        if text:
                            # Check if any wake word is in the text
                            for wake_word in self.wake_words:
                                if wake_word in text:
                                    print(f"\nWake word detected: '{text}'")
                                    return True
                    
                except queue.Empty:
                    continue
                except KeyboardInterrupt:
                    print("\nWake word detection stopped")
                    self.is_listening = False
                    return False
        
        return False
    
    def stop_listening(self):
        """Stop listening for wake word"""
        self.is_listening = False
    
    def listen_once(self, timeout=None):
        """
        Listen for wake word once (non-blocking)
        
        Args:
            timeout: Timeout in seconds (None for infinite)
            
        Returns:
            True if wake word detected, False otherwise
        """
        start_time = None
        if timeout:
            start_time = time.time()
        
        self.is_listening = True
        detected = False
        
        try:
            with sd.RawInputStream(samplerate=self.sample_rate,
                                  blocksize=2000,
                                  dtype='int16',
                                  channels=1,
                                  callback=self.audio_callback):
                
                while self.is_listening:
                    # Check timeout
                    if timeout and start_time:
                        if time.time() - start_time > timeout:
                            break
                    
                    try:
                        data = self.audio_queue.get(timeout=0.1)
                        
                        if self.recognizer.AcceptWaveform(data):
                            result = json.loads(self.recognizer.Result())
                            text = result.get('text', '').lower()
                            
                            if text:
                                for wake_word in self.wake_words:
                                    if wake_word in text:
                                        detected = True
                                        self.is_listening = False
                                        break
                    
                    except queue.Empty:
                        continue
        
        except KeyboardInterrupt:
            self.is_listening = False
        
        return detected

if __name__ == "__main__":
    # Test wake word detector
    print("Wake Word Detector Test\n")
    
    try:
        detector = WakeWordDetector(wake_words=["jarvis", "hey jarvis"])
        
        print("\nStarting wake word detection...")
        print("Say 'Jarvis' or 'Hey Jarvis' to test")
        print("Press Ctrl+C to stop\n")
        
        detected = detector.start_listening()
        
        if detected:
            print("Wake word detection successful!")
        else:
            print("Wake word detection stopped")
    
    except FileNotFoundError as e:
        print(f"\nError: {e}")
    except KeyboardInterrupt:
        print("\n\nTest interrupted")
