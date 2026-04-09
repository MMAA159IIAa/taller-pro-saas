import urllib.request
import urllib.parse
import json
from utils.database import get_config
from utils.logger import info, error

class WhatsAppService:
    """
    Envia mensajes de WhatsApp via UltraMsg API.
    Instancia y token configurables desde Configuracion del programa.
    """

    def __init__(self):
        self.instance = get_config("whatsapp_instance", "instance168879")
        self.token    = get_config("whatsapp_token",    "zuipocqnwxcnnq3d")
        self.base_url = f"https://api.ultramsg.com/{self.instance}/messages/chat"

    def _formatear_telefono(self, telefono):
        """Asegura formato internacional. Agrega 52 para Mexico si no tiene codigo."""
        tel = str(telefono).strip().replace(" ","").replace("-","").replace("(","").replace(")","")
        if tel.startswith("+"): return tel[1:]
        if tel.startswith("52") and len(tel) >= 12: return tel
        if len(tel) == 10: return "52" + tel
        return tel

    def enviar(self, telefono, mensaje):
        if not telefono or not self.token:
            error("WhatsAppService", "Sin telefono o token configurado")
            return False
        try:
            tel = self._formatear_telefono(telefono)
            datos = urllib.parse.urlencode({
                "token":       self.token,
                "to":          tel,
                "body":        mensaje,
                "priority":    "1",
                "referenceId": ""
            }).encode("utf-8")
            req = urllib.request.Request(
                self.base_url,
                data=datos,
                method="POST"
            )
            req.add_header("Content-Type", "application/x-www-form-urlencoded")
            req.add_header("Accept", "application/json")
            req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())
                if data.get("sent") == "true" or data.get("id"):
                    info("WhatsAppService", f"WA enviado a {tel}")
                    return True
                else:
                    error("WhatsAppService", f"Respuesta inesperada: {data}")
                    return False
        except Exception as ex:
            error("WhatsAppService", f"Error enviando WA a {telefono}: {ex}")
            return False

    def enviar_listo(self, nombre, telefono, auto, servicio, taller="Taller Pro"):
        msg = (f"Hola {nombre}! 🔧\n\n"
               f"Tu vehiculo *{auto}* ya esta listo.\n"
               f"Servicio: {servicio}\n\n"
               f"Puedes pasar a recogerlo en nuestro horario de atencion.\n\n"
               f"Gracias por tu preferencia! 🙌\n"
               f"_{taller}_")
        return self.enviar(telefono, msg)

    def enviar_recibo(self, nombre, telefono, auto, servicio, costo, taller="Taller Pro"):
        msg = (f"Hola {nombre}! ✅\n\n"
               f"Tu vehiculo *{auto}* fue entregado.\n"
               f"Servicio: {servicio}\n"
               f"Total: *${float(costo):,.2f}*\n\n"
               f"Gracias por elegirnos. Te esperamos pronto! 🚗\n"
               f"_{taller}_")
        return self.enviar(telefono, msg)

    def enviar_seguimiento(self, nombre, telefono, auto, taller="Taller Pro"):
        msg = (f"Hola {nombre}! 👋\n\n"
               f"Te escribimos de *{taller}*.\n"
               f"Han pasado mas de 6 meses desde el ultimo servicio de tu *{auto}*.\n\n"
               f"Este mes tenemos *promociones especiales* en mantenimiento. 🎯\n\n"
               f"Contactanos para agendar tu cita!\n"
               f"_{taller}_")
        return self.enviar(telefono, msg)
