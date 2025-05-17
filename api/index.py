from mangum import Mangum
from app.main import app

# The absolute key to solving this - use this exact format
handler = Mangum(app, lifespan="off")