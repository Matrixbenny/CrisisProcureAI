from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="CrisisProcure Web Portal", version="1.0.0")

UI_DIR = Path(__file__).resolve().parents[1] / "ui"

app.mount("/ui", StaticFiles(directory=UI_DIR), name="ui")


@app.get("/")
def home() -> FileResponse:
    return FileResponse(UI_DIR / "index.html")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "web-portal"}
