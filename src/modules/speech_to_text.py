from src.core.logger_config import get_logger

logger = get_logger(__name__)
"""
Speech-to-text module using Faster Whisper
"""

from faster_whisper import WhisperModel
import os
from src.utils.config import (
    WHISPER_MODEL_SIZE, 
    WHISPER_DEVICE, 
    WHISPER_COMPUTE_TYPE,
    LANGUAGE,
    MODELS_DIR
)

class SpeechToText:
    def __init__(
        self, 
        model_size=WHISPER_MODEL_SIZE, 
        device=WHISPER_DEVICE, 
        compute_type=WHISPER_COMPUTE_TYPE
    ):
        """
        Initialize Whisper model for speech-to-text
        
        Args:
            model_size: Model size (tiny, base, small, medium, large)
            device: Device to run on (cpu or cuda)
            compute_type: Computation type (int8, float16, float32)
        """
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.model = None
        
        logger.info(f"\nInitializing Whisper model ({model_size})...")
        logger.info("First-time setup will download model (this may take a moment)...")
        
        try:
            # Create models directory if it doesn't exist
            os.makedirs(MODELS_DIR, exist_ok=True)
            
            # Initialize model
            self.model = WhisperModel(
                model_size,
                device=device,
                compute_type=compute_type,
                download_root=MODELS_DIR
            )
            logger.info("Whisper model loaded successfully!")
            
        except Exception as e:
            logger.error(f"Error loading Whisper model: {e}")
            raise
    
    def transcribe(self, audio_file, language=LANGUAGE, verbose=False):
        """
        Transcribe audio file to text
        
        Args:
            audio_file: Path to audio file
            language: Language code (None for auto-detect)
            verbose: Print detailed segment information
            
        Returns:
            Dictionary with transcription results
        """
        if not os.path.exists(audio_file):
            logger.info(f"Audio file not found: {audio_file}")
            return None
        
        if self.model is None:
            logger.info("Model not initialized!")
            return None
        
        logger.info("\nTranscribing audio...")
        
        try:
            # Transcribe
            segments, info = self.model.transcribe(
                audio_file,
                language=language,
                beam_size=5,
                vad_filter=True,  # Voice activity detection
                vad_parameters=dict(min_silence_duration_ms=500)
            )
            
            # Collect all segments
            transcription_text = ""
            segment_list = []
            
            for segment in segments:
                transcription_text += segment.text + " "
                segment_list.append({
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text
                })
                
                if verbose:
                    logger.info(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")
            
            transcription_text = transcription_text.strip()
            
            # Prepare result
            result = {
                "text": transcription_text,
                "language": info.language,
                "language_probability": info.language_probability,
                "duration": info.duration,
                "segments": segment_list
            }
            
            logger.info("Transcription completed!")
            return result
            
        except Exception as e:
            logger.error(f"Error during transcription: {e}")
            return None
    
    def transcribe_simple(self, audio_file, language=LANGUAGE):
        """
        Simple transcription that returns only the text
        
        Args:
            audio_file: Path to audio file
            language: Language code (None for auto-detect)
            
        Returns:
            Transcribed text string or None if failed
        """
        result = self.transcribe(audio_file, language)
        if result:
            return result["text"]
        return None

if __name__ == "__main__":
    # Test the speech-to-text module
    logger.info("Speech-to-Text Test\n")
    
    # You need to have an audio file to test
    # This will be created by running audio_capture.py first
    test_audio = "recordings/temp_recording.wav"
    
    if not os.path.exists(test_audio):
        logger.info(f"No test audio file found at: {test_audio}")
        logger.info("Run audio_capture.py first to create a test recording.")
    else:
        # Initialize STT
        stt = SpeechToText()
        
        # Transcribe
        result = stt.transcribe(test_audio, verbose=True)
        
        if result:
            logger.info("\n" + "=" * 60)
            logger.info("TRANSCRIPTION RESULT:")
            logger.info("=" * 60)
            logger.info(f"Text: {result['text']}")
            logger.info(f"Language: {result['language']} ({result['language_probability']:.2%} confidence)")
            logger.info(f"Duration: {result['duration']:.2f} seconds")
            logger.info("=" * 60)
        else:
            logger.error("\nTranscription failed!")
