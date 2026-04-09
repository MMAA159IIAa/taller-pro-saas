import threading
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from utils.database import conectar, get_config
from utils.logger import info, error
from servicios.email_service import EmailService

class SalesAgent:
    """
    Detecta clientes con servicio vencido (+6 meses)
    y envia mensajes de seguimiento automaticos.
    Maximo 1 mensaje por cliente cada 30 dias.
    """

    def __init__(self, intervalo_horas=24):
        self.intervalo = intervalo_horas * 3600
        self.activo    = False
        self.hilo      = None
        self.email     = EmailService()
        self.dias_espera = int(get_config("seguimiento_dias", "30"))

    def iniciar(self):
        if self.activo: return
        self.activo = True
        self.hilo = threading.Thread(target=self._loop, daemon=True)
        self.hilo.start()
        info("SalesAgent", f"Iniciado — revisando cada {self.intervalo//3600}h")

    def detener(self):
        self.activo = False

    def _loop(self):
        while self.activo:
            try:
                self._revisar_vencidos()
            except Exception as ex:
                error("SalesAgent", f"Error: {ex}")
            time.sleep(self.intervalo)

    def _revisar_vencidos(self):
        conn  = conectar()
        todos = conn.execute("SELECT id, nombre, correo, auto, fecha FROM registros WHERE correo != ''").fetchall()
        conn.close()
        ahora = datetime.now()
        enviados = 0
        for reg in todos:
            id_reg, nombre, correo, auto, fecha_str = reg
            try:
                fecha_servicio = datetime.strptime(fecha_str, "%Y-%m-%d")
                if ahora < fecha_servicio + relativedelta(months=6):
                    continue
                if self._enviado_recientemente(id_reg):
                    continue
                ok = self.email.enviar_seguimiento(nombre, correo, auto)
                if ok:
                    self._registrar_envio(id_reg, nombre)
                    enviados += 1
            except Exception as ex:
                error("SalesAgent", f"Error procesando {nombre}: {ex}")
        if enviados:
            info("SalesAgent", f"{enviados} mensajes de seguimiento enviados")

    def _enviado_recientemente(self, cliente_id):
        conn = conectar()
        row = conn.execute("""
            SELECT fecha_envio FROM seguimiento
            WHERE cliente_id=? AND tipo='seguimiento'
            ORDER BY id DESC LIMIT 1
        """, (cliente_id,)).fetchone()
        conn.close()
        if not row: return False
        try:
            ultimo = datetime.strptime(row[0], "%Y-%m-%d")
            return (datetime.now() - ultimo).days < self.dias_espera
        except:
            return False

    def _registrar_envio(self, cliente_id, nombre):
        conn = conectar()
        conn.execute("""INSERT INTO seguimiento (cliente_id, fecha_envio, tipo, mensaje)
                        VALUES (?, ?, 'seguimiento', ?)""",
                     (cliente_id, datetime.now().strftime("%Y-%m-%d"),
                      f"Mensaje de seguimiento enviado a {nombre}"))
        conn.commit()
        conn.close()
