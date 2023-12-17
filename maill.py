import os
import smtplib
from email.mime.text import MIMEText
from email.utils import formatdate
from datetime import datetime
import pytz  # For handling timezones
from dotenv import load_dotenv
load_dotenv()
class SendErrorMail():
    def __init__(self,system_no=os.getenv('SYSTEM_NO'),subject='This is an email sent from Instagram bot',body=''):
        self.send_email(subject,system_no,body)

    def send_email(self,subject,system_no,body):
        sender_email = os.getenv('SENDER_MAIL')
        sender_password = os.getenv('SENDER_PASSWORD')
        # sender_password = os.getenv('SENDER_PASSWORD')
        receiver_email = os.getenv('RECEIVER_MAIL')

        # Get current time in IST timezone
        ist = pytz.timezone('Asia/Kolkata')  # IST timezone
        current_time = datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S %Z%z')

        # Include date and time in the email body
        body = body+f"\n\nCurrent IST Time: {current_time}"

        message = MIMEText(body)
        message["Subject"] = 'PC number : '+str(system_no)+' '+subject
        message["From"] = sender_email
        message["To"] = receiver_email
        message["Date"] = formatdate(localtime=True)  # Set the email's date

        # Send email
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, message.as_string())

        print("Email sent successfully.")

# Usage
# SendErrorMail()
