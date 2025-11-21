import edge_tts
import pygame
import asyncio
import threading
import os
import tempfile
import time

class TextToSpeech:
    def __init__(self):
        # Voice options: 
        # en-GB-RyanNeural (Jarvis-like)
        # en-US-ChristopherNeural (American male)
        # en-US-AriaNeural (American female)
        self.voice = "en-GB-RyanNeural" 
        
        try:
            pygame.mixer.init()
            self.audio_enabled = True
        except Exception as e:
            print(f"⚠️ Audio output not available: {e}")
            self.audio_enabled = False

    def speak(self, text):
        """
        Speaks text using Edge TTS (Online, High Quality)
        """
        if not text: return
        
        print(f"\n🗣️ JARVIS: {text}\n")
        
        if not self.audio_enabled: return

        # Run in separate thread to avoid blocking
        threading.Thread(target=self._run_speak, args=(text,)).start()

    def _run_speak(self, text):
        try:
            # Create a unique temp file for this utterance to avoid conflicts
            # timestamp to ensure uniqueness
            filename = f"jarvis_speech_{int(time.time()*1000)}.mp3"
            temp_file = os.path.join(tempfile.gettempdir(), filename)
            
            # Generate audio (needs asyncio loop)
            asyncio.run(self._generate_audio(text, temp_file))
            
            # Play audio
            self._play_audio(temp_file)
            
            # Cleanup
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except:
                pass
                
        except Exception as e:
            print(f"❌ TTS Error: {e}")

    async def _generate_audio(self, text, output_file):
        communicate = edge_tts.Communicate(text, self.voice)
        await communicate.save(output_file)

    def _play_audio(self, file_path):
        try:
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            
            # Wait for playback to finish
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
                
            pygame.mixer.music.unload()
        except Exception as e:
            print(f"❌ Audio Playback Error: {e}")

if __name__ == "__main__":
    # Test
    tts = TextToSpeech()
    tts.speak("System upgrade complete. Voice module online.")
    # Keep main thread alive to hear audio
    time.sleep(5)