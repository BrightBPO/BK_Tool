from flask_mail import Message
from app import mail

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