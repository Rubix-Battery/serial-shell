#!/usr/bin/env python3
"""
Termial: Simple Serial Terminal for Windows (ESP32 / NodeMCU)
- Efficient, low-CPU, colored RX, CLI, TX/RX
"""

import serial
import serial.tools.list_ports
import threading
import sys
import os
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

def serial_reader(ser, stop_event, logfile=None):
    """Read from serial port, print RX in green, log if needed."""
    while not stop_event.is_set():
        try:
            data = ser.read(1024)  # blocking read, returns after timeout or data
            if data:
                text = data.decode(errors='ignore')
                # Ensure each RX message ends with a newline
                if not text.endswith("\n"):
                    text += "\n"
                sys.stdout.write(Fore.GREEN + text + Style.RESET_ALL)
                sys.stdout.flush()
                if logfile:
                    with open(logfile, 'a') as f:
                        f.write(f"RX: {text}")
        except Exception as e:
            print(f"[Serial read error: {e}]")
            break

def main():
    print("=== Termial: Simple Serial Terminal ===")
    print("Type /help for commands.\n")

    port_input = input("Enter port (e.g., COM1): ").strip()
    port = port_input if port_input else 'COM1'
    baud_input = input("Enter baud rate [115200]: ").strip()
    baud = int(baud_input) if baud_input else 115200
    logfile = os.path.join(LOG_DIR, f"{port.replace('/', '_')}.log")

    stop_event = threading.Event()

    def open_serial():
        ser = serial.Serial(port, baud, timeout=0.5)
        return ser

    ser = open_serial()
    reader_thread = threading.Thread(target=serial_reader, args=(ser, stop_event, logfile), daemon=True)
    reader_thread.start()

    try:
        while True:
            line = input()
            if line.startswith("/"):
                tokens = line.split()
                cmd = tokens[0].lower()
                if cmd == "/quit":
                    break
                elif cmd == "/help":
                    print("Commands:")
                    print(" /help           - Show this message")
                    print(" /quit           - Exit terminal")
                    print(" /port <COM>     - Change serial port")
                    print(" /baud <rate>    - Change baud rate")
                    print(" /log <filename> - Change log file")
                    print(" /lsport        - List available serial ports")
                elif cmd == "/lsport":
                    print("Available serial ports:")
                    ports = list(serial.tools.list_ports.comports())
                    if ports:
                        maxlen = max(len(port.device) for port in ports)
                        label_width = maxlen + 3  # 3 for ' -'
                        for port in ports:
                            port_and_dash = f"{port.device} -"
                            print(f"  {Fore.BLUE}{port_and_dash.ljust(label_width)}{Style.RESET_ALL} {Fore.MAGENTA}{port.description}{Style.RESET_ALL}")
                    else:
                        print("  (No serial ports found)")
                elif cmd == "/port" and len(tokens) >= 2:
                    new_port = tokens[1]
                    print(f"[Switching to port {new_port}]")
                    stop_event.set()
                    reader_thread.join()
                    ser.close()
                    port = new_port
                    stop_event.clear()
                    ser = open_serial()
                    reader_thread = threading.Thread(target=serial_reader, args=(ser, stop_event, logfile), daemon=True)
                    reader_thread.start()
                elif cmd == "/baud" and len(tokens) >= 2:
                    baud = int(tokens[1])
                    print(f"[Switching baud rate to {baud}]")
                    stop_event.set()
                    reader_thread.join()
                    ser.close()
                    stop_event.clear()
                    ser = open_serial()
                    reader_thread = threading.Thread(target=serial_reader, args=(ser, stop_event, logfile), daemon=True)
                    reader_thread.start()
                elif cmd == "/log" and len(tokens) >= 2:
                    logfile = os.path.join(LOG_DIR, tokens[1])
                    print(f"[Logging to {logfile}]")
                else:
                    print("Unknown command. Type /help for list.")
            else:
                if ser and ser.is_open:
                    ser.write((line + "\n").encode())
    except KeyboardInterrupt:
        print("User exited.")
    except EOFError:
        print("End of input.")
    finally:
        stop_event.set()
        reader_thread.join()
        ser.close()
        print("\nTerminal closed.")



if __name__ == "__main__":
    main()
