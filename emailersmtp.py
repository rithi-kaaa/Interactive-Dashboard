import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os


def send_email_with_attachment(sender_email, receiver_email, subject, body, attachment_path, smtp_server='smtp.gmail.com', smtp_port=587):
    # Create the email
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject
    app_password = 'alnboejzxzjndjgp'  # Replace with your actual App Password


    # Attach the body message
    msg.attach(MIMEText(body, 'plain'))

    # Attach the PDF report
    attachment = open(attachment_path, "rb")
    part = MIMEBase('application', 'octet-stream')
    part.set_payload((attachment).read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', f"attachment; filename= {attachment_path}")
    msg.attach(part)

    # Send the email
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(sender_email, app_password)  # Replace with your email password or better, use environment variables
    text = msg.as_string()
    server.sendmail(sender_email, receiver_email, text)
    server.quit()

# Example usage:
# send_email_with_attachment("sender@example.com", "receiver@example.com", "Your Carbon Emissions Report", "Here is the report.", "report.pdf")