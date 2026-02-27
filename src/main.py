#!/usr/bin/env python3
"""
Portable Serial Terminal for Windows (ESP32 / NodeMCU)
- Uses PySerial's threaded ReaderThread
- Runtime port and baud rate changes
- Input/output in same console
- Optional logging
"""

import serial
import serial.threaded
import threading
import sys
import os
import time

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)


class TerminalProtocol(serial.threaded.Protocol):
    """Handles incoming serial data, prints to console, and logs if enabled."""
    def __init__(self, label=None, logfile=None, flush_interval=0.1):
        super().__init__()
        self.transport = None
        self.label = label
        self.logfile = logfile
        self.flush_interval = flush_interval  # seconds
        self._buffer = bytearray()
        self._last_received = time.time()
        self._lock = threading.Lock()
        self._flusher = threading.Thread(target=self._flush_loop, daemon=True)
        self._flusher.start()

    def connection_made(self, transport):
        self.transport = transport
        print(f"[Connected on {transport.serial.port}]")

    def data_received(self, data):
        """Accumulate data; flush after idle timeout"""
        with self._lock:
            self._buffer.extend(data)
            self._last_received = time.time()

    def _flush_loop(self):
        """Periodically flush buffer if idle > flush_interval"""
        while True:
            time.sleep(self.flush_interval / 2)
            now = time.time()
            with self._lock:
                if self._buffer and (now - self._last_received >= self.flush_interval):
                    text = self._buffer.decode(errors='ignore')
                    sys.stdout.write(text + "\n")  # add newline
                    sys.stdout.flush()
                    # Optional logging
                    if self.logfile:
                        with open(self.logfile, 'a') as f:
                            f.write(f"{self.label}: {text}\n")
                    self._buffer.clear()

    @classmethod
    def flush(cls, logfile):
        """Flush class-level buffer (optional, existing behavior)"""
        if cls.buffer:
            with open(logfile, 'a') as f:
                f.write(f"{cls.last_direction}: {cls.buffer}\n")
            cls.buffer = ""

    def connection_lost(self, exc):
        print(f"\n[Connection lost: {exc}]")


def start_terminal(port_name, baud=115200, label="TERMINAL", logfile=None):
    """Starts a ReaderThread and returns the thread and Serial object."""
    ser = serial.Serial(port_name, baud, timeout=0)
    protocol_factory = lambda: TerminalProtocol(label=label, logfile=logfile)
    thread = serial.threaded.ReaderThread(ser, protocol_factory)
    thread.start()
    return thread, ser


def main():
    print("=== Portable Serial Terminal ===")
    print("Type /help for commands.\n")

    port_input = input("Enter port (e.g., COM1): ").strip()
    port = port_input if port_input else 'COM1'
    baud_input = input("Enter baud rate [115200]: ").strip()
    baud = int(baud_input) if baud_input else 115200
    logfile = os.path.join(LOG_DIR, f"{port.replace('/', '_')}.log")

    thread, ser = start_terminal(port, baud, logfile=logfile)

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
                elif cmd == "/port" and len(tokens) >= 2:
                    new_port = tokens[1]
                    print(f"[Switching to port {new_port}]")
                    thread.close()
                    ser.close()
                    thread, ser = start_terminal(new_port, baud, logfile=logfile)
                elif cmd == "/baud" and len(tokens) >= 2:
                    baud = int(tokens[1])
                    print(f"[Switching baud rate to {baud}]")
                    thread.close()
                    ser.close()
                    thread, ser = start_terminal(port, baud, logfile=logfile)
                elif cmd == "/log" and len(tokens) >= 2:
                    logfile = os.path.join(LOG_DIR, tokens[1])
                    print(f"[Logging to {logfile}]")
                else:
                    print("Unknown command. Type /help for list.")
            else:
                if ser and ser.is_open:
                    ser.write((line + "\n").encode())
    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        thread.close()
        ser.close()
        print("\nTerminal closed.")


if __name__ == "__main__":
    main()
