#!/usr/bin/env python
"""
JARVIS Launcher - Interactive Menu
Choose how to run JARVIS
"""

import sys
import os
import subprocess

def main():
    print("\n" + "="*70)
    print(" "*20 + "JARVIS AI Assistant")
    print(" "*20 + "Launch Menu")
    print("="*70)
    
    print("\nHow would you like to run JARVIS?\n")
    print("1. Console Mode (Terminal/Command Line)")
    print("   - Text-based interface")
    print("   - Voice activation with 'Hey JARVIS'")
    print("   - Lightweight")
    
    print("\n2. GUI Mode (Graphical Interface)")
    print("   - Visual interface with chat window")
    print("   - Click to start/stop")
    print("   - Better for desktop use")
    
    print("\n3. Exit")
    
    print("\n" + "="*70)
    
    while True:
        choice = input("\nEnter your choice (1, 2, or 3): ").strip()
        
        if choice == "1":
            print("\n[Launching Console Mode...]")
            print("Say 'Hey JARVIS' to activate\n")
            subprocess.run([sys.executable, "run_jarvis.py"])
            break
            
        elif choice == "2":
            print("\n[Launching GUI Mode...]")
            print("Click 'Start System' in the window\n")
            subprocess.run([sys.executable, "run_jarvis_gui.py"])
            break
            
        elif choice == "3":
            print("\nGoodbye!")
            break
            
        else:
            print("\n[ERROR] Invalid choice. Please enter 1, 2, or 3.")

if __name__ == "__main__":
    main()
