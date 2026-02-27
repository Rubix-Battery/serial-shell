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


    def get_valid_port():
        while True:
            ports = [p.device for p in serial.tools.list_ports.comports() if not p.device.startswith('NULL_')]
            port_input = input(f"Enter port (e.g., COM1) [{ports[0] if ports else 'COM1'}]: ").strip()
            port = port_input.upper() if port_input else (ports[0] if ports else 'COM1')
            if port in ports:
                return port
            print(f"{Fore.RED}[Error: '{port}' is not a valid port. Available: {', '.join(ports) if ports else 'None'}]{Style.RESET_ALL}")

    port = get_valid_port()

    COMMON_BAUD_RATES = [9600, 19200, 38400, 57600, 115200, 230400, 460800, 921600]

    def get_valid_baud():
        while True:
            baud_input = input(f"Enter baud rate {COMMON_BAUD_RATES} [default: 115200]: ").strip()
            baud = int(baud_input) if baud_input else 115200
            if baud in COMMON_BAUD_RATES:
                return baud
            print(f"{Fore.RED}[Error: '{baud}' is not a valid baud rate. Allowed: {', '.join(str(b) for b in COMMON_BAUD_RATES)}]{Style.RESET_ALL}")

    baud = get_valid_baud()
    logfile = os.path.join(LOG_DIR, f"{port.replace('/', '_')}.log")

    stop_event = threading.Event()


    def open_serial():
        try:
            ser = serial.Serial(port, baud, timeout=0.5)
            return ser
        except (serial.SerialException, OSError) as e:
            print(f"[Error: Could not open port '{port}': {e}]")
            return None

    ser = open_serial()
    while ser is None:
        port = input("Enter a valid port (e.g., COM1): ").strip()
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
                    ports = [port for port in serial.tools.list_ports.comports() if not port.device.startswith('NULL_')]
                    if ports:
                        maxlen = max(len(port.device) for port in ports)
                        label_width = maxlen + 3  # 3 for ' -'
                        for port in ports:
                            port_name = f"{port.device}"
                            print(f"  {Fore.BLUE}{port_name.ljust(label_width)}{Style.RESET_ALL} {Fore.YELLOW}-{Style.RESET_ALL} {Fore.MAGENTA}{port.description}{Style.RESET_ALL}")
                    else:
                        print("  (No serial ports found)")
                elif cmd == "/port" and len(tokens) >= 2:
                    new_port = tokens[1]
                    print(f"{Fore.CYAN}[Switching to port {new_port}]{Style.RESET_ALL}")
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
                    print(f"{Fore.CYAN}[Switching baud rate to {baud}]{Style.RESET_ALL}")
                    stop_event.set()
                    reader_thread.join()
                    ser.close()
                    stop_event.clear()
                    ser = open_serial()
                    reader_thread = threading.Thread(target=serial_reader, args=(ser, stop_event, logfile), daemon=True)
                    reader_thread.start()
                elif cmd == "/log" and len(tokens) >= 2:
                    logfile = os.path.join(LOG_DIR, tokens[1])
                    print(f"{Fore.CYAN}[Logging to {logfile}]{Style.RESET_ALL}")
                else:
                    print("Unknown command. Type /help for list.")
            else:
                if ser and ser.is_open:
                    ser.write((line + "\n").encode())
    except KeyboardInterrupt:
        print(f"{Fore.CYAN}User exited.{Style.RESET_ALL}")
    except EOFError:
        print(f"{Fore.CYAN}End of input.{Style.RESET_ALL}")
    finally:
        stop_event.set()
        reader_thread.join()
        ser.close()
        print(f"{Fore.CYAN}\nTerminal closed.{Style.RESET_ALL}")



if __name__ == "__main__":
    main()
