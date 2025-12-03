# Adaptive Noise Calibration

Jarvis now features **Adaptive Noise Calibration**. This allows the system to automatically adjust its sensitivity based on the surrounding environment.

## How it Works

### 1. Dynamic Thresholding
The Voice Activity Detector (VAD) continuously monitors the audio input when you are *not* speaking.
- **Quiet Room**: The threshold lowers, allowing you to whisper or speak softly.
- **Noisy Room**: The threshold raises, preventing background noise (fans, AC, traffic) from triggering false recordings.

### 2. Implementation Details
- **File**: `src/utils/vad_detector.py`
- **Method**: `adapt_threshold(audio_frame)`
- **Logic**: 
  - It calculates the energy of the current "silence" frame.
  - It uses an Exponential Moving Average (EMA) to slowly drift the threshold towards the current noise floor.
  - `NewThreshold = (OldThreshold * 0.95) + (CurrentNoise * 1.5 * 0.05)`

### 3. Benefits
- **Fewer False Positives**: Jarvis won't start recording just because a door slammed or a car drove by.
- **Better Recognition**: By correctly identifying the start and end of speech in noisy environments, the Speech-to-Text engine receives cleaner audio segments.

## Manual Calibration
You can still force a manual calibration if the environment changes drastically (e.g., you turn on a vacuum cleaner).
- The system performs an initial calibration on startup.
- The adaptive system takes over from there.
