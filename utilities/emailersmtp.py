## credits: http://linuxcursor.com/python-programming/06-how-to-send-pdf-ppt-attachment-with-html-body-in-python-script
## https://devpress.csdn.net/python/63045e9fc67703293080bf35.html
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib

def sendEmailWithPdf(sender_email, sender_password, subject, messageHtml, recipients, path_to_pdf):
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(sender_email, sender_password)
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = ", ".join(recipients)

    content = MIMEText(messageHtml, "html")
    msg.attach(content)

    # Attach the pdf to the msg going by e-mail
    with open(path_to_pdf, "rb") as f:
        attach = MIMEApplication(f.read(), _subtype="pdf")
    attach.add_header('Content-Disposition', 'attachment', filename=str(path_to_pdf.split("/")[-1]))
    msg.attach(attach)
    server.send_message(msg)


# sender_email = "mmreporting339509@gmail.com"
# sender_password = "xxx"
# subject = "AMC-OEEReport-2023-05-24 18:00"
# message = ""
# recipients = ["chawchia@hotmail.co.uk"]
# path_to_pdf = "/Users/ryo.chia/Downloads/cdb47836f83442cc4ed4252069d0e2dc.pdf"
# sendEmailWithPdf(sender_email, sender_password, subject, message, recipients, path_to_pdf)