from agentes.base_llm import BaseLLM
from utils.database import get_config

class RecepcionistaAgent(BaseLLM):
    """
    Agente Frontend de Atención Primaria.
    Este agente es el primero en recibir los WhatsApps o mensajes web.
    """
    def __init__(self):
        # 1. Recuperamos información vital del Taller para inyectar en el agente
        nombre_taller = get_config("taller_nombre", "Taller Pro")
        tel_taller = get_config("taller_tel", "No disponible")
        horarios = get_config("horarios", "Lun-Vie 9am a 6pm, Sábado 9am a 2pm")
        
        contexto_inyectado = (
            f"- Nombre Oficial del Taller: {nombre_taller}\n"
            f"- Nuestro Whatsapp de contacto: {tel_taller}\n"
            f"- Horarios Operativos: {horarios}\n"
        )
        
        # 2. Inicializamos apuntando a su carpeta de Skill
        super().__init__("01-Recepcionista", taller_context=contexto_inyectado)
        
    def procesar_mensaje_entrante(self, cliente_id, nombre_cliente, mensaje):
        """
        Recibe un mensaje de un cliente. 
        Manejamos su nombre para darle calidez antes de pasárselo al LLM.
        """
        # Si el historial está vacío (es el primer mensaje), el IA debe saber el nombre
        if not self.historial:
            mensaje_enriquecido = f"El usuario se llama {nombre_cliente}. Su mensaje: {mensaje}"
        else:
            mensaje_enriquecido = mensaje
            
        respuesta = self.responder(mensaje_enriquecido)
        return respuesta
