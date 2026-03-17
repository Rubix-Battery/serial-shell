# SERIAL-SHELL
Simple serial monitor terminal that feels like a standard terminal.

## How to use

Simply launch the `serial-shell.exe` and use it! You can leave the port and baud at the default `COM1` and `115200` by pressing `Enter` or enter new values when prompted. Be sure to check out the help section if needed by typing `/h` or `/help`. (Any text preceded by `/` is treated as a special command to `serial-shell`)

## Packaging into executable

```shell
# to build
python build_script.py

# It will create a venv and install the required packages (requires internet connection)
# and build the executable

# Note: The icon for the .exe may not change until you reboot the 
# PC or copy the executable to another location. (Because of Windows' persistent
# icon image cache.)
```

## Resources

[`.png` to `.ico` converter](https://image.online-convert.com/convert/png-to-ico) for creating an icon for the executable file.