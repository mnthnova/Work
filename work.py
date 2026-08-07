if not problem_machines:
        html_table = "<p style='color: green; font-weight: bold; font-size: 16px;'>All setups are healthy today! No issues found.</p>"
    else:
        html_table = """
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
            html_table += f"""
              <tr>
                <td style="padding: 8px; border: 1px solid #ddd;">{row['IP Address']}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{row['Host Status']}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{row['Drive Status']}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{row['Serial Number']}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{row['Main Issue']}</td>
              </tr>
            """
        html_table += "</table>"

    # 7. COMPILE THE FINAL EMAIL BODY
    # We wrap yesterday's text inside a <pre> tag so the plain text table stays perfectly aligned!
    final_html_body = f"""
    <html>
      <head>
        <style>
          body {{ font-family: Arial, sans-serif; }}
          h2 {{ color: #333; }}
          h3 {{ margin-top: 30px; }}
          .yesterday-box {{ background-color: #f4f4f4; padding: 15px; border-radius: 5px; font-family: monospace; white-space: pre; overflow-x: auto; }}
        </style>
      </head>
      <body>
        <h2>Daily Drive Health Report</h2>
        
        <h3 style="color: #d9534f;">🚨 Today's Status</h3>
        {html_table}
        
        <hr style="margin-top: 40px; margin-bottom: 20px; border: 0; border-top: 1px solid #ccc;">
        
        <h3 style="color: #5bc0de;">🗓️ Yesterday's Status</h3>
        <div class="yesterday-box">{yesterday_report_text}</div>
      </body>
    </html>
    """
