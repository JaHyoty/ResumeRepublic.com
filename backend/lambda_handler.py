"""
AWS Lambda handler for the FastAPI application.
Uses Mangum to adapt ASGI (FastAPI) to AWS Lambda events.
"""

from mangum import Mangum
from app.main import app

# Mangum adapter: converts API Gateway events to ASGI
handler = Mangum(app, lifespan="off")
