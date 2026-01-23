Backend
cd "/Users/pratikkumar/Desktop/Antenna Digital Twin/backend" && export PYTHONPATH="/Users/pratikkumar/Desktop/Antenna Digital Twin:$PYTHONPATH" && python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

Frontend
cd "/Users/pratikkumar/Desktop/Antenna Digital Twin/frontend" && npm run dev