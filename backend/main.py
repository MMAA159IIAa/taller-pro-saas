from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from core import database
from models import models
from schemas import schemas
from api import router as api_router
from api import webhook as webhook_router

# Crear tablas en bd (Solo para SQLite local por ahora, en BD de Nube usa Alembic(Migraciones))
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="TallerPro SaaS API", version="1.0")
app.include_router(api_router.router, prefix="/api")
app.include_router(webhook_router.router, prefix="/api")

@app.get("/")
def read_root():
    return {"status": "ok", "message": "API TallerPro Central is running"}

# ==========================================
# 🛑 KILL-SWITCH & LICENSES (Para el .exe)
# ==========================================
@app.get("/api/v1/license/check/{taller_id}", response_model=schemas.LicenseCheck)
def check_license(taller_id: int, db: Session = Depends(database.get_db)):
    """
    Este endpoint será consultado por tu programa Tkinter (.exe) cada vez que abra.
    """
    taller = db.query(models.Taller).filter(models.Taller.id == taller_id).first()
    
    if not taller:
        # Si alguien copió el .exe pero no existe en tu base de datos central
        raise HTTPException(status_code=404, detail="Taller no registrado en la central.")

    if not taller.suscripcion_activa:
        # ⚠️ EL KILL SWITCH
        return schemas.LicenseCheck(
            taller_id=taller.id,
            taller_name=taller.nombre,
            status="suspendido",
            mensaje="Su suscripción ha finalizado. Por favor realice el pago de la mensualidad para continuar usando TallerPro."
        )

    # Si todo está en orden
    return schemas.LicenseCheck(
        taller_id=taller.id,
        taller_name=taller.nombre,
        status="activo",
        mensaje="Licencia válida.",
        fecha_vencimiento=taller.fecha_vencimiento
    )

# ==========================================
# 🔑 ACTIVACIÓN (Primera vez)
# ==========================================
@app.get("/api/v1/license/activate/{key}")
def activate_license(key: str, db: Session = Depends(database.get_db)):
    """
    TallerPro llamará aquí la primera vez para activar su copia con la clave.
    """
    taller = db.query(models.Taller).filter(models.Taller.activation_key == key).first()
    
    if not taller:
        raise HTTPException(status_code=403, detail="Clave de activación inválida.")
        
    if not taller.suscripcion_activa:
        raise HTTPException(status_code=403, detail="Esta clave ha sido suspendida.")

    return {
        "taller_id": taller.id,
        "taller_name": taller.nombre,
        "fecha_vencimiento": taller.fecha_vencimiento,
        "status": "activo"
    }

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
