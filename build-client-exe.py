"""
Build script to convert client.py to standalone Windows executable using PyInstaller
Run this on Windows with Python installed
"""

import PyInstaller.__main__
import os
import sys

def build_exe():
    print("Building client.exe with PyInstaller...")
    
    # PyInstaller command to create a single file executable
    PyInstaller.__main__.run([
        'client.py',
        '--onefile',           # Create single file executable
        '--windowed',          # Hide console window (use --console for debugging)
        '--name=client',       # Output executable name
        '--icon=NONE',         # No icon (can add icon file later)
        '--clean',             # Clean build cache
        '--noconfirm',         # Overwrite existing files
    ])
    
    print("\nBuild complete!")
    print("Executable location: dist/client.exe")
    print("\nTo test: dist\\client.exe localhost 8765")

if __name__ == '__main__':
    build_exe()
