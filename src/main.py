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

# text colors
TERMIAL_COLOR = Fore.LIGHTCYAN_EX
ERROR_COLOR = Fore.RED
RX_COLOR = Fore.CYAN
LSPORT_COLOR = Fore.YELLOW

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
                sys.stdout.write(RX_COLOR + text + Style.RESET_ALL)
                sys.stdout.flush()
                if logfile:
                    with open(logfile, 'a') as f:
                        f.write(f"RX: {text}")
        except Exception as e:
            print(f"{ERROR_COLOR}[Serial read error: {e}]{Style.RESET_ALL}")
            break

COMMON_BAUD_RATES = [9600, 19200, 38400, 57600, 115200, 230400, 460800, 921600]

def validate_baud(baud: int):
    if baud in COMMON_BAUD_RATES:
        return baud
    print(f"{ERROR_COLOR}[Error: '{baud}' is not a valid baud rate. Allowed: {', '.join(str(b) for b in COMMON_BAUD_RATES)}]{Style.RESET_ALL}")

def prompt_baud():
    while True:
        baud_input = input(f"Enter baud rate {COMMON_BAUD_RATES} [default: 115200]: ").strip()
        baud = int(baud_input) if baud_input else 115200
        return validate_baud(baud)


def get_valid_port():
    while True:
        ports = [p.device for p in serial.tools.list_ports.comports() if not p.device.startswith('NULL_')]
        port_input = input(f"{TERMIAL_COLOR}Enter port (e.g., COM1) [{ports[0] if ports else 'COM1'}]: ").strip()
        port = port_input.upper() if port_input else (ports[0] if ports else 'COM1')
        if port in ports:
            return port
        print(f"{ERROR_COLOR}[Error: '{port}' is not a valid port. Available: {', '.join(ports) if ports else 'None'}]{Style.RESET_ALL}")

def main():
    port = get_valid_port()

    baud = prompt_baud()
    logfile = os.path.join(LOG_DIR, f"{port.replace('/', '_')}.log")

    # clear the setup details
    os.system('cls' if os.name == 'nt' else 'clear')

    def print_header():
        print(f"{TERMIAL_COLOR}=== Termial: Simple Serial Terminal ===")
        print(f"{TERMIAL_COLOR}Type /help for commands.\n")
        print(f"{TERMIAL_COLOR}Port: {port}")
        print(f"{TERMIAL_COLOR}Baud: {baud}{Style.RESET_ALL}")

    print_header()

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
                    print(" /cls            - Clear the screen")
                    print(" /quit           - Exit terminal")
                    print(" /port <COM>     - Change serial port")
                    print(" /baud <rate>    - Change baud rate")
                    print(" /log <filename> - Change log file")
                    print(" /lsport        - List available serial ports")
                elif cmd == "/cls":
                    # Clear the screen and reprint the header and prompts
                    os.system('cls' if os.name == 'nt' else 'clear')
                    print_header()
                elif cmd == "/lsport":
                    print("Available serial ports (not in use):")
                    all_ports = [port for port in serial.tools.list_ports.comports() if not port.device.startswith('NULL_')]
                    available_ports = []
                    for port in all_ports:
                        try:
                            s = serial.Serial(port.device, timeout=0.1)
                            s.close()
                            available_ports.append(port)
                        except (serial.SerialException, OSError):
                            pass
                    if available_ports:
                        maxlen = max(len(port.device) for port in available_ports)
                        label_width = maxlen + 3  # 3 for ' -'
                        for port in available_ports:
                            port_name = f"{port.device}"
                            print(f"  {TERMIAL_COLOR}{port_name.ljust(label_width)}{Style.RESET_ALL} {LSPORT_COLOR}- {port.description}{Style.RESET_ALL}")
                    else:
                        print("  (No available serial ports found)")
                elif cmd == "/port" and len(tokens) >= 2:
                    new_port = tokens[1]
                    print(f"{TERMIAL_COLOR}[Switching to port {new_port}]{Style.RESET_ALL}")
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
                    print(f"{TERMIAL_COLOR}[Switching baud rate to {baud}]{Style.RESET_ALL}")
                    stop_event.set()
                    reader_thread.join()
                    ser.close()
                    stop_event.clear()
                    ser = open_serial()
                    reader_thread = threading.Thread(target=serial_reader, args=(ser, stop_event, logfile), daemon=True)
                    reader_thread.start()
                elif cmd == "/log" and len(tokens) >= 2:
                    logfile = os.path.join(LOG_DIR, tokens[1])
                    print(f"{TERMIAL_COLOR}[Logging to {logfile}]{Style.RESET_ALL}")
                else:
                    print("Unknown command. Type /help for list.")
            else:
                if ser and ser.is_open:
                    ser.write((line + "\n").encode())
    except KeyboardInterrupt:
        print(f"{TERMIAL_COLOR}User exited.{Style.RESET_ALL}")
    except EOFError:
        print(f"{TERMIAL_COLOR}End of input.{Style.RESET_ALL}")
    finally:
        stop_event.set()
        reader_thread.join()
        ser.close()
        print(f"{TERMIAL_COLOR}\nTerminal closed.{Style.RESET_ALL}")



if __name__ == "__main__":
    main()
