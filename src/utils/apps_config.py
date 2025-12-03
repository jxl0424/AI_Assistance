"""
Application registry - paths and commands for common applications
"""

import os
import platform
from pathlib import Path

# Cross-platform application paths
# Try multiple common locations for each application

def get_system_paths():
    """Get system-specific path prefixes"""
    system = platform.system()
    if system == "Windows":
        return {
            "program_files": os.environ.get("ProgramFiles", "C:\\Program Files"),
            "program_files_x86": os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"),
            "appdata": os.environ.get("APPDATA", ""),
            "system32": "C:\\Windows\\System32",
            "username": os.environ.get("USERNAME", "")
        }
    elif system == "Darwin":  # macOS
        return {
            "applications": "/Applications",
            "user_applications": os.path.expanduser("~/Applications")
        }
    else:  # Linux
        return {
            "usr_bin": "/usr/bin",
            "usr_local_bin": "/usr/local/bin",
            "snap": "/snap"
        }

# Get system paths
paths = get_system_paths()

APPLICATIONS = {
    "chrome": {
        "paths": [
            # Windows
            os.path.join(paths.get("program_files", ""), "Google", "Chrome", "Application", "chrome.exe"),
            os.path.join(paths.get("program_files_x86", ""), "Google", "Chrome", "Application", "chrome.exe"),
            # macOS
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            # Linux
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable",
            "/snap/bin/chromium"
        ],
        "aliases": ["chrome", "google chrome", "browser"],
        "url_support": True
    },
    "firefox": {
        "paths": [
            # Windows
            os.path.join(paths.get("program_files", ""), "Mozilla Firefox", "firefox.exe"),
            os.path.join(paths.get("program_files_x86", ""), "Mozilla Firefox", "firefox.exe"),
            # macOS
            "/Applications/Firefox.app/Contents/MacOS/firefox",
            # Linux
            "/usr/bin/firefox",
            "/snap/bin/firefox"
        ],
        "aliases": ["firefox", "mozilla firefox"],
        "url_support": True
    },
    "spotify": {
        "paths": [
            # Windows
            os.path.join(paths.get("appdata", ""), "Spotify", "Spotify.exe"),
            # macOS
            "/Applications/Spotify.app/Contents/MacOS/Spotify",
            # Linux
            "/usr/bin/spotify",
            "/snap/bin/spotify"
        ],
        "aliases": ["spotify", "music"],
        "url_support": False
    },
    "vscode": {
        "paths": [
            # Windows
            os.path.join(paths.get("program_files", ""), "Microsoft VS Code", "Code.exe"),
            os.path.join("C:\\Users", paths.get("username", ""), "AppData", "Local", "Programs", "Microsoft VS Code", "Code.exe"),
            # macOS
            "/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code",
            # Linux
            "/usr/bin/code",
            "/snap/bin/code"
        ],
        "aliases": ["vscode", "visual studio code", "vs code", "code"],
        "url_support": False
    },
    "notepad": {
        "paths": [
            # Windows
            os.path.join(paths.get("system32", ""), "notepad.exe"),
            # macOS - use TextEdit as fallback
            "/Applications/TextEdit.app/Contents/MacOS/TextEdit",
            # Linux - use gedit or nano
            "/usr/bin/gedit",
            "/usr/bin/nano",
            "/usr/bin/vim"
        ],
        "aliases": ["notepad", "text editor", "editor"],
        "url_support": False
    },
    "explorer": {
        "paths": [
            # Windows
            os.path.join(paths.get("system32", ""), "explorer.exe"),
            # macOS - use Finder
            "/System/Library/CoreServices/Finder.app/Contents/MacOS/Finder",
            # Linux - use nautilus or xdg-open
            "/usr/bin/nautilus",
            "/usr/bin/dolphin",
            "/usr/bin/thunar"
        ],
        "aliases": ["explorer", "file explorer", "files", "finder"],
        "url_support": False
    }
}

def find_application_path(app_name):
    """
    Find the actual path of an application
    
    Args:
        app_name: Application key from APPLICATIONS dict
        
    Returns:
        Path to executable or None if not found
    """
    if app_name not in APPLICATIONS:
        return None
    
    for path in APPLICATIONS[app_name]["paths"]:
        if os.path.exists(path):
            return path
    
    return None

def get_app_from_alias(alias):
    """
    Get application key from alias
    
    Args:
        alias: Application name or alias
        
    Returns:
        Application key or None if not found
    """
    alias_lower = alias.lower().strip()
    
    for app_key, app_info in APPLICATIONS.items():
        if alias_lower in app_info["aliases"]:
            return app_key
    
    return None

def list_available_apps():
    """
    List all applications that are actually installed
    
    Returns:
        Dictionary of available apps
    """
    available = {}
    
    for app_key, app_info in APPLICATIONS.items():
        path = find_application_path(app_key)
        if path:
            available[app_key] = {
                "path": path,
                "aliases": app_info["aliases"]
            }
    
    return available

if __name__ == "__main__":
    # Test the application registry
    print(" Scanning for installed applications...\n")
    
    available = list_available_apps()
    
    if available:
        print(f" Found {len(available)} applications:\n")
        for app_key, info in available.items():
            print(f" {app_key.upper()}")
            print(f"   Path: {info['path']}")
            print(f"   Aliases: {', '.join(info['aliases'])}")
            print()
    else:
        print(" No applications found!")
