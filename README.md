# Admin Panel (local network / partial isolation) 
python app_backend.py --port 5001 --host 0.0.0.0

# Admin Panel (local device(server) / total isolation) 
python app_backend.py --port 5001 --host 127.0.0.1

# Front End 
python app_frontend.py --port 5000 --host 0.0.0.0 