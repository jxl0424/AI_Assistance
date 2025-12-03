from src.core.logger_config import get_logger

logger = get_logger(__name__)
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
                 sample_rate=16000,
                 on_amplitude=None):
        """
        Initialize wake word detector with Vosk
        
        Args:
            wake_words: List of wake words to detect
            model_path: Path to Vosk model (will auto-download if not provided)
            wake_words: List of wake words to detect
            model_path: Path to Vosk model (will auto-download if not provided)
            sample_rate: Audio sample rate
            on_amplitude: Callback function for audio amplitude (0-100)
        """
        self.wake_words = [w.lower() for w in wake_words]
        self.sample_rate = sample_rate
        self.audio_queue = queue.Queue()
        self.is_listening = False
        self.on_amplitude = on_amplitude
        
        # Initialize Vosk model
        logger.info("Loading Vosk model for wake word detection...")
        
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
                    logger.info(f"Loaded model from: {path}")
                    break
            
            if not model_found:
                logger.info("Vosk model not found!")
                logger.info("Download a model from: https://alphacephei.com/vosk/models")
                logger.info("   Recommended: vosk-model-small-en-us-0.15 (~40MB)")
                logger.info("   Extract to: models/vosk-model-small-en-us-0.15/")
                raise FileNotFoundError("Vosk model not found")
        
        self.recognizer = vosk.KaldiRecognizer(self.model, sample_rate)
        
        # OPTIMIZATION: Restrict grammar to specific wake words
        # This forces the recognizer to only listen for these words, 
        # significantly reducing latency and CPU usage compared to full ASR.
        try:
            # Extract unique words from phrases (e.g. "hey jarvis" -> "hey", "jarvis")
            unique_words = set()
            for phrase in self.wake_words:
                unique_words.update(phrase.split())
            
            # Add [unk] for unknown words to prevent forcing matches
            grammar_list = list(unique_words) + ["[unk]"]
            grammar_json = json.dumps(grammar_list)
            
            logger.info(f"Optimizing detection with grammar: {grammar_list}")
            self.recognizer = vosk.KaldiRecognizer(self.model, sample_rate, grammar_json)
        except Exception as e:
            logger.warning(f"Failed to set grammar (using full vocabulary): {e}")
            self.recognizer = vosk.KaldiRecognizer(self.model, sample_rate)

        self.recognizer.SetWords(True)
        
        logger.info("Wake word detector ready!")
        logger.info(f"Listening for: {', '.join(self.wake_words)}")
    
    def audio_callback(self, indata, frames, time, status):
        """Callback for audio stream"""
        if status:
            logger.info(f"Audio status: {status}")
        
        # Check if microphone is muted (very low amplitude)
        import numpy as np
        amplitude = np.max(np.abs(np.frombuffer(indata, dtype=np.int16)))
        
        # Call amplitude callback for visualizer
        if self.on_amplitude:
            # Normalize to 0-100 range (approximate)
            # Max 16-bit int is 32768, but speech is usually lower
            norm_amp = min(100, int((amplitude / 5000) * 100))
            self.on_amplitude(norm_amp)
        
        # If amplitude is consistently very low, mic might be muted
        if amplitude < 10:  # Very quiet threshold
            # Don't add to queue if mic is muted
            return
            
        self.audio_queue.put(bytes(indata))
    
    def start_listening(self):
        """Start listening for wake word"""
        self.is_listening = True
        
        with sd.RawInputStream(samplerate=self.sample_rate, 
                              blocksize=2000,
                              dtype='int16',
                              channels=1,
                              callback=self.audio_callback):
            
            logger.info("\nListening for wake word...")
            logger.info(f"Say: '{self.wake_words[0]}' to activate\n")
            
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
                                    logger.info(f"\nWake word detected: '{text}'")
                                    return True
                    
                except queue.Empty:
                    continue
                except KeyboardInterrupt:
                    logger.info("\nWake word detection stopped")
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
    logger.info("Wake Word Detector Test\n")
    
    try:
        detector = WakeWordDetector(wake_words=["jarvis", "hey jarvis"])
        
        logger.info("\nStarting wake word detection...")
        logger.info("Say 'Jarvis' or 'Hey Jarvis' to test")
        logger.info("Press Ctrl+C to stop\n")
        
        detected = detector.start_listening()
        
        if detected:
            logger.info("Wake word detection successful!")
        else:
            logger.info("Wake word detection stopped")
    
    except FileNotFoundError as e:
        logger.error(f"\nError: {e}")
    except KeyboardInterrupt:
        logger.info("\n\nTest interrupted")
