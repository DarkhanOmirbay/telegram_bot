import os
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN', '')
admin_str = os.getenv("ADMIN_IDS","")
ADMIN_IDS = [int(x) for x in admin_str.split(",") if x]

GOOGLE_CREDENTIALS_PATH = os.getenv('GOOGLE_CREDENTIALS_PATH', 'google_credentials.json')
GOOGLE_SPREADSHEET_NAME = os.getenv('GOOGLE_SPREADSHEET_NAME', 'SignContract Leads')

if BOT_TOKEN == '':
    raise ValueError("Пожалуйста, установите BOT_TOKEN в файле .env")