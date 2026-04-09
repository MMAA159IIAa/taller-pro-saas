import sqlite3
import datetime
import uuid
import sys
import os

# Ajustar ruta para encontrar módulos del backend
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

try:
    from core.database import SessionLocal, engine
    from models import models
    # Asegurar que las tablas existan en la BD central (sql_app.db)
    models.Base.metadata.create_all(bind=engine)
except ImportError as e:
    print(f"❌ Error de importación: {e}")
    print(f"Buscando en: {BASE_DIR}")
    input("\nPresiona ENTER para salir...")
    sys.exit()

def menu():
    print("\n--- TALLERPRO SAAS MANAGER ---")
    print("1. Ver todos los talleres")
    print("2. Crear nuevo taller (Generar Licencia)")
    print("3. Suspender/Activar taller (Kill-Switch)")
    print("4. Extender suscripción (+30 días)")
    print("5. Salir")
    return input("Selecciona una opción: ")

def crear_taller():
    nombre = input("Nombre del Taller: ")
    clave = str(uuid.uuid4())[:8].upper() # Clave corta de 8 caracteres
    meses = int(input("Cúantos meses de suscripción inicial?: ") or 1)
    vencimiento = datetime.datetime.now() + datetime.timedelta(days=30*meses)
    
    db = SessionLocal()
    nuevo = models.Taller(
        nombre=nombre,
        activation_key=clave,
        fecha_vencimiento=vencimiento,
        suscripcion_activa=True
    )
    db.add(nuevo)
    db.commit()
    print(f"\n✅ Taller creado exitosamente!")
    print(f"ID: {nuevo.id}")
    print(f"Nombre: {nuevo.nombre}")
    print(f"LLAVE DE ACTIVACIÓN: {clave}")
    print(f"Vence el: {vencimiento.strftime('%d/%m/%Y')}")
    db.close()

def listar_talleres():
    db = SessionLocal()
    talleres = db.query(models.Taller).all()
    print("\nID | Nombre | Clave | Estatus | Vencimiento")
    print("-" * 60)
    for t in talleres:
        status = "ACTIVO" if t.suscripcion_activa else "SUSPENDIDO"
        vence = t.fecha_vencimiento.strftime('%d/%m/%Y') if t.fecha_vencimiento else "N/A"
        print(f"{t.id} | {t.nombre} | {t.activation_key} | {status} | {vence}")
    db.close()

def cambiar_estatus():
    t_id = int(input("ID del Taller a modificar: "))
    db = SessionLocal()
    taller = db.query(models.Taller).filter(models.Taller.id == t_id).first()
    if taller:
        taller.suscripcion_activa = not taller.suscripcion_activa
        db.commit()
        status = "ACTIVO" if taller.suscripcion_activa else "SUSPENDIDO"
        print(f"✅ Taller {t_id} ahora está {status}")
    else:
        print("❌ Taller no encontrado.")
    db.close()

def extender():
    t_id = int(input("ID del Taller a extender: "))
    db = SessionLocal()
    taller = db.query(models.Taller).filter(models.Taller.id == t_id).first()
    if taller:
        if not taller.fecha_vencimiento:
            taller.fecha_vencimiento = datetime.datetime.now()
        taller.fecha_vencimiento += datetime.timedelta(days=30)
        db.commit()
        print(f"✅ Nueva fecha para {taller.nombre}: {taller.fecha_vencimiento.strftime('%d/%m/%Y')}")
    else:
        print("❌ Taller no encontrado.")
    db.close()

if __name__ == "__main__":
    try:
        while True:
            op = menu()
            if op == "1": listar_talleres()
            elif op == "2": crear_taller()
            elif op == "3": cambiar_estatus()
            elif op == "4": extender()
            elif op == "5": break
            else: print("Opción no válida.")
    except Exception as e:
        print(f"\n❌ Ocurrió un error inesperado: {e}")
        import traceback
        traceback.print_exc()
    
    input("\n--- Presiona ENTER para salir del Gestor SaaS ---")
