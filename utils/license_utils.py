import subprocess
import os
import sys
import requests
import socket
import datetime

# Por defecto apunta a localhost para pruebas, cambiar a la URL de Render en producción
# URL de producción en Render
BASE_URL = "https://taller-pro-saas.onrender.com"

def obtener_hw_id():
    """Genera un ID único para la computadora basado en el serial del disco."""
    try:
        # Método Windows: WMIC
        cmd = 'wmic diskdrive get serialnumber'
        res = subprocess.check_output(cmd, shell=True).decode().split('\n')
        serial = res[1].strip()
        if not serial or serial == "":
            # Fallback a nombre de máquina + usuario si wmic falla
            return f"FB-{socket.gethostname()}-{os.getlogin()}"
        return serial
    except:
        return f"GEN-{socket.gethostname()}"

def obtener_nombre_pc():
    return socket.gethostname()

def verificar_licencia_remota(taller_id):
    """Consulta al servidor central si este taller y esta PC tienen permiso."""
    if not taller_id:
        return {"status": "error", "mensaje": "Taller no configurado"}
        
    hw_id = obtener_hw_id()
    pc_name = obtener_nombre_pc()
    
    try:
        url = f"{BASE_URL}/api/v1/license/check/{taller_id}?hw_id={hw_id}&pc_name={pc_name}"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            return resp.json()
        elif resp.status_code == 404:
            return {"status": "error", "mensaje": "Este taller no existe en el servidor central."}
        else:
            return {"status": "error", "mensaje": f"Error del servidor: {resp.status_code}"}
    except Exception as e:
        # En caso de no haber internet, se podría permitir un modo offline temporal
        # Pero para este ejercicio de SaaS, seremos estrictos.
        return {"status": "offline", "mensaje": f"No hay conexión con el servidor central."}

def activar_licencia_remota(key):
    """Intenta activar el programa con una clave por primera vez."""
    hw_id = obtener_hw_id()
    pc_name = obtener_nombre_pc()
    
    try:
        url = f"{BASE_URL}/api/v1/license/activate/{key}?hw_id={hw_id}&pc_name={pc_name}"
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            return resp.json()
        else:
            return {"status": "error", "mensaje": resp.json().get('detail', 'Error desconocido')}
    except Exception as e:
        return {"status": "error", "mensaje": "No se pudo conectar al servidor de activación."}
