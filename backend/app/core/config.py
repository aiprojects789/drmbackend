from dotenv import load_dotenv
import os
load_dotenv()

MODE = os.getenv("PAYPAL_MODE", "sandbox")
CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
SECRET = os.getenv("PAYPAL_SECRET")
BASE = os.getenv("PAYPAL_BASE_SANDBOX") if MODE == "sandbox" else os.getenv("PAYPAL_BASE_LIVE")
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
WEBHOOK_ID = os.getenv("WEBHOOK_ID")
