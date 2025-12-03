from src.core.logger_config import get_logger

logger = get_logger(__name__)
"""
Continuous listener with automatic speech detection
"""

import sounddevice as sd
import numpy as np
import wave
import time
from src.utils.vad_detector import VADDetector
from src.utils.config import SAMPLE_RATE, RECORDINGS_DIR, TEMP_AUDIO_FILE
import os

class ContinuousListener:
    def __init__(self, sample_rate=SAMPLE_RATE):
        """
        Initialize continuous listener with VAD
        
        Args:
            sample_rate: Audio sample rate
        """
        self.sample_rate = sample_rate
        self.vad = VADDetector(sample_rate=sample_rate)
        self.is_recording = False
        self.audio_chunks = []
        
        # Ensure recordings directory exists
        os.makedirs(RECORDINGS_DIR, exist_ok=True)
    
    def calibrate_vad(self, duration=2.0):
        """
        Calibrate VAD by measuring ambient noise
        
        Args:
            duration: Calibration duration in seconds
        """
        logger.info(f"Calibrating VAD... (measuring ambient noise for {duration}s)")
        logger.info("   Please stay quiet...")
        
        # Record ambient noise
        recording = sd.rec(
            int(duration * self.sample_rate),
            samplerate=self.sample_rate,
            channels=1,
            dtype='int16'
        )
        sd.wait()
        
        # Auto-adjust threshold
        self.vad.auto_adjust_threshold(recording.flatten())
        logger.info("VAD calibrated!")
    
    def record_with_vad(self, max_duration=5.0, pre_speech_buffer=0.5):
        """
        Record audio with automatic speech detection
        
        Args:
            max_duration: Maximum recording duration in seconds
            pre_speech_buffer: Duration to keep before speech starts (seconds)
            
        Returns:
            Path to saved audio file or None
        """
        logger.info("Listening for speech...")
        
        chunk_duration = 0.1  # 100ms chunks
        chunk_samples = int(self.sample_rate * chunk_duration)
        max_chunks = int(max_duration / chunk_duration)
        
        audio_buffer = []
        speech_detected = False
        speech_chunks = []
        silence_count = 0
        max_silence_chunks = int(self.vad.silence_duration / chunk_duration)
        
        # Pre-speech buffer size
        pre_buffer_size = int(pre_speech_buffer / chunk_duration)
        
        try:
            with sd.InputStream(samplerate=self.sample_rate,
                               channels=1,
                               dtype='int16') as stream:
                
                for i in range(max_chunks):
                    # Read audio chunk
                    chunk, overflowed = stream.read(chunk_samples)
                    
                    if overflowed:
                        logger.info("Audio overflow detected")
                    
                    # Add to circular buffer
                    audio_buffer.append(chunk)
                    if len(audio_buffer) > pre_buffer_size:
                        audio_buffer.pop(0)
                    
                    # Check for speech
                    is_speech = self.vad.is_speech(chunk.flatten())
                    
                    if not speech_detected and is_speech:
                        # Speech started!
                        speech_detected = True
                        logger.info("Speech detected!")
                        
                        # Add pre-speech buffer to recording
                        speech_chunks.extend(audio_buffer)
                        audio_buffer = []
                        
                    elif not speech_detected:
                        # We are in silence/noise before speech
                        # Adaptively calibrate to this background noise
                        self.vad.adapt_threshold(chunk.flatten())
                    
                    if speech_detected:
                        speech_chunks.append(chunk)
                        
                        # Show progress
                        if len(speech_chunks) % 10 == 0:
                            print(".", end="", flush=True)
                        
                        if not is_speech:
                            silence_count += 1
                        else:
                            silence_count = 0
                        
                        # Check if speech ended (continuous silence)
                        if silence_count >= max_silence_chunks:
                            logger.info("\nSpeech ended (silence detected)")
                            break
                
                # Check if we recorded anything
                if not speech_chunks:
                    logger.info("No speech detected")
                    return None
                
                # Concatenate all chunks
                audio_data = np.concatenate(speech_chunks, axis=0)
                
                # Save to file
                filename = TEMP_AUDIO_FILE
                with wave.open(filename, 'wb') as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)  # 16-bit
                    wf.setframerate(self.sample_rate)
                    wf.writeframes(audio_data.tobytes())
                
                duration = len(audio_data) / self.sample_rate
                logger.info(f"Recorded {duration:.1f}s of audio")
                
                return filename
        
        except KeyboardInterrupt:
            logger.info("\nRecording interrupted")
            return None
        except Exception as e:
            logger.error(f"Recording error: {e}")
            return None
    
    def record_fixed_duration(self, duration=5.0):
        """
        Record for a fixed duration (fallback method)
        
        Args:
            duration: Recording duration in seconds
            
        Returns:
            Path to saved audio file
        """
        logger.info(f"Recording for {duration}s...")
        
        recording = sd.rec(
            int(duration * self.sample_rate),
            samplerate=self.sample_rate,
            channels=1,
            dtype='int16'
        )
        sd.wait()
        
        # Save to file
        filename = TEMP_AUDIO_FILE
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes(recording.tobytes())
        
        logger.info("Recording complete")
        return filename

if __name__ == "__main__":
    # Test continuous listener
    logger.info("Continuous Listener Test\n")
    
    listener = ContinuousListener()
    
    # Calibrate
    input("Press Enter to calibrate VAD (stay quiet)...")
    listener.calibrate_vad(duration=2)
    
    # Test recording
    input("\nPress Enter to start recording with VAD...")
    logger.info("Speak something and then stay quiet to auto-stop...\n")
    
    audio_file = listener.record_with_vad(max_duration=10)
    
    if audio_file:
        logger.info(f"\nTest successful! Audio saved to: {audio_file}")
        logger.info("You can now use this with speech_to_text.py to transcribe")
    else:
        logger.error("\nTest failed!")
