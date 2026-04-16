from agentes.base_agent import BaseAgent
from utils.database import conectar, get_config
from servicios.email_service import EmailService
from servicios.whatsapp_service import WhatsAppService
from servicios.recibo_generator import generar_recibo

try:
    from agentes.humanizador_agent import HumanizadorAgent
except ImportError:
    HumanizadorAgent = None

class NotificationAgent(BaseAgent):
    """
    Monitorea cambios de estatus y envia notificaciones automaticas.
    - Listo     → correo + WhatsApp al cliente
    - Entregado → recibo PDF por correo + confirmacion por WhatsApp
    """

    def __init__(self, intervalo_segundos=30):
        super().__init__("Notificador", intervalo_segundos)
        self.email     = EmailService()
        self.wa        = WhatsAppService()
        self.humanizador = HumanizadorAgent() if HumanizadorAgent else None

    def ejecutar_tarea(self):
        self._revisar_listos()
        self._revisar_entregados()

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
                    self.log(f"Correo enviado: {nombre} — {auto} listo")

            # WhatsApp
            if telefono:
                usar_ia = get_config("usar_ia_notificaciones", "0") == "1"
                try:
                    if usar_ia and self.humanizador:
                        msg_ia = self.humanizador.redactar_notificacion_listo(nombre, auto, servicio)
                        # Le concatenamos la firma obligatoria
                        msg_ia += f"\n\n_{taller}_"
                        ok = self.wa.enviar(telefono, msg_ia)
                    else:
                        ok = self.wa.enviar_listo(nombre, telefono, auto, servicio, taller)
                except Exception as e:
                    self.log(f"Fallo IA en WhatsApp Listo {nombre}, usando fallback: {e}")
                    ok = self.wa.enviar_listo(nombre, telefono, auto, servicio, taller)
                    
                if ok:
                    enviado = True
                    self.log(f"WhatsApp enviado: {nombre} — {auto} listo")

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
                        self.log(f"Recibo por correo enviado a: {nombre}")

            # WhatsApp de confirmacion de entrega
            if telefono:
                usar_ia = get_config("usar_ia_notificaciones", "0") == "1"
                try:
                    if usar_ia and self.humanizador:
                        msg_ia = self.humanizador.redactar_notificacion_entregado(nombre, auto, servicio, costo)
                        msg_ia += f"\n\n_{taller}_"
                        ok = self.wa.enviar(telefono, msg_ia)
                    else:
                        ok = self.wa.enviar_recibo(nombre, telefono, auto, servicio, costo or 0, taller)
                except Exception as e:
                    self.log(f"Fallo IA en WhatsApp Entregado {nombre}, usando fallback: {e}")
                    ok = self.wa.enviar_recibo(nombre, telefono, auto, servicio, costo or 0, taller)

                if ok:
                    enviado = True
                    self.log(f"WhatsApp entrega enviado a: {nombre}")

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
