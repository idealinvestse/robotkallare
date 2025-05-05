import logging
import smtplib
from email.message import EmailMessage
from app.config import get_settings

logger = logging.getLogger("alerting")

# Simple email alert function (expand as needed)
def send_alert_email(subject: str, body: str):
    settings = get_settings()
    smtp_host = getattr(settings, "ALERT_SMTP_HOST", None)
    smtp_port = getattr(settings, "ALERT_SMTP_PORT", 587)
    smtp_user = getattr(settings, "ALERT_SMTP_USER", None)
    smtp_pass = getattr(settings, "ALERT_SMTP_PASS", None)
    to_addr = getattr(settings, "ALERT_EMAIL_TO", None)
    from_addr = getattr(settings, "ALERT_EMAIL_FROM", smtp_user)
    if not all([smtp_host, smtp_user, smtp_pass, to_addr, from_addr]):
        logger.warning("Alert email not sent: SMTP config missing.")
        return False
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg.set_content(body)
    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        logger.info(f"Alert email sent to {to_addr}")
        return True
    except Exception as e:
        logger.error(f"Failed to send alert email: {e}")
        return False
