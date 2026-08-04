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
        # 1. Capture Port Open Errors
        try:
            serial_console = serial.Serial(port=uart_device, baudrate=self.baudrate)
        except Exception as e:
            return f"[PORT ERROR: Could not open {uart_device} - {str(e)}]"

        # Sending ESC character to UART (Using your proven 2-second delays)
        for _ in range(0, 2):
            serial_console.write(b"\x1b")
            time.sleep(2)
        time.sleep(2)

        serial_command = self.serial_command.strip() + "\r"
        serial_output = ""
        
        serial_console.write(serial_command.encode())
        time.sleep(2) # Give drive time to fetch memory
        rx_buf_bytes = serial_console.in_waiting

        loops = 0
        max_loops = 10 # 10 loops max to prevent infinite hanging

        while rx_buf_bytes != 0 and loops < max_loops:
            time.sleep(self.timeout)
            rx_buf_bytes = serial_console.in_waiting
            
            if rx_buf_bytes > 0:
                new_data = serial_console.read(rx_buf_bytes).decode('utf-8', errors='ignore')
                serial_output += new_data
                
                # Exit early if bricked drive spam is detected
                if "[SFROM] BOOT HEADER ERR" in new_data:
                    break
            loops += 1

        serial_console.close()
        
        # 2. Capture if port opened but drive sent nothing
        if not serial_output.strip():
            return "[NO DATA RECEIVED: Port opened, but drive stayed silent]"
            
        return serial_output

def run_serial_cmd(serial_command):
    uart_device = "/dev/ttyUSB0"
    serial_obj = UART(serial_command)
    
    if stat.S_ISCHR(os.stat(uart_device).st_mode):
        return serial_obj.run_serial_minicom(uart_device)
    return f"[DEVICE ERROR: {uart_device} does not exist or is not configured]"

def extract_info(raw_output, address_pattern):
    # If the output is one of our custom error messages, skip parsing
    if not raw_output or raw_output.startswith("["): 
        return "", ""
        
    clean_output = raw_output.replace("\0", "")
    uart_ascii_lines = []

    for line in clean_output.splitlines():
        if re.match(address_pattern, line, re.IGNORECASE):
            parts = re.split(r'\s{2,}', line)
            if len(parts) > 1:
                ascii_part = parts[-1].strip().replace(".", "")
                if ascii_part:
                    uart_ascii_lines.append(ascii_part)
                else:
                    uart_ascii_lines.append("")

    while len(uart_ascii_lines) < 4:
        uart_ascii_lines.append("")

    model = (uart_ascii_lines[0] + uart_ascii_lines[1]).strip()
    serial = (uart_ascii_lines[2] + uart_ascii_lines[3]).strip()
    return model, serial

# ==========================================
# 1st ATTEMPT: PRIMARY COMMAND
# ==========================================
primary_raw = run_serial_cmd(COMMAND_PRIMARY)
model, serial = extract_info(primary_raw, r'^208a[0-9a-fA-F]{4}:')

# ==========================================
# 2nd ATTEMPT: FALLBACK COMMAND
# ==========================================
fallback_raw = ""
if not model and not serial:
    fallback_raw = run_serial_cmd(COMMAND_FALLBACK)
    model, serial = extract_info(fallback_raw, r'^208f[0-9a-fA-F]{4}:')

# ==========================================
# DEBUGGER: Build the "Cat File" Output
# ==========================================
debug_log = ""
if not model and not serial:
    debug_log = (
        f"\n--- UART DEBUG INFO ---\n"
        f"PRIMARY CMD RUN:\n{primary_raw}\n"
        f"-----------------------\n"
        f"FALLBACK CMD RUN:\n{fallback_raw if fallback_raw else 'NOT RUN'}\n"
        f"-----------------------\n"
    )

# ==========================================
# FINAL JSON OUTPUT
# ==========================================
result = {
    "model_number": model,
    "serial_number": serial,
    "debug_info": debug_log
}

print(json.dumps(result))
