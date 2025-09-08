from mangum import Mangum
from main import app

# Wrap FastAPI app with Mangum for serverless
handler = Mangum(app)
