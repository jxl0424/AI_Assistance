# Wake Word Optimization & SOTA Methods

## Current Optimization
We have optimized the **Vosk** wake word detector to significantly reduce latency and CPU usage.

### Grammar Restriction
By default, Vosk listens for *any* word in its large vocabulary, which is computationally expensive and slower.
We have modified `WakeWordDetector` to restrict the recognizer's grammar to **only** the wake words (e.g., "jarvis", "hey jarvis").

**Benefits:**
- **Faster Detection:** The search space is tiny, so the recognizer matches the wake word almost instantly.
- **Lower CPU Usage:** The background process consumes much less power.
- **Fewer False Positives:** The recognizer won't try to match random noise to other words.

### Non-Blocking Feedback
We updated the feedback system to allow non-blocking beeps. The activation beep now plays asynchronously, allowing the system to start listening for your command immediately, shaving off ~100ms of perceived latency.

## State-of-the-Art (SOTA) Methods
If you wish to further improve wake word detection, here are the current SOTA methods:

### 1. Porcupine (Picovoice)
- **Status:** Commercial (Free tier available)
- **Performance:** **Best in class**. Extremely low latency, high accuracy, runs on-device (Raspberry Pi, etc.).
- **Pros:** Easy to use, very lightweight.
- **Cons:** Requires API key, limits on free tier.

### 2. openWakeWord
- **Status:** Open Source (Apache 2.0)
- **Performance:** **Best Open Source**. Uses ONNX models trained on large datasets.
- **Pros:** No API keys, runs offline, very accurate, easy to train custom models.
- **Cons:** Requires `openwakeword` and `onnxruntime` packages.

### 3. Raven (Snips)
- **Status:** Open Source
- **Performance:** Good, but older.
- **Pros:** Lightweight.
- **Cons:** Less maintained.

### Recommendation
If you want to switch from Vosk, **openWakeWord** is the best free, open-source upgrade.
To use it:
1. Install: `pip install openwakeword`
2. Update `WakeWordDetector` to use `openwakeword.Model`.

For now, the **Optimized Vosk** implementation should be sufficient and much faster than before.
