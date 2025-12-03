# JARVIS HUD Interface

I have created a prototype "Iron Man" style Heads-Up Display (HUD) for your desktop.

## Features
- **Transparent Overlay**: Sits on top of your windows without blocking them.
- **System Diagnostics**: Real-time CPU and RAM usage in the top-left corner.
- **Arc Reactor**: Rotating reactor animation in the bottom-left.
- **Waveform Visualizer**: Simulated voice activity in the bottom-center.
- **Clock**: Futuristic clock in the top-right.

## How to Run
```powershell
python run_jarvis_hud.py
```

## Controls
- **ESC**: Close the HUD.

## Note on Transparency
This uses Windows-specific transparency keys. The background is technically a very dark color (`#000001`) that Windows treats as "invisible".
If you click on a UI element (like the clock), it interacts with the HUD. If you click on the empty space, it *might* click through depending on your specific Windows version and settings, but usually, it sits *on top* and might block clicks to windows behind it.

To make it fully "click-through" (interactive wallpaper), we would need deeper Windows API calls (User32.dll), which is more complex.
For now, this serves as a visual overlay.
