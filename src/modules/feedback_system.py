from src.core.logger_config import get_logger

logger = get_logger(__name__)
"""
Feedback system - Audio and visual feedback for user interactions
"""

import numpy as np
import sounddevice as sd
import sys
from colorama import init, Fore, Style

# Initialize colorama for colored terminal output
init(autoreset=True)

class FeedbackSystem:
    def __init__(self, sample_rate=16000):
        """
        Initialize feedback system
        
        Args:
            sample_rate: Audio sample rate for beeps
        """
        self.sample_rate = sample_rate
    
    def play_beep(self, frequency=1000, duration=0.1, volume=0.3, blocking=True):
        """
        Play a beep sound
        
        Args:
            frequency: Frequency in Hz
            duration: Duration in seconds
            volume: Volume (0.0 to 1.0)
        """
        try:
            # Generate sine wave
            t = np.linspace(0, duration, int(self.sample_rate * duration))
            wave = volume * np.sin(2 * np.pi * frequency * t)
            
            # Play sound
            sd.play(wave.astype(np.float32), self.sample_rate)
            if blocking:
                sd.wait()
        except Exception as e:
            # Silent fail if audio playback fails
            pass
    
    def activation_beep(self, blocking=False):
        """Play activation beep (wake word detected)"""
        self.play_beep(frequency=800, duration=0.1, volume=0.3, blocking=blocking)
    
    def success_beep(self):
        """Play success beep (command executed)"""
        # Two quick beeps
        self.play_beep(frequency=1000, duration=0.08, volume=0.2)
        self.play_beep(frequency=1200, duration=0.08, volume=0.2)
    
    def error_beep(self):
        """Play error beep (command failed)"""
        self.play_beep(frequency=400, duration=0.2, volume=0.3)
    
    def listening_beep(self):
        """Play listening beep (started recording command)"""
        self.play_beep(frequency=1500, duration=0.05, volume=0.2)
    
    # Visual feedback methods
    
    def print_status(self, message, status="info"):
        """
        Print colored status message
        
        Args:
            message: Message to print
            status: Status type (info, success, error, warning, listening)
        """
        colors = {
            "info": Fore.CYAN,
            "success": Fore.GREEN,
            "error": Fore.RED,
            "warning": Fore.YELLOW,
            "listening": Fore.MAGENTA,
            "wake": Fore.BLUE
        }
        
        icons = {
            "info": "[INFO]",
            "success": "[SUCCESS]",
            "error": "[ERROR]",
            "warning": "[WARNING]",
            "listening": "[LISTENING]",
            "wake": "[WAKE]"
        }
        
        color = colors.get(status, Fore.WHITE)
        icon = icons.get(status, "")
        
        logger.info(f"{color}{icon} {message}{Style.RESET_ALL}")
    
    def print_banner(self, text):
        """Print a banner"""
        width = 60
        logger.info("\n" + "=" * width)
        logger.info(f"{Fore.CYAN}{text.center(width)}{Style.RESET_ALL}")
        logger.info("=" * width)
    
    def print_command(self, text):
        """Print recognized command"""
        logger.info(f"\n{Fore.YELLOW}You said: {Style.BRIGHT}\"{text}\"{Style.RESET_ALL}")
    
    def print_action(self, action, target):
        """Print parsed action"""
        logger.info(f"{Fore.BLUE}Action: {action} -> {target}{Style.RESET_ALL}")
    
    def show_listening_animation(self, duration=0.5):
        """Show a brief listening animation"""
        animation = ["|", "/", "-", "\\"]
        
        import time
        for _ in range(int(duration * 10)):
            for frame in animation:
                sys.stdout.write(f'\r{Fore.CYAN}Listening {frame}')
                sys.stdout.flush()
                time.sleep(0.05)
        
        sys.stdout.write('\r' + ' ' * 30 + '\r')
        sys.stdout.flush()
    
    def clear_line(self):
        """Clear current line"""
        sys.stdout.write('\r' + ' ' * 80 + '\r')
        sys.stdout.flush()
    
    def show_thinking(self):
        """Show thinking indicator"""
        logger.info(f"{Fore.CYAN}Processing...{Style.RESET_ALL}", end='', flush=True)
    
    def clear_thinking(self):
        """Clear thinking indicator"""
        self.clear_line()

if __name__ == "__main__":
    # Test feedback system
    logger.info("Feedback System Test\n")
    
    feedback = FeedbackSystem()
    
    import time
    
    feedback.print_banner("JARVIS Voice Assistant")
    time.sleep(0.5)
    
    feedback.print_status("Initializing system...", "info")
    time.sleep(0.5)
    
    feedback.print_status("Listening for wake word...", "wake")
    time.sleep(1)
    
    logger.info("\nPlaying activation beep...")
    feedback.activation_beep()
    feedback.print_status("Wake word detected!", "success")
    time.sleep(0.5)
    
    logger.info("\nPlaying listening beep...")
    feedback.listening_beep()
    feedback.print_status("Recording command...", "listening")
    time.sleep(0.5)
    
    feedback.print_command("open chrome")
    feedback.print_action("open", "chrome")
    time.sleep(0.5)
    
    logger.info("\nPlaying success beep...")
    feedback.success_beep()
    feedback.print_status("Command executed successfully!", "success")
    time.sleep(0.5)
    
    logger.error("\nPlaying error beep...")
    feedback.error_beep()
    feedback.print_status("Command failed!", "error")
    
    logger.info("\nTest complete!")
