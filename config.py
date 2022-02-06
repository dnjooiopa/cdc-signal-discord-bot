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

ADMIN_ID = int(os.getenv('ADMIN_ID'))
DAYS = int(os.getenv('DAYS'))

MQTT_USERNAME = os.getenv('MQTT_USERNAME')
MQTT_PASSWORD = os.getenv('MQTT_PASSWORD')
MQTT_HOST = os.getenv('MQTT_HOST')
MQTT_PORT = os.getenv('MQTT_PORT')