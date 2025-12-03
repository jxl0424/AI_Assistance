#!/usr/bin/env python
"""
JARVIS Launcher - Console Mode
Runs JARVIS in console/terminal mode
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

if __name__ == "__main__":
    # Initialize logging system
    from src.core.logger_config import init_jarvis_logging
    init_jarvis_logging(debug=False)  # Set to True for verbose logging
    
    # Import and create JARVIS
    from main import JarvisAgent
    
    print("\n" + "="*70)
    print(" "*20 + "JARVIS - Console Mode")
    print("="*70)
    print("\nStarting JARVIS in console mode...")
    print("Say 'Hey JARVIS' to activate\n")
    
    # Start JARVIS
    jarvis = JarvisAgent(use_wake_word=True)
    jarvis.run()
