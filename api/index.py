import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from mangum import Mangum
from main import app

# Wrap FastAPI app with Mangum for serverless
handler = Mangum(app, lifespan="off")
