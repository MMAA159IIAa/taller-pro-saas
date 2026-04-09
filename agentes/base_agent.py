import threading
import time
from datetime import datetime
from utils.database import conectar

class BaseAgent:
    """Clase base para agentes autónomos con logging en DB"""
    def __init__(self, nombre, intervalo_segundos=60):
        self.nombre = nombre
        self.intervalo = intervalo_segundos
        self.activo = False
        self.hilo = None

    def log(self, mensaje, nivel="INFO"):
        """Guarda el 'pensamiento' del agente en la base de datos"""
        print(f"[{self.nombre}] {mensaje}")
        try:
            conn = conectar()
            conn.execute("INSERT INTO agentes_logs (agente, mensaje, fecha, nivel) VALUES (?,?,?,?)",
                         (self.nombre, mensaje, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), nivel))
            # Mantener solo los últimos 100 logs para no saturar
            conn.execute("DELETE FROM agentes_logs WHERE id NOT IN (SELECT id FROM agentes_logs ORDER BY id DESC LIMIT 100)")
            conn.commit()
            conn.close()
        except:
            pass

    def iniciar(self):
        if self.activo: return
        self.activo = True
        self._set_status(1)
        self.hilo = threading.Thread(target=self._main_loop, daemon=True)
        self.hilo.start()
        self.log("Agente iniciado y patrullando...")

    def detener(self):
        self.activo = False
        self._set_status(0)
        self.log("Agente detenido.")

    def _set_status(self, val):
        try:
            conn = conectar()
            conn.execute("INSERT OR REPLACE INTO agentes_status (clave, activo, ultima_actividad) VALUES (?,?,?)",
                         (self.nombre, val, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
            conn.close()
        except: pass

    def _main_loop(self):
        while self.activo:
            try:
                self.ejecutar_tarea()
                self._set_status(1)
            except Exception as e:
                self.log(f"Error en ejecución: {e}", "ERROR")
            time.sleep(self.intervalo)

    def ejecutar_tarea(self):
        """Sobrescribir en subclases"""
        pass
