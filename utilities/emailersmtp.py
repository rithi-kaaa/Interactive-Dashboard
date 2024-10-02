import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os

def send_email_with_attachment(receiver_email, subject, body, attachment_path):
    sender_email = "i40nervecentre@gmail.com"
    sender_password = "mp5group2024"

    # Setting up the MIME structure
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject

    # Body of the email
    msg.attach(MIMEText(body, 'plain'))

    # Attachment
    attachment = open(attachment_path, "rb")
    part = MIMEBase('application', 'octet-stream')
    part.set_payload(attachment.read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', f"attachment; filename= {os.path.basename(attachment_path)}")
    msg.attach(part)

    # Connecting to Gmail SMTP server
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, receiver_email, text)
        server.quit()
        print(f"Email successfully sent to {receiver_email}")
    except Exception as e:
        print(f"Failed to send email to {receiver_email}. Error: {str(e)}")