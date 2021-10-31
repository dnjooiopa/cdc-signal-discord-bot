import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('API_KEY')
BOT_TOKEN = os.getenv('BOT_TOKEN')
CRYPTO_CHANNEL = os.getenv('CRYPTO_CHANNEL')

UNKNOWN_MESSAGE = os.getenv('UNKNOWN_MESSAGE')
WELCOME_MESSAGE = os.getenv('WELCOME_MESSAGE')

HOUR = os.getenv('HOUR')
MINUTE = os.getenv('MINUTE')
SECOND = os.getenv('SECOND')

ADMIN_ID = os.getenv('ADMIN_ID')