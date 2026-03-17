import subprocess
import shutil
import os
import sys

# needs fixing yet:
# https://stackoverflow.com/questions/6943208/activate-a-virtualenv-with-a-python-script

def venv_exists():
    if os.name == "nt":
        return os.path.isdir("venv") and os.path.isdir(os.path.join("venv", "Scripts"))
    else:
        return os.path.isdir("venv") and os.path.isdir(os.path.join("venv", "bin"))

def setup_venv():
    python_exe = "python" if os.name == "nt" else "python3"
    subprocess.run([python_exe, "-m", "venv", "venv"])
    venv_python = os.path.join("venv", "Scripts", "python.exe") if os.name == "nt" else os.path.join("venv", "bin", "python")
    subprocess.run([venv_python, "-m", "pip", "install", "-r", "requirements.txt"])

def clean():
    # Remove build directory if it exists
    if os.path.isdir("build"):
        shutil.rmtree("build")
    # Remove .spec file if it exists
    spec_file = "serial-shell.spec"
    if os.path.isfile(spec_file):
        os.remove(spec_file)

def build_executable():
    venv_python = os.path.join("venv", "Scripts", "python.exe") if os.name == "nt" else os.path.join("venv", "bin", "python")
    subprocess.run([
        venv_python, "-m", "PyInstaller",
        "--onefile",
        "--icon=img/SerialShell.ico",
        "--name=serial-shell",
        "src/main.py"
    ], check=True)


def main():
    venv_python = os.path.join("venv", "Scripts", "python.exe") if os.name == "nt" else os.path.join("venv", "bin", "python")
    if not venv_exists():
        setup_venv()
        
    # If not running inside venv, re-launch script with venv's python
    if os.path.abspath(sys.executable) != os.path.abspath(venv_python):
        subprocess.run([venv_python, __file__])
        return
    
    clean()
    build_executable()
    clean()



if __name__ == "__main__":
    main()