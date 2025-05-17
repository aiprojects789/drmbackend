from mangum import Mangum
from app.main import app

# Explicitly expose the handler for Vercel
handler = Mangum(app, lifespan="off")  # Disable lifespan for ASGI apps