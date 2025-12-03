# How to Run JARVIS - Quick Guide

## You Have 3 Ways to Run JARVIS:

### 1. Interactive Menu (RECOMMENDED)
```bash
python start_jarvis.py
```
- Choose between Console or GUI mode
- Easy selection
- Best for new users

---

### 2. Console Mode (Direct)
```bash
python run_jarvis.py
```
- Runs in terminal/command line
- Text-based interface
- Voice activation: "Hey JARVIS"
- Lightweight and fast

---

### 3. GUI Mode (Direct)
```bash
python run_jarvis_gui.py
```
- Graphical user interface
- Visual chat window
- Click "Start System" button
- Better for desktop use

---

## What Happened to the GUI?

The GUI is still there! It just needs to be launched with the GUI launcher:

**Before reorganization:**
- GUI was in root directory
- Mixed with other files

**After reorganization:**
- GUI is in `src/modules/gui_app.py`
- Separate launchers for console and GUI
- Cleaner organization

---

## Quick Start:

### Option A: Interactive Menu
```bash
python start_jarvis.py
# Then choose: 1 for Console, 2 for GUI
```

### Option B: Direct Launch
```bash
# Console mode
python run_jarvis.py

# OR GUI mode
python run_jarvis_gui.py
```

---

## Features of Each Mode:

### Console Mode:
- [OK] Voice activation ("Hey JARVIS")
- [OK] All features available
- [OK] Lightweight
- [OK] Fast startup
- [OK] Terminal-based
- [OK] Good for debugging

### GUI Mode:
- [OK] Visual interface
- [OK] Chat window
- [OK] Status indicators
- [OK] Click to start/stop
- [OK] Better UX
- [OK] Desktop application feel

---

## Troubleshooting:

### GUI not showing?
Make sure you're running:
```bash
python run_jarvis_gui.py
```
NOT:
```bash
python run_jarvis.py  # This is console mode
```

### Want to switch modes?
Just close JARVIS and run the other launcher:
```bash
# From console to GUI
Ctrl+C  # Stop console mode
python run_jarvis_gui.py  # Start GUI mode
```

---

## Files:

- `start_jarvis.py` - Interactive menu
- `run_jarvis.py` - Console mode
- `run_jarvis_gui.py` - GUI mode
- `src/main.py` - Core JARVIS (can run directly)
- `src/modules/gui_app.py` - GUI application

---

## Recommendation:

**For daily use:**
- Use `python start_jarvis.py` (menu)
- Choose GUI mode for desktop
- Choose Console mode for quick tasks

**For development:**
- Use Console mode for debugging
- Easier to see logs
- Faster iteration

**For demos:**
- Use GUI mode
- Looks more professional
- Better visual feedback

---

## Summary:

Your GUI is not gone! You just need to use the right launcher:

```bash
# Interactive menu (choose mode)
python start_jarvis.py

# Console mode (no GUI)
python run_jarvis.py

# GUI mode (with GUI)
python run_jarvis_gui.py
```

All three work! Pick your favorite! 
