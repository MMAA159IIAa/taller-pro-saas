import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
from utils.database import get_config
from utils.logger import info, error

class EmailService:
    def __init__(self):
        self.smtp_email = get_config("smtp_email")
        self.smtp_pass  = get_config("smtp_pass")
        self.taller     = get_config("taller_nombre", "Taller Pro")

    def _conectar(self):
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(self.smtp_email, self.smtp_pass)
        return server

    def enviar(self, destinatario, asunto, cuerpo, adjunto_path=None):
        if not self.smtp_email or not self.smtp_pass:
            error("EmailService", "No hay credenciales configuradas")
            return False
        try:
            msg = MIMEMultipart()
            msg["From"]    = self.smtp_email
            msg["To"]      = destinatario
            msg["Subject"] = asunto
            msg.attach(MIMEText(cuerpo, "plain", "utf-8"))
            if adjunto_path and os.path.exists(adjunto_path):
                with open(adjunto_path, "rb") as f:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header("Content-Disposition",
                                    f"attachment; filename={os.path.basename(adjunto_path)}")
                    msg.attach(part)
            server = self._conectar()
            server.send_message(msg)
            server.quit()
            info("EmailService", f"Correo enviado a {destinatario}")
            return True
        except Exception as ex:
            error("EmailService", f"Error enviando a {destinatario}: {ex}")
            return False

    def enviar_listo(self, nombre, correo, auto, servicio):
        asunto = f"Tu vehiculo {auto} esta listo - {self.taller}"
        cuerpo = (f"Hola {nombre},\n\n"
                  f"Tu vehiculo {auto} ya esta listo.\n"
                  f"Servicio realizado: {servicio}\n\n"
                  f"Puedes pasar a recogerlo en nuestro horario de atencion.\n\n"
                  f"Gracias por tu preferencia.\n\n{self.taller}")
        return self.enviar(correo, asunto, cuerpo)

    def enviar_recibo(self, nombre, correo, pdf_path):
        asunto = f"Recibo de servicio - {self.taller}"
        cuerpo = (f"Hola {nombre},\n\n"
                  f"Adjunto encontraras tu recibo de servicio.\n\n"
                  f"Gracias por tu preferencia.\n\n{self.taller}")
        return self.enviar(correo, asunto, cuerpo, adjunto_path=pdf_path)

    def enviar_seguimiento(self, nombre, correo, auto):
        asunto = f"Te toca mantenimiento - {self.taller}"
        cuerpo = (f"Hola {nombre},\n\n"
                  f"Han pasado mas de 6 meses desde el ultimo servicio de tu {auto}.\n"
                  f"Tenemos promociones especiales este mes.\n\n"
                  f"Contactanos para agendar tu cita.\n\n{self.taller}")
        return self.enviar(correo, asunto, cuerpo)
