from app import app
from flask import request, redirect
import threading

print("Starting development server...")

# # Redirect HTTP → HTTPS
# @app.before_request
# def force_https():
#     if request.url.startswith("http://"):
#         url = request.url.replace("http://", "https://").replace(":8000", ":8443")
#         return redirect(url, code=301)

# def run_http():
#     app.run(
#         host="0.0.0.0",
#         port=8000,
#         debug=True,
#         use_reloader=False
#     )

# def run_https():
#     app.run(
#         host="0.0.0.0",
#         port=8443,
#         debug=True,
#         use_reloader=False,
#         ssl_context=("cert.pem", "server.key")
#     )

# if __name__ == "__main__":
#     threading.Thread(target=run_http).start()
#     threading.Thread(target=run_https).start()

app.run(
    host="0.0.0.0",
    port=8000,
    debug=False,
    ssl_context=("cert.pem", "server.key")
)