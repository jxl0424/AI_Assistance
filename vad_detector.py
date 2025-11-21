"""
Voice Activity Detection (VAD) - Detect when user starts/stops speaking
"""

import numpy as np
import time

class VADDetector:
    def __init__(self, 
                 sample_rate=16000,
                 frame_duration=0.03,  # 30ms frames
                 energy_threshold=500,
                 silence_duration=1.2):  # seconds of silence to stop
        """
        Initialize VAD detector
        
        Args:
            sample_rate: Audio sample rate
            frame_duration: Duration of each frame in seconds
            energy_threshold: Energy threshold for speech detection
            silence_duration: Duration of silence before stopping
        """
        self.sample_rate = sample_rate
        self.frame_duration = frame_duration
        self.frame_size = int(sample_rate * frame_duration)
        self.energy_threshold = energy_threshold
        self.silence_duration = silence_duration
    
    def calculate_energy(self, audio_frame):
        """
        Calculate energy of audio frame
        
        Args:
            audio_frame: Audio data array
            
        Returns:
            Energy value
        """
        return np.sum(np.abs(audio_frame))
    
    def is_speech(self, audio_frame):
        """
        Check if audio frame contains speech
        
        Args:
            audio_frame: Audio data array
            
        Returns:
            True if speech detected, False otherwise
        """
        energy = self.calculate_energy(audio_frame)
        return energy > self.energy_threshold
    
    def detect_speech_end(self, audio_chunks):
        """
        Detect when user stops speaking
        
        Args:
            audio_chunks: List of audio chunks
            
        Returns:
            True if speech has ended, False otherwise
        """
        if len(audio_chunks) < 2:
            return False
        
        # Check last N chunks for silence
        num_chunks_to_check = int(self.silence_duration / self.frame_duration)
        recent_chunks = audio_chunks[-num_chunks_to_check:]
        
        # Count silent chunks
        silent_count = 0
        for chunk in recent_chunks:
            if not self.is_speech(chunk):
                silent_count += 1
        
        # If most recent chunks are silent, speech has ended
        silence_ratio = silent_count / len(recent_chunks)
        return silence_ratio > 0.8  # 80% of chunks are silent
    
    def auto_adjust_threshold(self, audio_samples, percentile=90):
        """
        Auto-adjust energy threshold based on ambient noise
        
        Args:
            audio_samples: Audio data to analyze
            percentile: Percentile for threshold
        """
        energies = []
        for i in range(0, len(audio_samples) - self.frame_size, self.frame_size):
            frame = audio_samples[i:i + self.frame_size]
            energies.append(self.calculate_energy(frame))
        
        if energies:
            self.energy_threshold = np.percentile(energies, percentile)
            print(f"🔧 Auto-adjusted VAD threshold to: {self.energy_threshold:.0f}")

if __name__ == "__main__":
    # Test VAD
    print("🎙️ VAD Detector Test\n")
    
    vad = VADDetector()
    print(f"Energy Threshold: {vad.energy_threshold}")
    print(f"Silence Duration: {vad.silence_duration}s")
    print(f"Frame Size: {vad.frame_size} samples")
