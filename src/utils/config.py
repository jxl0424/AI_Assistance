"""
Configuration file for voice agent settings
"""

# Audio Recording Settings
SAMPLE_RATE = 16000  # Whisper works best with 16kHz
CHANNELS = 1  # Mono audio
DTYPE = 'int16'  # 16-bit audio
CHUNK_SIZE = 1024  # Buffer size for recording

# Whisper Model Settings
WHISPER_MODEL_SIZE = "tiny"  # Options: tiny, base, small, medium, large
WHISPER_DEVICE = "cpu"  # Options: cpu, cuda
WHISPER_COMPUTE_TYPE = "int8"  # Options: int8, float16, float32

# File Paths
RECORDINGS_DIR = "recordings"
MODELS_DIR = "models"
TEMP_AUDIO_FILE = f"{RECORDINGS_DIR}/temp_recording.wav"

# Language Settings
LANGUAGE = None  # None for auto-detect, or specify like "en", "es", etc.

# Recording Settings
DEFAULT_RECORD_DURATION = 5  # seconds (if using fixed duration)
SILENCE_THRESHOLD = 500  # Amplitude threshold for silence detection (optional)
