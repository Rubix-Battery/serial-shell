#!/usr/bin/env python3

import serial
import serial.tools.list_ports
import threading
import time
import sys
import os
from colorama import init, Fore, Style

init(autoreset=True)

# Colors
TERM_COLOR = Fore.CYAN
ERROR_COLOR = Fore.RED
RX_COLOR = Fore.LIGHTCYAN_EX
TX_COLOR = Fore.GREEN

COMMON_BAUD_RATES = [9600, 19200, 38400, 57600, 115200, 230400, 460800, 921600]

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)


class SerialTerminal:

    def __init__(self):
        self.port = None
        self.baud = 115200
        self.ser = None
        self.logfile = None

        self.stop_event = threading.Event()
        self.reader_thread = None

        # buffered RX
        self._rx_buffer = bytearray()
        self._last_rx = 0
        self._lock = threading.Lock()

    # --------------------------------------------------
    # Validation
    # --------------------------------------------------

    def available_ports(self):
        return [
            (p.device, p.description)
            for p in serial.tools.list_ports.comports()
            if not p.device.startswith("NULL_")
        ]

    def validate_port(self, port):
        ports = [p[0] for p in self.available_ports()]
        if port in ports:
            return True
        print(f"{ERROR_COLOR}Invalid port: {port} Available: {', '.join(ports) if ports else 'None'}")
        return False

    def validate_baud(self, baud):
        if baud in COMMON_BAUD_RATES:
            return True
        print(f"{ERROR_COLOR}Invalid baud. Allowed: {COMMON_BAUD_RATES}")
        return False

    # --------------------------------------------------
    # Serial Lifecycle
    # --------------------------------------------------

    def open_serial(self):
        try:
            self.ser = serial.Serial(self.port, self.baud, timeout=0.1)
            self.logfile = os.path.join(LOG_DIR, f"{self.port}.log")
            print(f"{TERM_COLOR}[Connected {self.port} @ {self.baud}]")
            return True
        except Exception as e:
            print(f"{ERROR_COLOR}[Open error: {e}]")
            return False

    def close_serial(self):
        self.stop_event.set()
        if self.reader_thread:
            self.reader_thread.join()
        if self.ser and self.ser.is_open:
            self.ser.close()

    def start_reader(self):
        self.stop_event.clear()
        self.reader_thread = threading.Thread(target=self.reader_loop, daemon=True)
        self.reader_thread.start()

    # --------------------------------------------------
    # Buffered RX (100ms idle flush)
    # --------------------------------------------------

    def reader_loop(self):
        while not self.stop_event.is_set():
            try:
                data = self.ser.read(1024)
                now = time.time()

                if data:
                    with self._lock:
                        self._rx_buffer.extend(data)
                        self._last_rx = now

                with self._lock:
                    if self._rx_buffer and (now - self._last_rx) > 0.1:
                        text = self._rx_buffer.decode(errors="ignore")
                        sys.stdout.write(RX_COLOR + text + Style.RESET_ALL)
                        sys.stdout.flush()

                        if self.logfile:
                            with open(self.logfile, "a") as f:
                                f.write(f"RX: {text}\n")

                        self._rx_buffer.clear()

            except Exception as e:
                print(f"{ERROR_COLOR}[Read error: {e}]")
                break

    # --------------------------------------------------
    # CLI
    # --------------------------------------------------

    def print_header(self):
        # clear the setup prompts and details
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"{TERM_COLOR}=================================")
        print(f"{TERM_COLOR}        Termial Console         ")
        print(f"{TERM_COLOR}=================================")
        print(f"{TERM_COLOR}Port: {self.port}")
        print(f"{TERM_COLOR}Baud: {self.baud}")
        print(f"{TERM_COLOR}Type /h for help\n")

    def list_ports(self):
        ports = self.available_ports()
        if not ports:
            print("No available ports.")
            return
        print(f"{TERM_COLOR}Available Ports:")
        for device, desc in ports:
            print(f"  {TERM_COLOR}{device}\t{desc}")

    def handle_command(self, line):
        parts = line.split()
        cmd = parts[0].lower()

        if cmd in ("/q", "/quit", "/exit"):
            return False

        elif cmd in ("/h", "/help"):
            print(f"{TERM_COLOR}/h          Show commands")
            print(f"{TERM_COLOR}/q          Exit")
            print(f"{TERM_COLOR}/c          Clear screen")
            print(f"{TERM_COLOR}/p <COMx>   Change port")
            print(f"{TERM_COLOR}/b <rate>   Change baud")
            print(f"{TERM_COLOR}/lsp        List ports")

        elif cmd in ("/clear", "/cls", "/c"):
            os.system("cls" if os.name == "nt" else "clear")
            self.print_header()

        elif cmd == "/lsp":
            self.list_ports()

        elif cmd in ("/p", "/port") and len(parts) > 1:
            new_port = parts[1].upper()
            if not self.validate_port(new_port):
                return True

            self.close_serial()
            self.port = new_port
            if self.open_serial():
                self.start_reader()

        elif cmd in ("/b", "/baud") and len(parts) > 1:
            try:
                new_baud = int(parts[1])
            except ValueError:
                print(f"{ERROR_COLOR}Invalid baud value.")
                return True

            if not self.validate_baud(new_baud):
                return True

            self.close_serial()
            self.baud = new_baud
            if self.open_serial():
                self.start_reader()

        else:
            print("Unknown command.")

        return True

    # --------------------------------------------------
    # Main Loop
    # --------------------------------------------------

    def run(self):
        while True:
            port_input = input(f"{TERM_COLOR}Enter port (e.g., COM1): ").upper()
            # default to first serial port on system if none is input
            port = port_input if port_input else ('COM1' if os.name == 'nt' else '/dev/ttyUSB0')
            if self.validate_port(port):
                self.port = port
                break

        while True:
            baud_input = input(f"{TERM_COLOR}Enter baud {COMMON_BAUD_RATES} [115200]: ").strip()
            baud = int(baud_input) if baud_input else 115200
            if self.validate_baud(baud):
                self.baud = baud
                break

        self.print_header()

        if not self.open_serial():
            return

        self.start_reader()

        try:
            while True:
                line = input()
                if line.startswith("/"):
                    if not self.handle_command(line):
                        break
                else:
                    if self.ser and self.ser.is_open:
                        # Log TX to file
                        if self.logfile:
                            with open(self.logfile, "a") as f:
                                f.write(f"TX: {line}\n")
                        self.ser.write((line + "\n").encode())

        except (KeyboardInterrupt, EOFError):
            pass
        finally:
            self.close_serial()
            print(f"{TERM_COLOR}\nExiting.")


def main():
    SerialTerminal().run()


if __name__ == "__main__":
    main()