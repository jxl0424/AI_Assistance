
import subprocess
import sys
import time

def install_vision_model():
    print("Checking for Ollama...")
    try:
        subprocess.run(["ollama", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: Ollama is not installed or not in PATH.")
        print("Please install Ollama from https://ollama.com/")
        return

    print("\nInstalling Vision Model (llava)...")
    print("This may take a while depending on your internet connection (approx 4GB).")
    
    try:
        # Run in a new window so user can see progress, or just run it here
        process = subprocess.Popen(["ollama", "pull", "llava"])
        process.wait()
        
        if process.returncode == 0:
            print("\nSUCCESS: Vision model 'llava' installed!")
            print("You can now ask Jarvis: 'What is on my screen?'")
        else:
            print("\nFailed to install model.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    install_vision_model()
    input("\nPress Enter to exit...")
