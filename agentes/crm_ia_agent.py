from agentes.base_llm import BaseLLM
from utils.logger import info

class CRMAgent(BaseLLM):
    """
    Cerebro especializado en Seguimiento de Clientes, Reactivación y Reviews.
    Basado en 03-Seguimiento_CRM/SKILL.md
    """
    def __init__(self):
        super().__init__("03-Seguimiento_CRM")
        
    def redactar_seguimiento_3_dias(self, nombre, auto, servicio):
        self.borrar_memoria()
        prompt = (f"El siguiente cliente retiró su vehículo hace exactamente 3 días:\n"
                  f"- Cliente: {nombre}\n"
                  f"- Vehículo: {auto}\n"
                  f"- Servicio realizado: {servicio}\n\n"
                  f"Instrucción: Completa la 'Secuencia A: El Cazador de 5 Estrellas'. "
                  f"Redacta un mensaje de WhatsApp corto y muy amable preguntando cómo ha sentido su vehículo "
                  f"después del servicio. Pídele que si está satisfecho, nos apoye con 5 estrellas en "
                  f"Google Maps en el siguiente enlace: [https://g.page/r/taller_pro_ejemplo]. Usa emojis.")
        
        info("CRMAgent", f"🧠 IA redactando CRM de 3 Días para {nombre}...")
        respuesta = self.responder(prompt)
        return respuesta.strip()

    def redactar_seguimiento_6_meses(self, nombre, auto, ultimo_servicio):
        self.borrar_memoria()
        prompt = (f"El siguiente cliente NO ha venido al taller desde hace 6 meses:\n"
                  f"- Cliente: {nombre}\n"
                  f"- Vehículo: {auto}\n"
                  f"- El último servicio que se le hizo hace 6 meses fue: {ultimo_servicio}\n\n"
                  f"Instrucción: Completa la 'Secuencia B: Check-Up de 6 Meses'. "
                  f"Genera un WhatsApp preventivo para invitarlo a agendar un servicio de "
                  f"mantenimiento o cambio de aceite. Explica suavemente que mantenerlo al día evita "
                  f"gastos costosos a futuro. Hazlo personal, no como un robot automático.")
        
        info("CRMAgent", f"🧠 IA redactando CRM de 6 Meses para {nombre}...")
        respuesta = self.responder(prompt)
        return respuesta.strip()
