"""
HealthMate AI - aplikacioni kryesor (FastAPI).

Ky skedar:
  - krijon aplikacionin web,
  - lidh të gjitha "routers" (pjesët e API-së),
  - shërben frontendin (HTML/CSS/JS) nga dosja /frontend.
"""
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

load_dotenv()

from .database import init_db  # noqa: E402
from .routers import chat, labs, profile, symptoms, therapies, who  # noqa: E402

FRONTEND = Path(__file__).resolve().parent.parent / "frontend"

app = FastAPI(title="HealthMate AI", description="Asistenti personal i shëndetit", version="1.0")

init_db()

for r in (profile.router, labs.router, therapies.router, symptoms.router, chat.router, who.router):
    app.include_router(r)

app.mount("/static", StaticFiles(directory=FRONTEND), name="static")


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(FRONTEND / "index.html")
