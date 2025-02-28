from flask_mail import Mail, Message
import os

from app import app

# Email Configuration
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587  # Use 465 if SSL is needed
app.config["MAIL_USE_TLS"] = True  # Enable TLS
app.config["MAIL_USE_SSL"] = False  # Ensure SSL is disabled
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
app.config["MAIL_DEFAULT_SENDER"] = "no-reply@example.com"

mail = Mail(app)  # Initialize Flask-Mail

def send_email(subject, recipients, body):
    """
    Utility function to send emails.
    :param subject: Email subject
    :param recipients: List of recipients
    :param body: Email body (plain text)
    """
    try:
        msg = Message(subject, recipients=recipients)
        msg.body = body
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False