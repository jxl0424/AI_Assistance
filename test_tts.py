import pyttsx3

print("Testing voice engine...")
try:
    engine = pyttsx3.init()
    engine.say("Testing voice system. One, two, three.")
    engine.runAndWait()
    print("Voice check complete.")
except Exception as e:
    print(f"Voice failed: {e}")