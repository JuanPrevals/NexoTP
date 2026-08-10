"""Gateway ASGI de NexoTP.

FastAPI expone la salud de la API y aloja la aplicacion Flask existente mediante
WSGI. Esto permite migrar el cliente a React sin duplicar ni debilitar las
reglas de negocio que ya viven en Flask/SQLAlchemy.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from a2wsgi import WSGIMiddleware

from .core.config import settings
from .legacy import app as flask_app


app = FastAPI(title="API NexoTP", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.allowed_origins),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Accept", "Content-Type", "X-Requested-With", "X-CSRF-Token"],
)


@app.get("/api/health")
def health():
    return {"ok": True, "service": "NexoTP"}


app.mount("/", WSGIMiddleware(flask_app))
