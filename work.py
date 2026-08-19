def load_and_flatten_data(filepath):
    """Reads the JSON and flattens it into a simple dictionary {ip: {details}} for easy comparison"""
    if not os.path.exists(filepath):
        return {}
        
    try:
        with open(filepath, 'r') as file:
            data = json.load(file)
    except:
        return {}
        
    flat_data = {}
    for host_entry in data:
        for json_ip_key, host_details in host_entry.items():
            ip = host_details.get("ip_address", json_ip_key)
            flat_data[ip] = {
                "status": host_details.get("status", ""),
                "drive_status": host_details.get("drive_status", "").strip(),
                "serial_number": host_details.get("serial_number", "").strip()
            }
    return flat_data

def generate_and_send_report():
    # 1. LOAD DATA FOR TODAY AND YESTERDAY
    today_data = load_and_flatten_data(TODAY_JSON)
    yesterday_data = load_and_flatten_data(YESTERDAY_JSON)

    if not today_data:
        print(f"Error: {TODAY_JSON} not found or empty.")
        return

    # 2. COMPARE DATA (Find what changed)
    changes_found = []
    
    for ip, today_info in today_data.items():
        yesterday_info = yesterday_data.get(ip)
        
        # If the machine is brand new today and wasn't there yesterday
        if not yesterday_info:
            changes_found.append({
                "IP Address": ip,
                "Change Details": "NEW HOST ADDED TODAY"
            })
            continue

        diffs = []
        # Check Host Status
        if today_info["status"] != yesterday_info["status"]:
            diffs.append(f"Host: [{yesterday_info['status']} &rarr; {today_info['status']}]")
            
        # Check Drive Status
        if today_info["drive_status"] != yesterday_info["drive_status"]:
            old_drive = yesterday_info["drive_status"] if yesterday_info["drive_status"] else "EMPTY"
            new_drive = today_info["drive_status"] if today_info["drive_status"] else "EMPTY"
            diffs.append(f"Drive: [{old_drive} &rarr; {new_drive}]")
            
        # Check Serial Number
        if today_info["serial_number"] != yesterday_info["serial_number"]:
            old_serial = yesterday_info["serial_number"] if yesterday_info["serial_number"] else "EMPTY"
            new_serial = today_info["serial_number"] if today_info["serial_number"] else "EMPTY"
            diffs.append(f"Serial: [{old_serial} &rarr; {new_serial}]")

        # If we found any differences, add them to the report
        if diffs:
            changes_found.append({
                "IP Address": ip,
                "Change Details": " <br> ".join(diffs)
            })

    # 3. IDENTIFY ALL PROBLEM MACHINES TODAY (Just for the standard summary)
    problem_machines = []
    for ip, info in today_data.items():
        issues = []
        if info["status"] == "unreachable":
            issues.append("Host Unreachable")
        else:
            if info["drive_status"] == "" or info["drive_status"] == "not attached":
                issues.append("Drive Not Attached")
            if not info["serial_number"]:
                issues.append("Missing Serial Number")
                
        if issues:
            problem_machines.append({
                "IP Address": ip,
                "Host Status": info["status"],
                "Drive Status": info["drive_status"] if info["drive_status"] else "EMPTY",
                "Serial Number": info["serial_number"] if info["serial_number"] else "EMPTY",
                "Main Issue": " | ".join(issues)
            })

    # 4. BUILD THE HTML FOR "CHANGES SINCE YESTERDAY"
    if not changes_found:
        changes_html = "<p style='color: green;'>No hosts changed status since yesterday.</p>"
    else:
        changes_html = """
        <table style="width: 100%; border-collapse: collapse; font-family: Arial, sans-serif; margin-bottom: 30px;">
          <tr>
            <th style="background-color: #ffeeba; padding: 10px; border: 1px solid #ddd; text-align: left; width: 20%;">IP Address</th>
            <th style="background-color: #ffeeba; padding: 10px; border: 1px solid #ddd; text-align: left;">What Changed? (Yesterday &rarr; Today)</th>
          </tr>
        """
        for row in changes_found:
            changes_html += f"""
              <tr>
                <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">{row['IP Address']}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{row['Change Details']}</td>
              </tr>
            """
        changes_html += "</table>"

    # 5. BUILD THE HTML FOR "CURRENT BROKEN MACHINES"
    if not problem_machines:
        problems_html = "<p style='color: green;'>All setups are healthy today!</p>"
    else:
        problems_html = """
        <table style="width: 100%; border-collapse: collapse; font-family: Arial, sans-serif;">
          <tr>
            <th style="background-color: #f2f2f2; padding: 10px; border: 1px solid #ddd; text-align: left;">IP Address</th>
            <th style="background-color: #f2f2f2; padding: 10px; border: 1px solid #ddd; text-align: left;">Host Status</th>
            <th style="background-color: #f2f2f2; padding: 10px; border: 1px solid #ddd; text-align: left;">Drive Status</th>
            <th style="background-color: #f2f2f2; padding: 10px; border: 1px solid #ddd; text-align: left;">Serial Number</th>
            <th style="background-color: #f2f2f2; padding: 10px; border: 1px solid #ddd; text-align: left;">Main Issue</th>
          </tr>
        """
        for row in problem_machines:
            problems_html += f"""
              <tr>
                <td style="padding: 8px; border: 1px solid #ddd;">{row['IP Address']}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{row['Host Status']}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{row['Drive Status']}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{row['Serial Number']}</td>
                <td style="padding: 8px; border: 1px solid #ddd; color: #d9534f;">{row['Main Issue']}</td>
              </tr>
            """
        problems_html += "</table>"

    # 6. OVERWRITE YESTERDAY'S JSON WITH TODAY'S (For tomorrow's comparison)
    with open(YESTERDAY_JSON, 'w') as out_file:
        json.dump(today_data, out_file, indent=4)

    # 7. ASSEMBLE FINAL EMAIL
    final_html_body = f"""
    <html>
      <head>
        <style>body {{ font-family: Arial, sans-serif; }}</style>
      </head>
      <body>
        <h2>Daily Drive Health Report</h2>
        
        <h3 style="color: #f0ad4e;">🔄 Host Changes (Yesterday vs Today)</h3>
        {changes_html}
        
        <h3 style="color: #d9534f;">🚨 Currently Problematic Hosts</h3>
        {problems_html}
      </body>
    </html>
    """

    # 8. SEND EMAIL
    try:
        msg = EmailMessage()
        msg['Subject'] = f"Drive Report: {len(changes_found)} changed, {len(problem_machines)} currently broken"
        msg['From'] = SENDER_EMAIL
        msg['To'] = ", ".join(RECEIVER_EMAILS)
        msg.set_content("Please enable HTML to view this email.")
        msg.add_alternative(final_html_body, subtype='html')

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.send_message(msg)
            
        print("Email successfully sent with Comparison Table!")
        
    except Exception as e:
        print(f"Failed to send email. Error: {str(e)}")

if __name__ == "__main__":
    generate_and_send_report()
    
    
    
import subprocess
import os

def get_diff_output():
    """Runs git diff with 3 lines of context (-U3)."""
    try:
        return subprocess.check_output(['git', 'diff', '-U3', 'HEAD~1', 'HEAD'], text=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running git diff: {e}")
        return ""

def call_translation_api(text, target_lang):
    """Replace with your actual translation API call."""
    return f".. TRANSLATED TO {target_lang.upper()} ..\n{text}"

def process_hunk(file_path, target_path, target_lang, context_lines, added_lines):
    """Translates the block and injects it into the target file."""
    if not context_lines or not added_lines:
        return

    # Translate the new addition
    new_translated_text = call_translation_api('\n'.join(added_lines), target_lang)
    
    # Translate the context to find the anchor in the target file
    translated_context = [call_translation_api(line, target_lang) for line in context_lines]

    with open(target_path, 'r', encoding='utf-8') as f:
        target_file_lines = f.read().splitlines()

    # Search for the 3-line context block
    insertion_index = -1
    for i in range(len(target_file_lines) - len(translated_context)):
        if target_file_lines[i:i+len(translated_context)] == translated_context:
            insertion_index = i + len(translated_context)
            break

    if insertion_index != -1:
        # Inject the new text right after the context block
        target_file_lines.insert(insertion_index, new_translated_text)
        
        with open(target_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(target_file_lines) + '\n')
        print(f"Successfully synced hunk to {target_path}")
    else:
        print(f"WARNING: Could not find matching context block in {target_path}. Skipping hunk.")

def main():
    diff_text = get_diff_output()
    if not diff_text:
        return

    current_file = ""
    context_lines = []
    added_lines = []

    # A simplified parser to extract context and additions from the diff
    for line in diff_text.splitlines():
        if line.startswith('+++ b/'):
            # Trigger sync for the previous file before moving to the next
            current_file = line.replace('+++ b/', '')
            context_lines = []
            added_lines = []
        elif line.startswith(' ') and current_file:
            context_lines.append(line[1:]) # Keep context without the space
        elif line.startswith('+') and not line.startswith('+++'):
            added_lines.append(line[1:])
            
        # When we hit the end of a block, process it
        if added_lines and line.startswith((' ', '-', '@@')) and current_file:
            if current_file.startswith('content/') and current_file.endswith('.rst'):
                target = current_file.replace('content/', 'content_ja/', 1)
                os.makedirs(os.path.dirname(target), exist_ok=True)
                process_hunk(current_file, target, 'ja', context_lines[-3:], added_lines)
            
            added_lines = [] # Reset for the next addition in the same file

if __name__ == "__main__":
    main()

