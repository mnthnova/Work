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



import json
import smtplib
from email.message import EmailMessage

# ==========================================
# CONFIGURATION
# ==========================================
JSON_FILE = "output.json"
REPORT_FILE = "failed_drives_report.txt"

# Email Settings
SENDER_EMAIL = "your_sender_email@gmail.com"
SENDER_PASSWORD = "your_app_password_here" 
RECEIVER_EMAIL = "your_receiver_email@company.com"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465

def generate_and_send_report():
    # 1. Read JSON
    try:
        with open(JSON_FILE, 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        print(f"Error: {JSON_FILE} not found.")
        return

    # 2. Filter for problem machines
    problem_machines = []
    
    for host in data:
        ip = host.get("ip_address", "Unknown")
        status = host.get("status", "")
        drive_status = host.get("drive_status", "")
        serial = host.get("serial_number", "").strip()
        
        issues = []
        if status == "unreachable":
            issues.append("Host Unreachable")
        else:
            if drive_status != "attached":
                issues.append("Drive Not Attached")
            if not serial:
                issues.append("Missing Serial Number")
                
        if issues:
            problem_machines.append({
                "IP Address": ip,
                "Host Status": status,
                "Drive Status": drive_status if drive_status else "N/A",
                "Serial Number": serial if serial else "EMPTY",
                "Main Issue": " | ".join(issues)
            })

    if not problem_machines:
        print("All machines are healthy! No report needed.")
        return

    # 3. Generate plain text table (to save in the file)
    headers = ["IP Address", "Host Status", "Drive Status", "Serial Number", "Main Issue"]
    col_widths = {h: len(h) for h in headers}
    for row in problem_machines:
        for h in headers:
            col_widths[h] = max(col_widths[h], len(str(row[h])))
            
    separator = "-" * (sum(col_widths.values()) + (len(headers) * 3) + 1)
    text_table = "DAILY DRIVE HEALTH REPORT\n" + separator + "\n"
    text_table += "| " + " | ".join(h.ljust(col_widths[h]) for h in headers) + " |\n"
    text_table += separator + "\n"
    for row in problem_machines:
        text_table += "| " + " | ".join(str(row[h]).ljust(col_widths[h]) for h in headers) + " |\n"
    text_table += separator + "\n"

    with open(REPORT_FILE, 'w') as out_file:
        out_file.write(text_table)
    print(f"Saved text report to {REPORT_FILE}")

    # 4. Generate HTML table (for the email body)
    html_table = """
    <html>
      <head>
        <style>
          table { width: 100%; border-collapse: collapse; font-family: Arial, sans-serif; }
          th { background-color: #f2f2f2; color: #333; font-weight: bold; padding: 10px; border: 1px solid #ddd; text-align: left; }
          td { padding: 8px; border: 1px solid #ddd; text-align: left; }
          tr:nth-child(even) { background-color: #f9f9f9; }
          h2 { font-family: Arial, sans-serif; color: #d9534f; }
        </style>
      </head>
      <body>
        <h2>Daily Drive Health Report</h2>
        <p>The following machines require attention:</p>
        <table>
          <tr>
            <th>IP Address</th>
            <th>Host Status</th>
            <th>Drive Status</th>
            <th>Serial Number</th>
            <th>Main Issue</th>
          </tr>
    """
    
    for row in problem_machines:
        html_table += f"""
          <tr>
            <td>{row['IP Address']}</td>
            <td>{row['Host Status']}</td>
            <td>{row['Drive Status']}</td>
            <td>{row['Serial Number']}</td>
            <td>{row['Main Issue']}</td>
          </tr>
        """
        
    html_table += """
        </table>
      </body>
    </html>
    """

    # 5. Send Email with HTML Body
    try:
        msg = EmailMessage()
        msg['Subject'] = f"ALERT: Drive Health Report ({len(problem_machines)} issues found)"
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECEIVER_EMAIL
        
        # Set a plain text fallback, then add the HTML body
        msg.set_content("Please enable HTML to view this email.")
        msg.add_alternative(html_table, subtype='html')

        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
            
        print("HTML Email successfully sent!")
        
    except Exception as e:
        print(f"Failed to send email. Error: {str(e)}")

if __name__ == "__main__":
    generate_and_send_report()

