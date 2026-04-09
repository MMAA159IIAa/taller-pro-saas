import threading
import time
from datetime import datetime
from utils.database import conectar, get_config
from utils.logger import info, error
from servicios.email_service import EmailService
from servicios.whatsapp_service import WhatsAppService
from servicios.recibo_generator import generar_recibo

class NotificationAgent:
    """
    Monitorea cambios de estatus y envia notificaciones automaticas.
    - Listo     → correo + WhatsApp al cliente
    - Entregado → recibo PDF por correo + confirmacion por WhatsApp
    """

    def __init__(self, intervalo_segundos=30):
        self.intervalo = intervalo_segundos
        self.activo    = False
        self.hilo      = None
        self.email     = EmailService()
        self.wa        = WhatsAppService()

    def iniciar(self):
        if self.activo: return
        self.activo = True
        self.hilo = threading.Thread(target=self._loop, daemon=True)
        self.hilo.start()
        info("NotificationAgent", f"Iniciado — revisando cada {self.intervalo}s")

    def detener(self):
        self.activo = False
        info("NotificationAgent", "Detenido")

    def _loop(self):
        while self.activo:
            try:
                self._revisar_listos()
                self._revisar_entregados()
            except Exception as ex:
                error("NotificationAgent", f"Error en loop: {ex}")
            time.sleep(self.intervalo)

    def _revisar_listos(self):
        conn = conectar()
        pendientes = conn.execute("""
            SELECT id, nombre, correo, telefono, auto, servicio
            FROM registros
            WHERE estatus='Listo' AND notificado=0
            AND (correo != '' OR telefono != '')
        """).fetchall()
        conn.close()

        taller = get_config("taller_nombre", "Taller Pro")

        for reg in pendientes:
            id_reg, nombre, correo, telefono, auto, servicio = reg
            enviado = False

            # Correo
            if correo:
                ok = self.email.enviar_listo(nombre, correo, auto, servicio)
                if ok:
                    enviado = True
                    info("NotificationAgent", f"Correo enviado: {nombre} — {auto} listo")

            # WhatsApp
            if telefono:
                ok = self.wa.enviar_listo(nombre, telefono, auto, servicio, taller)
                if ok:
                    enviado = True
                    info("NotificationAgent", f"WhatsApp enviado: {nombre} — {auto} listo")

            if enviado:
                conn = conectar()
                conn.execute("UPDATE registros SET notificado=1 WHERE id=?", (id_reg,))
                conn.commit()
                conn.close()

    def _revisar_entregados(self):
        conn = conectar()
        pendientes = conn.execute("""
            SELECT id, nombre, correo, telefono, auto, servicio, fecha, costo
            FROM registros
            WHERE estatus='Entregado' AND recibo_enviado=0
            AND (correo != '' OR telefono != '')
        """).fetchall()
        conn.close()

        taller = get_config("taller_nombre", "Taller Pro")

        for reg in pendientes:
            id_reg, nombre, correo, telefono, auto, servicio, fecha, costo = reg
            enviado = False

            # Generar PDF y enviar por correo
            if correo:
                pdf = generar_recibo(nombre, auto, servicio, fecha, costo, id_reg)
                if pdf:
                    ok = self.email.enviar_recibo(nombre, correo, pdf)
                    if ok:
                        enviado = True
                        info("NotificationAgent", f"Recibo por correo: {nombre}")

            # WhatsApp de confirmacion de entrega
            if telefono:
                ok = self.wa.enviar_recibo(nombre, telefono, auto, servicio, costo or 0, taller)
                if ok:
                    enviado = True
                    info("NotificationAgent", f"WhatsApp entrega: {nombre}")

            if enviado:
                conn = conectar()
                conn.execute("UPDATE registros SET recibo_enviado=1 WHERE id=?", (id_reg,))
                conn.commit()
                conn.close()

    # ── Envio manual (desde boton en UI) ─────────────────────────────────────
    def notificar_manual(self, id_reg):
        """Envia notificacion manual a un cliente especifico."""
        conn = conectar()
        reg = conn.execute("""
            SELECT nombre, correo, telefono, auto, servicio, estatus, fecha, costo
            FROM registros WHERE id=?
        """, (id_reg,)).fetchone()
        conn.close()
        if not reg: return False, "Registro no encontrado"

        nombre, correo, telefono, auto, servicio, estatus, fecha, costo = reg
        taller  = get_config("taller_nombre", "Taller Pro")
        enviado = []

        if estatus == "Listo":
            if correo:
                self.email.enviar_listo(nombre, correo, auto, servicio)
                enviado.append("correo")
            if telefono:
                self.wa.enviar_listo(nombre, telefono, auto, servicio, taller)
                enviado.append("WhatsApp")
        elif estatus == "Entregado":
            if correo:
                pdf = generar_recibo(nombre, auto, servicio, fecha, costo, id_reg)
                if pdf:
                    self.email.enviar_recibo(nombre, correo, pdf)
                    enviado.append("correo con recibo")
            if telefono:
                self.wa.enviar_recibo(nombre, telefono, auto, servicio, costo or 0, taller)
                enviado.append("WhatsApp")
        else:
            if correo:
                self.email.enviar(correo, f"Actualizacion de tu vehiculo - {taller}",
                                  f"Hola {nombre}, el estatus de tu {auto} es: {estatus}.")
                enviado.append("correo")
            if telefono:
                self.wa.enviar(telefono, f"Hola {nombre}! El estatus de tu *{auto}* es: *{estatus}*. _{taller}_")
                enviado.append("WhatsApp")

        if enviado:
            return True, f"Enviado por: {', '.join(enviado)}"
        return False, "Cliente sin correo ni telefono registrado"
