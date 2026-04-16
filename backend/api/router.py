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
# 🛑 VALIDACIÓN SaaS (Escudo Oficial) - PRIORIDAD 1
# ==========================================
@router.get("/v1/license/check/{taller_id}")
def check_license(taller_id: int, hw_id: str, pc_name: str = "Desconocido", db: Session = Depends(database.get_db)):
    """Validación del .exe con transferencia automática de dueño si la PC cambia de licencia"""
    print(f"\n[🛡️ SaaS] CONSULTA DE LICENCIA Recibida -> Taller ID: {taller_id} | HW_ID: {hw_id}")
    taller = db.query(models.Taller).filter(models.Taller.id == taller_id).first()
    if not taller:
        print(f"[!] Taller {taller_id} no encontrado en DB central.")
        return {"status": "error", "mensaje": "Taller no registrado"}

    hw_id = hw_id.strip()
    device = db.query(models.Dispositivo).filter(models.Dispositivo.hw_id == hw_id).first()
    
    if not device:
        count = db.query(models.Dispositivo).filter(models.Dispositivo.taller_id == taller_id).count()
        limite = 1 if taller.plan == "Basico" else 5
        if count >= limite:
             return {"status": "limite_alcanzado", "mensaje": f"Límite de {limite} PCs alcanzado"}
        device = models.Dispositivo(taller_id=taller_id, hw_id=hw_id, nombre_pc=pc_name)
        db.add(device)
    else:
        device.taller_id = taller_id
        device.ultima_conexion = datetime.datetime.utcnow()
        device.nombre_pc = pc_name

    db.commit()

    if not taller.suscripcion_activa:
        print(f"[🚫 KILL-SWITCH] Acceso BLOCK para Taller: {taller.nombre}")
        return {"status": "suspendido", "mensaje": "Su suscripción ha sido SUSPENDIDA (Falta de Pago)."}

    print(f"[✅ OK] Taller {taller.nombre} autorizado.")
    return {"status": "activo", "taller_name": taller.nombre}

@router.get("/v1/license/activate/{key}")
def activate_license(key: str, hw_id: str, pc_name: str = "PC Nueva", db: Session = Depends(database.get_db)):
    """Activación y vinculación inicial de Hardware"""
    print(f"\n[✨ SaaS] SOLICITUD DE ACTIVACIÓN: Key={key} | PC={pc_name}")
    taller = db.query(models.Taller).filter(models.Taller.activation_key == key).first()
    if not taller:
        raise HTTPException(status_code=403, detail="Llave inválida")
    if not taller.suscripcion_activa:
        raise HTTPException(status_code=403, detail="Esta llave está suspendida")

    hw_id = hw_id.strip()
    device = db.query(models.Dispositivo).filter(models.Dispositivo.hw_id == hw_id).first()
    
    if not device:
        count = db.query(models.Dispositivo).filter(models.Dispositivo.taller_id == taller.id).count()
        limite = 1 if taller.plan == "Basico" else 5
        if count >= limite:
            raise HTTPException(status_code=403, detail="Límite de PCs para esta licencia alcanzado")
        device = models.Dispositivo(taller_id=taller.id, hw_id=hw_id, nombre_pc=pc_name)
        db.add(device)
    else:
        device.taller_id = taller.id
        device.nombre_pc = pc_name
        device.ultima_conexion = datetime.datetime.utcnow()
        
    db.commit()
    print(f"[🎉 ÉXITO] Licencia activada para: {taller.nombre}")
    return {"taller_id": taller.id, "taller_name": taller.nombre, "status": "activo"}

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
    return [
        (r.nombre_cliente, r.vehiculo, r.servicio, r.fecha_ingreso.strftime("%Y-%m-%d"), r.costo_proyectado, r.estado)
        for r in registros
    ]


# ==========================================
# ADMIN: GESTIÓN DE LICENCIAS (protegido)
# ==========================================
import uuid
from fastapi import Header

ADMIN_SECRET = os.getenv("X_ADMIN_SECRET", "tallerpro-admin-2026")

def _verificar_admin(x_admin_secret: str = Header(None)):
    if x_admin_secret != ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Acceso denegado")

@router.post("/v1/admin/crear-taller")
def admin_crear_taller(data: dict, db: Session = Depends(database.get_db),
                       x_admin_secret: str = Header(None)):
    _verificar_admin(x_admin_secret)
    clave = str(uuid.uuid4())[:8].upper()
    meses = data.get("meses", 1)
    vencimiento = datetime.datetime.utcnow() + datetime.timedelta(days=30 * meses)
    nuevo = models.Taller(
        nombre=data.get("nombre", "Sin nombre"),
        activation_key=clave,
        fecha_vencimiento=vencimiento,
        suscripcion_activa=True,
        plan=data.get("plan", "Basico")
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return {
        "id": nuevo.id,
        "nombre": nuevo.nombre,
        "activation_key": clave,
        "fecha_vencimiento": vencimiento.strftime("%d/%m/%Y"),
        "plan": nuevo.plan
    }

@router.get("/v1/admin/talleres")
def admin_listar_talleres(db: Session = Depends(database.get_db),
                          x_admin_secret: str = Header(None)):
    _verificar_admin(x_admin_secret)
    talleres = db.query(models.Taller).all()
    return [
        {
            "id": t.id,
            "nombre": t.nombre,
            "activation_key": t.activation_key,
            "suscripcion_activa": t.suscripcion_activa,
            "fecha_vencimiento": str(t.fecha_vencimiento) if t.fecha_vencimiento else None,
            "plan": t.plan
        }
        for t in talleres
    ]

@router.post("/v1/admin/toggle-taller/{taller_id}")
def admin_toggle_taller(taller_id: int, db: Session = Depends(database.get_db),
                        x_admin_secret: str = Header(None)):
    _verificar_admin(x_admin_secret)
    t = db.query(models.Taller).filter(models.Taller.id == taller_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Taller no encontrado")
    t.suscripcion_activa = not t.suscripcion_activa
    db.commit()
    return {"id": t.id, "nombre": t.nombre, "suscripcion_activa": t.suscripcion_activa}

@router.post("/v1/admin/extender-taller/{taller_id}")
def admin_extender_taller(taller_id: int, db: Session = Depends(database.get_db),
                          x_admin_secret: str = Header(None)):
    _verificar_admin(x_admin_secret)
    t = db.query(models.Taller).filter(models.Taller.id == taller_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Taller no encontrado")
    if not t.fecha_vencimiento:
        t.fecha_vencimiento = datetime.datetime.utcnow()
    t.fecha_vencimiento += datetime.timedelta(days=30)
    db.commit()
    return {"id": t.id, "nombre": t.nombre, "fecha_vencimiento": str(t.fecha_vencimiento)}

@router.get("/v1/admin/dispositivos/{taller_id}")
def admin_listar_dispositivos(taller_id: int, db: Session = Depends(database.get_db),
                               x_admin_secret: str = Header(None)):
    _verificar_admin(x_admin_secret)
    devs = db.query(models.Dispositivo).filter(models.Dispositivo.taller_id == taller_id).all()
    return [
        {
            "id": d.id,
            "hw_id": d.hw_id,
            "nombre_pc": d.nombre_pc,
            "ultima_conexion": str(d.ultima_conexion)
        }
        for d in devs
    ]

@router.delete("/v1/admin/dispositivo/{device_id}")
def admin_borrar_dispositivo(device_id: int, db: Session = Depends(database.get_db),
                              x_admin_secret: str = Header(None)):
    _verificar_admin(x_admin_secret)
    dev = db.query(models.Dispositivo).filter(models.Dispositivo.id == device_id).first()
    if not dev:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")
    db.delete(dev)
    db.commit()
    return {"status": "ok", "mensaje": "Dispositivo eliminado correctamente"}


