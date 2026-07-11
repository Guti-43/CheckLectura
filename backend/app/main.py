from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .db import init_db
from .routes import router

app = FastAPI(title='CheckLectura', version='1.0.0')
static_dir = Path(__file__).parent / 'static'
app.mount('/static', StaticFiles(directory=str(static_dir)), name='static')
app.include_router(router)


@app.on_event('startup')
def startup() -> None:
    init_db()


@app.get('/health')
def health() -> dict[str, str]:
    return {'status': 'ok'}
