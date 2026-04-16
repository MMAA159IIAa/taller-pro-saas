from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from core import database
from models import models
from schemas import schemas
from api import router as api_router
from api import webhook as webhook_router

# Crear tablas en bd (Solo para SQLite local por ahora, en BD de Nube usa Alembic(Migraciones))
models.Base.metadata.create_all(bind=database.engine)

from fastapi.responses import HTMLResponse
import os

app = FastAPI(title="TallerPro SaaS API", version="1.0")
app.include_router(api_router.router, prefix="/api")
app.include_router(webhook_router.router, prefix="/api")

@app.get("/", response_class=HTMLResponse)
def read_root():
    return """
    <html>
        <body style='background:#0f172a; color:white; font-family:sans-serif; text-align:center; padding-top:100px;'>
            <h1>TallerPro API Central is Running</h1>
            <p>Accede al <a href='/admin' style='color:#38bdf8'>Panel Maestro</a></p>
        </body>
    </html>
    """

@app.get("/admin", response_class=HTMLResponse)
def admin_panel():
    path = os.path.join(os.path.dirname(__file__), "templates", "admin.html")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

# Los endpoints de Licencia y Activación ahora residen en /api/router.py
# para evitar conflictos de rutas.

# ==========================================
# GESTIÓN SaaS (Panel Admin tuyo)
# ==========================================
@app.post("/api/v1/admin/taller", response_model=schemas.Taller)
def create_taller(taller: schemas.TallerCreate, db: Session = Depends(database.get_db)):
    db_taller = models.Taller(nombre=taller.nombre)
    db.add(db_taller)
    db.commit()
    db.refresh(db_taller)
    return db_taller
