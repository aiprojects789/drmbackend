from mangum import Mangum
from app.main import app

# The key is to wrap the app in Mangum and expose it as 'handler'
handler = Mangum(app)

# Alternative explicit version if above doesn't work:
# def handler(event, context):
#     mangum_handler = Mangum(app)
#     return mangum_handler(event, context)