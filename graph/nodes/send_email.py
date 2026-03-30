import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from graph.state import State

logger = logging.getLogger(__name__)


def send_email(state: State) -> dict:
    sender = os.environ["GMAIL_ADDRESS"]
    password = os.environ["GMAIL_APP_PASSWORD"]
    recipient = os.environ["GMAIL_ADDRESS"]

    msg = MIMEMultipart("alternative")
    msg["Subject"] = state["subject"]
    msg["From"] = sender
    msg["To"] = recipient

    msg.attach(MIMEText(state["markdown_content"], "plain", "utf-8"))
    msg.attach(MIMEText(state["html_content"], "html", "utf-8"))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, recipient, msg.as_string())

    logger.info("邮件已发送: %s -> %s", state["subject"], recipient)
    return {}
