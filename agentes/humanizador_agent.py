from agentes.base_llm import BaseLLM
from utils.logger import info, error

class HumanizadorAgent(BaseLLM):
    """
    Agente especializado en pulir textos crudos de mecánicos y 
    convertirlos en mensajes elegantes y cálidos para clientes.
    """
    def __init__(self):
        super().__init__("09-Humanizador")
        
    def redactar_notificacion_listo(self, nombre, auto, servicio):
        self.borrar_memoria()
        prompt = (f"El siguiente vehículo ya está listo para ser recogido:\n"
                  f"- Cliente: {nombre}\n"
                  f"- Auto: {auto}\n"
                  f"- Trabajos realizados / Notas: {servicio}\n\n"
                  f"Instrucción: Genera un mensaje de WhatsApp cálido y profesional "
                  f"notificándole que su vehículo ya está listo en el Taller y resaltando "
                  f"brevemente el trabajo que se le hizo (traduce los términos rudos si los hay). "
                  f"Mantén el mensaje corto, usa emojis, y omite saludos largos extras. No menciones el costo aún.")
        
        info("HumanizadorAgent", f"Redactando WhatsApp 'Listo' para {nombre}...")
        respuesta = self.responder(prompt)
        return respuesta.strip()

    def redactar_notificacion_entregado(self, nombre, auto, servicio, costo):
        self.borrar_memoria()
        prompt = (f"El cliente acaba de recoger su vehículo pagando su cuenta:\n"
                  f"- Cliente: {nombre}\n"
                  f"- Auto: {auto}\n"
                  f"- Costo Total: ${costo}\n\n"
                  f"Instrucción: Genera un mensaje de WhatsApp corto de despedida y agradecimiento en nombre del taller. "
                  f"Agradécele su confianza por traer su auto, mánadale un buen deseo y recuérdale que estamos a la orden. "
                  f"Maneja un tono muy empático y seguro, usa emojis.")
        
        info("HumanizadorAgent", f"Redactando WhatsApp 'Entregado/Despedida' para {nombre}...")
        respuesta = self.responder(prompt)
        return respuesta.strip()
