"""
Launcher for AI Lead Pipeline - Standalone Desktop App
This script starts the Streamlit application for the packaged .exe
"""
import subprocess
import sys
import os

def main():
    # Get the directory where the exe is located
    if getattr(sys, 'frozen', False):
        # Running as compiled .exe
        app_dir = os.path.dirname(sys.executable)
    else:
        # Running from source
        app_dir = os.path.dirname(os.path.abspath(__file__))

    # Path to streamlit app
    app_path = os.path.join(app_dir, "streamlit_app.py")

    # Run streamlit
    cmd = [sys.executable, "-m", "streamlit", "run", app_path, "--server.headless=true"]
    subprocess.run(cmd)

if __name__ == "__main__":
    main()
