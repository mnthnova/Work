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
        # Wait up to 3 seconds for a command to finish, preventing Ansible race conditions
        self.max_read_time = 3.0 

    def run_serial_minicom(self, uart_device):
        try:
            serial_console = serial.Serial(port=uart_device, baudrate=self.baudrate, timeout=0.1)
        except Exception:
            return "" # Return empty string instead of crashing, keeping JSON output safe

        # 1. FLUSH BUFFERS: Destroy any old junk data before Ansible sends the command
        time.sleep(0.5)
        serial_console.reset_input_buffer()
        serial_console.reset_output_buffer()

        # 2. WAKE UP DRIVE: Send fast ESC characters
        for _ in range(3):
            serial_console.write(b"\x1b")
            time.sleep(0.1)
        serial_console.write(b"\r\n")
        time.sleep(0.2)
        serial_console.reset_input_buffer()

        # 3. SEND COMMAND
        serial_command = self.serial_command.strip() + "\r"
        serial_output = ""
        serial_console.write(serial_command.encode())
        
        # 4. ROBUST READ: Time-based loop instead of buffer-based
        start_time = time.time()
        
        while (time.time() - start_time) < self.max_read_time:
            if serial_console.in_waiting > 0:
                new_data = serial_console.read(serial_console.in_waiting).decode('utf-8', errors='ignore')
                serial_output += new_data
                
                # INSTANT EXIT 1: Bricked drive detected
                if "[SFROM] BOOT HEADER ERR" in new_data:
                    break
                
                # INSTANT EXIT 2: Drive printed "ok" prompt (Finished successfully)
                if re.search(r'ok\s*>', serial_output):
                    time.sleep(0.1) # Catch any straggling characters
                    if serial_console.in_waiting > 0:
                        serial_output += serial_console.read(serial_console.in_waiting).decode('utf-8', errors='ignore')
                    break
            else:
                time.sleep(0.05)

        serial_console.close()
        return serial_output


def run_serial_cmd(serial_command):
    uart_device = "/dev/ttyUSB0"
    serial_obj = UART(serial_command)
    
    if stat.S_ISCHR(os.stat(uart_device).st_mode):
        return serial_obj.run_serial_minicom(uart_device)
    return "" # Keeps script alive so fallback can run gracefully


# ==========================================
# 1st ATTEMPT: PRIMARY COMMAND
# ==========================================
cmd_output = run_serial_cmd(COMMAND_PRIMARY)
clean_output = cmd_output.replace("\0", "")
uart_ascii_lines = []

for line in clean_output.splitlines():
    # Looking for primary memory address
    if re.match(r'^208a[0-9a-fA-F]{4}:', line, re.IGNORECASE):
        parts = re.split(r'\s{2,}', line)
        if len(parts) > 1:
            ascii_part = parts[-1].strip().replace(".", "")
            if ascii_part:
                uart_ascii_lines.append(ascii_part)
            else:
                uart_ascii_lines.append("")

while len(uart_ascii_lines) < 4:
    uart_ascii_lines.append("")

model_number = uart_ascii_lines[0] + uart_ascii_lines[1]
serial_number = uart_ascii_lines[2] + uart_ascii_lines[3]


# ==========================================
# 2nd ATTEMPT: FALLBACK COMMAND
# ==========================================
# If primary failed, try the fallback address
if not model_number.strip() and not serial_number.strip():
    cmd_output = run_serial_cmd(COMMAND_FALLBACK)
    clean_output = cmd_output.replace("\0", "")
    uart_ascii_lines = []

    for line in clean_output.splitlines():
        # Looking for fallback memory address
        if re.match(r'^208f[0-9a-fA-F]{4}:', line, re.IGNORECASE):
            parts = re.split(r'\s{2,}', line)
            if len(parts) > 1:
                ascii_part = parts[-1].strip().replace(".", "")
                if ascii_part:
                    uart_ascii_lines.append(ascii_part)
                else:
                    uart_ascii_lines.append("")

    while len(uart_ascii_lines) < 4:
        uart_ascii_lines.append("")

    model_number = uart_ascii_lines[0] + uart_ascii_lines[1]
    serial_number = uart_ascii_lines[2] + uart_ascii_lines[3]


# ==========================================
# FINAL JSON OUTPUT (For Ansible to Parse)
# ==========================================
result = {
    "model_number": model_number,
    "serial_number": serial_number
}

print(json.dumps(result))
