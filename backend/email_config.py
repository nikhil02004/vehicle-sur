import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Email Configuration
# All sensitive data is now loaded from .env file

# Sender email (the Gmail account that will send alerts)
EMAIL_SENDER = os.getenv('EMAIL_SENDER')

# Gmail app password (loaded from environment)
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')

# Receiver email (where alerts will be sent)
EMAIL_RECEIVER = os.getenv('EMAIL_RECEIVER')

# SMTP Configuration (Gmail settings)
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))

# Email Settings
EMAIL_ENABLED = os.getenv('EMAIL_ENABLED', 'true').lower() == 'true'
