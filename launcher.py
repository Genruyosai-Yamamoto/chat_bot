import subprocess
import sys
import os
import webbrowser
import time

VENV_DIR = "venv"

PYTHON_VENV = os.path.join(
    VENV_DIR,
    "Scripts",
    "python.exe"
)

PIP_VENV = os.path.join(
    VENV_DIR,
    "Scripts",
    "pip.exe"
)


def create_venv():
    if not os.path.exists(VENV_DIR):
        print("🧱 Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", VENV_DIR])
    else:
        print("✅ Virtual environment already exists")


def install_requirements():
    print("📦 Installing dependencies...")
    subprocess.run([
        PYTHON_VENV,
        "-m",
        "pip",
        "install",
        "-r",
        "requirements.txt"
    ])


def run_app():
    print("🚀 Starting Flask app...")

    # open browser
    webbrowser.open("http://127.0.0.1:5000")

    subprocess.run([
        PYTHON_VENV,
        "app.py"
    ])


if __name__ == "__main__":

    create_venv()
    install_requirements()
    time.sleep(1)
    run_app()