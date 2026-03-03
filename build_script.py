import subprocess
import shutil
import os
import argparse

def clean():
    # Remove build directory if it exists
    if os.path.isdir("build"):
        shutil.rmtree("build")
    # Remove .spec file if it exists
    spec_file = "Termial.spec"
    if os.path.isfile(spec_file):
        os.remove(spec_file)

def build_executable():
    # Build with PyInstaller
    subprocess.run([
        "pyinstaller",
        "--onefile",
        "--icon=img/termial.ico",
        "--name=Termial",
        "src/main.py"
    ], check=True)


def main():
    parser = argparse.ArgumentParser(description="Build Termial executable.")
    parser.add_argument(
        "-k", "--keep-build",
        action="store_true",
        help="Do not delete build directory and .spec file before/after build."
    )
    args = parser.parse_args()

    clean()
    build_executable()
    if not args.keep_build:
        clean()

if __name__ == "__main__":
    main()