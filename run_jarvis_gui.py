#!/usr/bin/env python
"""
JARVIS Launcher - GUI Mode
Runs JARVIS with graphical user interface
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

if __name__ == "__main__":
    # Initialize logging system
    from src.core.logger_config import init_jarvis_logging
    init_jarvis_logging(debug=False)  # Set to True for verbose logging
    
    # Import and run GUI
    from src.modules.gui_app import JarvisGui
    
    print("\n" + "="*70)
    print(" "*20 + "JARVIS - GUI Mode")
    print("="*70)
    print("\nLaunching JARVIS GUI...")
    print("Click 'Start System' in the window to begin\n")
    
    # Start GUI
    app = JarvisGui()
    app.mainloop()
