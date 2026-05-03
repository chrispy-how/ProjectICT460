import os
from dotenv import load_dotenv

load_dotenv()

DEBUG = False
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_SAMESITE = "Lax"

SECRET_KEY = os.getenv("SECRET_KEY")
