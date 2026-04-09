import sys
import os
import datetime
import uuid
import requests

# ─── Configuración ─────────────────────────────────────────────────────────────
# Por defecto apunta al servidor de Render. Cambia a localhost para pruebas locales.
API_URL = "https://taller-pro-saas.onrender.com"
ADMIN_SECRET = "tallerpro-admin-2026"  # Clave secreta de administración

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

# ─── Funciones API ─────────────────────────────────────────────────────────────

def _headers():
    return {"X-Admin-Secret": ADMIN_SECRET, "Content-Type": "application/json"}

def crear_taller():
    nombre = input("Nombre del Taller: ").strip()
    try:
        meses = int(input("¿Cuántos meses de suscripción?: ") or "1")
    except:
        meses = 1
    plan = input("Plan (Basico/Pro/Enterprise) [Basico]: ").strip() or "Basico"

    print(f"\n⏳ Creando taller en el servidor: {API_URL} ...")
    try:
        resp = requests.post(
            f"{API_URL}/api/v1/admin/crear-taller",
            json={"nombre": nombre, "meses": meses, "plan": plan},
            headers=_headers(),
            timeout=30
        )
        if resp.status_code == 200:
            data = resp.json()
            print(f"\n✅ Taller creado exitosamente!")
            print(f"ID: {data['id']}")
            print(f"Nombre: {data['nombre']}")
            print(f"LLAVE DE ACTIVACIÓN: {data['activation_key']}")
            print(f"Vence el: {data['fecha_vencimiento']}")
        else:
            print(f"❌ Error del servidor: {resp.status_code} - {resp.text}")
    except requests.exceptions.ConnectionError:
        print(f"❌ No se pudo conectar a {API_URL}")
        print("   ¿El servidor está encendido?")
    except Exception as ex:
        print(f"❌ Error: {ex}")

def listar_talleres():
    print(f"\n⏳ Consultando talleres en: {API_URL} ...")
    try:
        resp = requests.get(
            f"{API_URL}/api/v1/admin/talleres",
            headers=_headers(),
            timeout=30
        )
        if resp.status_code == 200:
            talleres = resp.json()
            print(f"\n{'ID':<5} {'Nombre':<30} {'Clave':<12} {'Estatus':<12} {'Vencimiento'}")
            print("-" * 75)
            for t in talleres:
                status = "✅ ACTIVO" if t.get("suscripcion_activa") else "🔴 SUSPENDIDO"
                vence = t.get("fecha_vencimiento", "N/A")[:10] if t.get("fecha_vencimiento") else "N/A"
                print(f"{t['id']:<5} {t['nombre']:<30} {t['activation_key']:<12} {status:<12} {vence}")
        else:
            print(f"❌ Error: {resp.status_code} - {resp.text}")
    except requests.exceptions.ConnectionError:
        print(f"❌ No se pudo conectar a {API_URL}")
    except Exception as ex:
        print(f"❌ Error: {ex}")

def cambiar_estatus():
    try:
        t_id = int(input("ID del Taller a modificar: "))
    except:
        print("ID inválido")
        return
    print(f"\n⏳ Modificando taller #{t_id} ...")
    try:
        resp = requests.post(
            f"{API_URL}/api/v1/admin/toggle-taller/{t_id}",
            headers=_headers(),
            timeout=30
        )
        if resp.status_code == 200:
            data = resp.json()
            status = "✅ ACTIVO" if data.get("suscripcion_activa") else "🔴 SUSPENDIDO"
            print(f"   Taller '{data['nombre']}' ahora está {status}")
        else:
            print(f"❌ Error: {resp.status_code} - {resp.text}")
    except requests.exceptions.ConnectionError:
        print(f"❌ No se pudo conectar a {API_URL}")
    except Exception as ex:
        print(f"❌ Error: {ex}")

def extender():
    try:
        t_id = int(input("ID del Taller a extender: "))
    except:
        print("ID inválido")
        return
    print(f"\n⏳ Extendiendo suscripción del taller #{t_id} ...")
    try:
        resp = requests.post(
            f"{API_URL}/api/v1/admin/extender-taller/{t_id}",
            headers=_headers(),
            timeout=30
        )
        if resp.status_code == 200:
            data = resp.json()
            print(f"   ✅ Nueva fecha para '{data['nombre']}': {str(data.get('fecha_vencimiento',''))[:10]}")
        else:
            print(f"❌ Error: {resp.status_code} - {resp.text}")
    except requests.exceptions.ConnectionError:
        print(f"❌ No se pudo conectar a {API_URL}")
    except Exception as ex:
        print(f"❌ Error: {ex}")

def menu():
    print(f"\n═══════════════════════════════════════════")
    print(f"   TALLERPRO SaaS MANAGER")
    print(f"   Servidor: {API_URL}")
    print(f"═══════════════════════════════════════════")
    print("1. Ver todos los talleres")
    print("2. Crear nuevo taller (Generar Licencia)")
    print("3. Suspender/Activar taller (Kill-Switch)")
    print("4. Extender suscripción (+30 días)")
    print("5. Salir")
    return input("\nSelecciona una opción: ").strip()

if __name__ == "__main__":
    try:
        while True:
            op = menu()
            if op == "1": listar_talleres()
            elif op == "2": crear_taller()
            elif op == "3": cambiar_estatus()
            elif op == "4": extender()
            elif op == "5": break
            else: print("⚠️  Opción no válida.")
    except KeyboardInterrupt:
        print("\n\nSaliendo...")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()

    input("\n--- Presiona ENTER para salir del Gestor SaaS ---")
