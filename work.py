def ExecuteCommand(self, request, context):
        print(f"[RECEIVED] ExecuteCommand for ID: '{request.commandId}'")
        
        # 1. We create some fake database log data for your timeline
        fake_timeline_data = [
            {"Time": "12:00:00", "BE_State": "NORMAL", "Thermal_Throttle": None, "FWQ": None},
            {"Time": "12:05:00", "BE_State": "WARNING", "Thermal_Throttle": "THROTTLED", "FWQ": "FWQ_BE_Response"},
            {"Time": "12:10:00", "BE_State": "CRITICAL", "Thermal_Throttle": "THROTTLED", "FWQ": None}
        ]
        
        # 2. We convert it to a JSON string just like your production code does
        json_string = json.dumps(fake_timeline_data, indent=2)
        print("[SENDING] Fake JSON Timeline Data back to Grafana...")

        # 3. We pack it into the SyncResponse
        sync_resp = commands_pb2.Command.Execute.SyncResponse(
            status=200,
            respData=json_string,
            downloadAvailable=False
        )
        
        return commands_pb2.Command.Execute.Response(syncResponse=sync_resp)

import serial
import time
import re
import sys
import stat
import os
import json

PORT = "/dev/ttyUSB0"
BAUDRATE = 115200
COMMAND_PRIMARY = "/mm 208A0000\n"
COMMAND_FALLBACK = "/mm 208F7000\n"

class UART:
    def __init__(self, serial_command):
        self.serial_command = serial_command
        self.baudrate = 115200
        self.timeout = 2

    def run_serial_minicom(self, uart_device):
        serial_console = serial.Serial(port=uart_device, baudrate=self.baudrate)

        # Sending ESC character to UART
        for _ in range(0, 2):
            serial_console.write("\x1b".encode())
            time.sleep(2)
        time.sleep(2)

        serial_command = self.serial_command + "\r"
        serial_output = ""

        serial_console.write(serial_command.encode())
        time.sleep(2)
        rx_buf_bytes = serial_console.in_waiting

        while rx_buf_bytes != 0:
            time.sleep(self.timeout)
            rx_buf_bytes = serial_console.in_waiting
            # Added errors='ignore' so weird bricked characters don't crash Python and drop the IP
            serial_output += serial_console.read(rx_buf_bytes).decode('utf-8', errors='ignore')

        serial_console.close()
        return serial_output

def run_serial_cmd(serial_command):
    uart_device = "/dev/ttyUSB0"
    serial_obj = UART(serial_command)

    # Check if minicom UART is configured
    if stat.S_ISCHR(os.stat(uart_device).st_mode):
        try:
            return serial_obj.run_serial_minicom(uart_device)
        except Exception as e:
            return f"ERROR: {str(e)}"
    
    # Returning string instead of sys.exit(1) so Ansible doesn't crash on this host
    return "ERROR: DEVICE NOT CONFIGURED"


# ==========================================
# YOUR EXACT PARSING LOGIC - PRIMARY
# ==========================================
cmd_output_primary = run_serial_cmd(COMMAND_PRIMARY)

clean_output = cmd_output_primary.replace("\0", "")
uart_ascii_lines = []

for line in clean_output.splitlines():
    if re.match(r'^208a[0-9a-fA-F]{4}:', line, re.IGNORECASE):
        parts = re.split(r'\s{2,}', line)
        if len(parts) > 1:
            ascii_part = parts[-1].strip()
            ascii_part = ascii_part.replace(".", "")
            if ascii_part:
                uart_ascii_lines.append(ascii_part)
            else:
                uart_ascii_lines.append("")

while len(uart_ascii_lines) < 4:
    uart_ascii_lines.append("")

line1 = uart_ascii_lines[0]
line2 = uart_ascii_lines[1]
line3 = uart_ascii_lines[2]
line4 = uart_ascii_lines[3]

model_number = line1 + line2
serial_number = line3 + line4

# ==========================================
# YOUR EXACT PARSING LOGIC - FALLBACK
# ==========================================
cmd_output_fallback = ""
if not model_number.strip() and not serial_number.strip():
    cmd_output_fallback = run_serial_cmd(COMMAND_FALLBACK)
    
    clean_output = cmd_output_fallback.replace("\0", "")
    uart_ascii_lines = []
    
    for line in clean_output.splitlines():
        if re.match(r'^208f[0-9a-fA-F]{4}:', line, re.IGNORECASE):
            parts = re.split(r'\s{2,}', line)
            if len(parts) > 1:
                ascii_part = parts[-1].strip()
                ascii_part = ascii_part.replace(".", "")
                if ascii_part:
                    uart_ascii_lines.append(ascii_part)
                else:
                    uart_ascii_lines.append("")

    while len(uart_ascii_lines) < 4:
        uart_ascii_lines.append("")

    line1 = uart_ascii_lines[0]
    line2 = uart_ascii_lines[1]
    line3 = uart_ascii_lines[2]
    line4 = uart_ascii_lines[3]

    model_number = line1 + line2
    serial_number = line3 + line4

# ==========================================
# NEW: ADD DEBUG LOGIC IF SERIAL IS EMPTY
# ==========================================
debug_log = ""
if not serial_number.strip():
    debug_log = "--- PRIMARY COMMAND RAW OUTPUT ---\n"
    debug_log += cmd_output_primary
    debug_log += "\n--- FALLBACK COMMAND RAW OUTPUT ---\n"
    if cmd_output_fallback:
        debug_log += cmd_output_fallback
    else:
        debug_log += "NOT RUN"

# ==========================================
# FINAL JSON 
# ==========================================
result = {
    "model_number": model_number,
    "serial_number": serial_number,
    "debug_info": debug_log
}

print(json.dumps(result))

