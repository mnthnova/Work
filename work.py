#!/usr/bin/env python3

import os
import glob
import smtplib
from email.message import EmailMessage

# ==========================
# Configuration
# ==========================

EXCEL_DIR = "/path/to/excel/folder"

SMTP_SERVER = "smtp.company.com"
SMTP_PORT = 25

FROM_MAIL = "noreply@company.com"

TO_MAILS = [
    "you@company.com",
    "colleague@company.com"
]

# ==========================
# Find Excel File
# ==========================

excel_files = glob.glob(os.path.join(EXCEL_DIR, "*.xlsx"))

if len(excel_files) != 1:
    raise Exception(
        f"Expected exactly 1 Excel file. Found {len(excel_files)}"
    )

excel_file = excel_files[0]

# ==========================
# Create Mail
# ==========================

msg = EmailMessage()

msg["Subject"] = "Daily LAT Tracker"
msg["From"] = FROM_MAIL
msg["To"] = ", ".join(TO_MAILS)

msg.set_content(
    """Hello Team,

Please find attached the latest LAT tracker.

Regards,
LAT Automation
"""
)

# ==========================
# Attach Excel
# ==========================

with open(excel_file, "rb") as f:
    msg.add_attachment(
        f.read(),
        maintype="application",
        subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=os.path.basename(excel_file)
    )

# ==========================
# Send Mail
# ==========================

with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
    server.send_message(msg)

print("Mail sent successfully")
