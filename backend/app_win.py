from waitress import serve
from app import app

print("Starting production server with Waitress...")

serve(
    app,
    host="127.0.0.1",
    port=8000,
    threads=8
)