from agentes.recepcionista_agent import RecepcionistaAgent
from agentes.base_llm import BaseLLM
import time

def prueba_rapida():
    print("Iniciando Agente Recepcionista con los nuevos precios reales...\n")
    agente = RecepcionistaAgent()
    
    mensaje_cliente = "Hola, buenas tardes. Disculpa, ¿qué precio tiene el cambio de aceite y la alineación?"
    print(f"👤 Cliente: {mensaje_cliente}")
    print("⏳ Generando respuesta de la IA (esto puede tardar unos segundos dependiendo del motor)...\n")
    
    try:
        respuesta = agente.procesar_mensaje_entrante(1, "Carlos", mensaje_cliente)
        print(f"🤖 Recepcionista TallerPro: {respuesta}\n")
    except Exception as e:
        print(f"❌ Error al consultar la IA (¿Tienes LM Studio abierto o la API configurada?): {e}")

if __name__ == "__main__":
    prueba_rapida()
