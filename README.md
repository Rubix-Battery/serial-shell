# Termial
Simple serial monitor terminal that feels like a standard terminal.

## How to use

Simply launch the `Termial.exe` and use it! You can leave the port and baud at the default `COM1` and `115200` by pressing `Enter` or enter new values when prompted. Be sure to check out the help section if needed by typing `/help`. (Any text preceded by `/` is treated as a special command to `Termial`)

## Python `venv` setup

```python
python -m venv venv
pip install -r requirements.txt
```
```shell
# *nix systems:
source venv/bin/activate
# Windows
venv/Scripts/Activate.ps1

# If using VS Code, usually relaunching the terminal
# will automatically activate the venv
```

## Packaging into executable

```shell
pyinstaller --onefile --icon=img/termial.ico --name=Termial src/main.py
# Note: The icon may not change until you reboot the PC or copy the 
# executable to another location.
```

## Resources

[`.png` to `.ico` converter](https://image.online-convert.com/convert/png-to-ico) for creating an icon for the executable file.