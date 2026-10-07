"""
HealthMate AI - pika e nisjes.

Nise me:  python run.py
Pastaj hap shfletuesin në:  http://localhost:8000
"""
import os
import threading
import webbrowser

import uvicorn
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    url = f"http://localhost:{port}"
    print(f"\n  HealthMate AI po niset...  Hape në shfletues: {url}\n")
    # Hap shfletuesin automatikisht pas një sekonde
    threading.Timer(1.5, lambda: webbrowser.open(url)).start()
    uvicorn.run("backend.main:app", host="127.0.0.1", port=port, reload=False)
