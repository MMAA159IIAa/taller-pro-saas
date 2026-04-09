from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
import datetime
from dateutil.relativedelta import relativedelta
from core import database
from models import models
from schemas import schemas

router = APIRouter()

# ==========================================
# GESTIÓN SaaS: DASHBOARD KPIs
# ==========================================
@router.get("/v1/dashboard/{taller_id}")
def get_dashboard_kpis(taller_id: int, db: Session = Depends(database.get_db)):
    """
    Retorna toda la matemática pre-procesada para la pantalla principal de un Taller.
    En lugar de hacer COUNT en el .exe cliente (lento y pesado), lo hace el motor DB en la nube.
    """
    # 1. Total Clientes (Registros Únicos de ese taller)
    total_clientes = db.query(models.Registro).filter(models.Registro.taller_id == taller_id).count()
    
    # 2. Servicios de Hoy
    hoy = datetime.datetime.utcnow().date()
    servicios_hoy = db.query(models.Registro).filter(
        models.Registro.taller_id == taller_id,
        func.date(models.Registro.fecha_ingreso) == hoy
    ).count()

    # 3. Finanzas del mes en curso
    primer_dia_mes = hoy.replace(day=1)
    
    ingresos = db.query(func.sum(models.Finanzas.monto)).filter(
        models.Finanzas.taller_id == taller_id,
        models.Finanzas.tipo == "Ingreso",
        models.Finanzas.fecha >= primer_dia_mes
    ).scalar() or 0.0

    egresos = db.query(func.sum(models.Finanzas.monto)).filter(
        models.Finanzas.taller_id == taller_id,
        models.Finanzas.tipo == "Egreso",
        models.Finanzas.fecha >= primer_dia_mes
    ).scalar() or 0.0
    
    # 4. Servicios vencidos (Mayores a 180 días que no han regresado)
    # Por ahora contamos registros donde fecha de ingreso fue hace mas de 6 meses
    fecha_6_meses = hoy - relativedelta(months=6)
    vencidos = db.query(models.Registro).filter(
        models.Registro.taller_id == taller_id,
        models.Registro.fecha_ingreso <= fecha_6_meses
    ).count()

    return {
        "kpis": {
            "clientes": total_clientes,
            "hoy": servicios_hoy,
            "ingresos": ingresos,
            "egresos": egresos,
            "balance": ingresos - egresos,
            "vencidos": vencidos
        }
    }

# ==========================================
# CRM: REGISTROS Y VENTAS
# ==========================================
@router.get("/v1/registros/{taller_id}")
def get_registros(taller_id: int, db: Session = Depends(database.get_db)):
    """Devuelve los últimos servicios para la tabla principal"""
    registros = db.query(models.Registro).filter(models.Registro.taller_id == taller_id).order_by(models.Registro.id.desc()).limit(50).all()
    # Mapeo a lista de tuplas para retro-compatibilidad rápida con Tkinter TreeView
    return [
        (r.nombre_cliente, r.vehiculo, r.servicio, r.fecha_ingreso.strftime("%Y-%m-%d"), r.costo_proyectado, r.estado)
        for r in registros
    ]
