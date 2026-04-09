from utils.database import get_config
from utils.logger import info

class SalesChatAgent:
    """
    Agente de ventas con memoria de contexto.
    Recuerda de que servicio se esta hablando y responde
    de forma continua sin perder el hilo de la conversacion.
    """

    def __init__(self):
        self.taller    = get_config("taller_nombre", "Taller Pro")
        self.tel       = get_config("taller_tel", "")
        self.horario   = get_config("horario", "Lunes a Viernes 9am-6pm, Sabado 9am-2pm")
        self.ubicacion = get_config("ubicacion", "")
        self.api_key   = get_config("claude_api_key", "")

        # Contexto de conversacion
        self.contexto_servicio = None  # servicio del que se habla
        self.historial = []            # mensajes anteriores

        # Precios reales del taller (del Excel del contador)
        self.precios = {
            "lubricacion":   {"nombre": "Servicio de Lubricacion", "min": 500,  "prom": 2652},
            "aceite":        {"nombre": "Cambio de Aceite",        "min": 500,  "prom": 2652},
            "frenos":        {"nombre": "Revision de Frenos",      "min": 640,  "prom": 3089},
            "balatas":       {"nombre": "Balatas Delanteras",      "min": 500,  "prom": 1709},
            "suspension":    {"nombre": "Revision Suspension",     "min": 300,  "prom": 4890},
            "afinacion":     {"nombre": "Afinacion Mayor",         "min": 1050, "prom": 4280},
            "clutch":        {"nombre": "Kit de Clutch",           "min": 12000,"prom": 12180},
            "llantas":       {"nombre": "4 Llantas",               "min": 3250, "prom": 10166},
            "amortiguadores":{"nombre": "Amortiguadores",          "min": 4850, "prom": 6164},
            "baleros":       {"nombre": "Baleros",                 "min": 150,  "prom": 4200},
        }

        # Sintomas que el cliente describe y a que servicio apuntan
        self.sintomas = {
            # Frenos
            "rechina":        "frenos",
            "rechinar":       "frenos",
            "ruido al frenar":"frenos",
            "no frena":       "frenos",
            "vibra al frenar":"frenos",
            "se va de lado":  "frenos",
            "jala":           "frenos",
            "pedal":          "frenos",
            "pastillas":      "frenos",
            "balatas":        "balatas",
            "discos":         "frenos",
            # Suspension
            "bota":           "suspension",
            "golpe":          "suspension",
            "traqueteo":      "suspension",
            "vibra":          "suspension",
            "ruido abajo":    "suspension",
            "estabilizador":  "suspension",
            "rotula":         "suspension",
            "amortiguador":   "amortiguadores",
            # Motor / Afinacion
            "no arranca":     "afinacion",
            "falla":          "afinacion",
            "humo":           "afinacion",
            "consume mucha":  "afinacion",
            "bujias":         "afinacion",
            "filtro":         "afinacion",
            "aceite":         "aceite",
            "lubricacion":    "lubricacion",
            "servicio":       "lubricacion",
            # Clutch
            "clutch":         "clutch",
            "embrague":       "clutch",
            "no agarra":      "clutch",
            # Llantas
            "llanta":         "llantas",
            "ponchada":       "llantas",
            "desgaste":       "llantas",
            # Baleros
            "zumba":          "baleros",
            "zumbido":        "baleros",
            "balero":         "baleros",
        }

    def responder(self, mensaje, contexto_externo=None):
        """
        Responde manteniendo el contexto de la conversacion.
        contexto_externo: si el chatbot de UI ya maneja el flujo de citas,
        solo se usa para respuestas de servicio.
        """
        if contexto_externo:
            self.contexto_servicio = contexto_externo

        msg     = mensaje.lower().strip()
        self.historial.append({"rol": "cliente", "msg": msg})

        # Si hay API key, usar IA real con contexto
        if self.api_key:
            return self._responder_con_ia(mensaje)

        respuesta = self._logica_local(msg, mensaje)
        self.historial.append({"rol": "agente", "msg": respuesta})
        info("SalesChatAgent", f"Contexto: {self.contexto_servicio} | Msg: {msg[:30]}")
        return respuesta

    def _logica_local(self, msg, msg_original):
        # 1. Detectar sintoma → identificar servicio
        for sintoma, servicio in self.sintomas.items():
            if sintoma in msg:
                self.contexto_servicio = servicio
                return self._resp_sintoma(sintoma, servicio, msg_original)

        # 2. Detectar servicio directo
        for serv_key in self.precios.keys():
            if serv_key in msg:
                self.contexto_servicio = serv_key
                return self._resp_servicio_directo(serv_key)

        # 3. Respuesta con contexto activo
        if self.contexto_servicio:
            return self._resp_con_contexto(msg, msg_original)

        # 4. Palabras clave generales
        if any(p in msg for p in ["hola","buenas","buen dia","buenas tardes","buenas noches"]):
            return self._resp_saludo()
        if any(p in msg for p in ["precio","costo","cuanto","cobran","vale"]):
            return self._resp_precios_generales()
        if any(p in msg for p in ["horario","hora","cuando abren","que horas"]):
            return f"Nuestro horario es {self.horario}. ¿Quieres agendar una cita?"
        if any(p in msg for p in ["donde","ubicacion","direccion","como llego"]):
            if self.ubicacion:
                return f"Estamos en {self.ubicacion}. ¿Necesitas indicaciones?"
            return f"Contactanos al {self.tel} y te damos la direccion exacta." if self.tel else "Escribe al numero del taller para la direccion."
        if any(p in msg for p in ["gracias","ok","listo","perfecto","de acuerdo"]):
            return f"Con mucho gusto! En {self.taller} estamos para servirte. Hasta pronto!"
        if any(p in msg for p in ["garantia","garantizan"]):
            return "Todos nuestros trabajos tienen garantia. Usamos refacciones de calidad y mano de obra certificada."

        # 5. No entendio pero NO decir "no entendi"
        return self._resp_no_entendio(msg_original)

    def _resp_sintoma(self, sintoma, servicio, msg_original):
        info_serv = self.precios.get(servicio, {})
        nombre    = info_serv.get("nombre", servicio.title())
        precio    = info_serv.get("prom", 0)
        taller    = self.taller

        respuestas_sintoma = {
            "rechina":  f"Ese ruido al frenar casi siempre indica que las balatas estan desgastadas. "
                        f"Es importante revisarlo pronto para evitar dano en los discos. "
                        f"El servicio de frenos completo esta desde ${info_serv.get('min',600):,}. "
                        f"¿De que marca y año es tu vehiculo?",

            "rechinar": f"Ese ruido al frenar casi siempre indica que las balatas estan desgastadas. "
                        f"Es importante revisarlo pronto. El servicio de frenos esta desde ${info_serv.get('min',600):,}. "
                        f"¿De que marca y año es tu vehiculo?",

            "bota":     f"Si el carro bota mucho probablemente son los amortiguadores o la suspension. "
                        f"Una suspension en mal estado puede ser peligrosa. "
                        f"Te recomiendo traerlo a revision. El diagnostico es gratis. ¿Que modelo tienes?",

            "vibra":    f"La vibracion puede ser suspension, balanceo o frenos segun donde la sientas. "
                        f"¿La vibras al frenar o siempre? Eso nos ayuda a darte el precio exacto.",

            "falla":    f"Las fallas en el motor pueden ser desde bujias hasta sensores. "
                        f"Lo mejor es un diagnostico computarizado para identificar exactamente que es. "
                        f"¿Como es la falla, se apaga, pierde potencia o enciende la luz del motor?",

            "zumba":    f"Ese zumbido suele ser un balero desgastado. "
                        f"Si no se atiende puede afectar la direccion. "
                        f"¿El zumbido aumenta cuando acelerans o cuando volteas el volante?",

            "no arranca": f"Puede ser bateria, alternador o sistema de arranque. "
                          f"¿Hace algun ruido cuando intentas arrancarlo o queda completamente en silencio?",
        }

        if sintoma in respuestas_sintoma:
            return respuestas_sintoma[sintoma]

        # Respuesta generica para sintoma detectado
        return (f"Entiendo, ese es un sintoma comun en el {nombre}. "
                f"En {taller} revisamos eso regularmente. "
                f"El servicio esta desde ${info_serv.get('min',500):,}. "
                f"¿De que modelo es tu vehiculo para darte cotizacion exacta?")

    def _resp_servicio_directo(self, serv_key):
        info_serv = self.precios[serv_key]
        nombre    = info_serv["nombre"]
        precio_min= info_serv["min"]
        taller    = self.taller
        return (f"El {nombre} en {taller} esta desde ${precio_min:,} "
                f"dependiendo del modelo y tipo de vehiculo. "
                f"Incluye revision completa y mano de obra. "
                f"¿Que vehiculo tienes? Te doy cotizacion exacta.")

    def _resp_con_contexto(self, msg, msg_original):
        """Responde usando el contexto del servicio activo."""
        serv     = self.contexto_servicio
        info_serv= self.precios.get(serv, {})
        nombre   = info_serv.get("nombre", serv.title()) if info_serv else serv.title()

        # Si el cliente da mas detalles del problema
        palabras_detalle = ["si","no","mucho","poco","a veces","siempre","cuando","solo","tambien",
                            "derecho","izquierdo","delante","atras","arriba","abajo","todo","nada"]
        if any(p in msg for p in palabras_detalle) or len(msg.split()) <= 4:
            return (f"Entendido. Con esa informacion de tu {nombre}, "
                    f"lo mejor es que lo traigas para hacer una revision completa. "
                    f"El diagnostico no tiene costo adicional. "
                    f"¿Cuando podrias traerlo? Te agendo la cita.")

        # Si menciona su vehiculo
        marcas = ["ford","chevy","chevrolet","nissan","toyota","honda","vw","volkswagen",
                  "dodge","ram","jeep","mazda","hyundai","kia","seat","fiat","renault","audi","bmw"]
        if any(m in msg for m in marcas):
            marca = next(m for m in marcas if m in msg)
            return (f"Perfecto, para el {marca.title()} el {nombre} esta aproximadamente "
                    f"en ${info_serv.get('prom',2000):,}. "
                    f"Incluye refacciones y mano de obra. "
                    f"¿Quieres agendar una cita?")

        return (f"Para darte el precio exacto del {nombre} necesito saber el modelo de tu vehiculo. "
                f"¿De que marca y año es?")

    def _resp_saludo(self):
        taller = self.taller
        tel    = self.tel
        return (f"Hola! Bienvenido a {taller}. "
                f"Estoy aqui para ayudarte con cualquier servicio para tu vehiculo. "
                f"¿Que problema estas teniendo o que servicio necesitas?")

    def _resp_precios_generales(self):
        lineas = ["Nuestros precios principales:"]
        for k, v in self.precios.items():
            lineas.append(f"• {v['nombre']}: desde ${v['min']:,}")
        lineas.append("\nEl precio exacto depende del modelo. ¿Que vehiculo tienes?")
        return "\n".join(lineas)

    def _resp_no_entendio(self, msg_original):
        """Nunca dice 'no entendi'. Siempre da opciones o pregunta algo util."""
        taller = self.taller
        opciones = [
            "¿Tienes algun ruido o falla en tu vehiculo?",
            "¿Buscas algun servicio en especifico?",
            "Puedo ayudarte con frenos, suspension, afinacion, aceite o cualquier otro servicio.",
        ]
        import random
        opcion = random.choice(opciones)
        return f"Claro, en {taller} estamos para ayudarte. {opcion}"

    def _responder_con_ia(self, mensaje):
        try:
            import urllib.request, json
            taller    = self.taller
            tel       = self.tel
            horario   = self.horario
            ubicacion = self.ubicacion

            # Construir historial para contexto
            msgs_ia = []
            for h in self.historial[-6:]:  # ultimos 6 mensajes
                rol = "user" if h["rol"] == "cliente" else "assistant"
                msgs_ia.append({"role": rol, "content": h["msg"]})
            msgs_ia.append({"role": "user", "content": mensaje})

            precios_txt = "\n".join([f"- {v['nombre']}: desde ${v['min']:,}" for v in self.precios.values()])

            system_prompt = (
                f"Eres un agente de ventas experto de {taller}, un taller mecanico. "
                f"PRECIOS REALES:\n{precios_txt}\n"
                f"Horario: {horario}. "
                f"{'Ubicacion: ' + ubicacion if ubicacion else ''} "
                f"{'Tel: ' + tel if tel else ''}\n\n"
                f"REGLAS:\n"
                f"1. NUNCA digas 'no entiendo' — siempre da una respuesta util\n"
                f"2. Si el cliente describe un sintoma, identifica el servicio y da precio\n"
                f"3. Recuerda el contexto de la conversacion\n"
                f"4. Se persuasivo pero sin presionar\n"
                f"5. Siempre intenta agendar una cita o conseguir el modelo del vehiculo\n"
                f"6. Responde en maximo 3 oraciones cortas\n"
                f"7. Usa lenguaje simple, no tecnico"
            )

            payload = json.dumps({
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 300,
                "system": system_prompt,
                "messages": msgs_ia
            }).encode("utf-8")

            req = urllib.request.Request(
                "https://api.anthropic.com/v1/messages",
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01"
                }
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
                return data["content"][0]["text"]
        except Exception as ex:
            info("SalesChatAgent", f"IA no disponible, usando logica local: {ex}")
            return self._logica_local(mensaje.lower(), mensaje)

    def resetear_contexto(self):
        self.contexto_servicio = None
        self.historial = []
