import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'your_secret_key')
    DEBUG = os.getenv('FLASK_DEBUG', 'True') == 'True'
    DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
    PLAYERS_FILE = os.path.join(DATA_DIR, 'players-2024.xlsx')
    EXCLUSION_FILE = os.path.join(DATA_DIR, 'exclusion.txt')
    MUST_INCLUDE_FILE = os.path.join(DATA_DIR, 'must_include.txt')
