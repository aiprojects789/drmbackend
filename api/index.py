from app.main import app
from mangum import Mangum

# Create Mangum handler for Vercel
handler = Mangum(app)