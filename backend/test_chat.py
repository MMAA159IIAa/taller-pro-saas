import requests
import time

# Asumimos que el backend SaaS está vivo localmente
WEBHOOK_URL = "http://localhost:8000/api/v1/webhook/1"
SENDER = "526621234567" # Telefono falso para la prueba

print("=============================================")
print("🤖 SIMULADOR: TallerPro Inteligencia Artificial")
print("=============================================")
print("Escribe un mensaje simulando ser el cliente.")
print("Escribe 'salir' para terminar la prueba.\n")

while True:
    try:
        user_input = input("TÚ (Cliente): ")
    except EOFError:
        break
        
    if user_input.lower() == 'salir':
        print("Cerrando simulador.")
        break
        
    # Construimos el formato falso de UltraMsg / Webhook
    payload = {
        "data": {
            "from": SENDER,
            "body": user_input,
            "type": "chat",
            "pushname": "Luis Cliente",
            "fromMe": False
        }
    }
    
    # Lo lanzamos al servidor FastAPI (Taller 1)
    try:
        # Esperamos generosamente a que OpenAI piense la respuesta (10 seg max)
        requests.post(WEBHOOK_URL, json=payload, timeout=15)
        
        # Le damos 2 segundos al backend para procesar OpenAI y escribir la respuesta
        # (Dado que el bot real respondería por WA, aqui no la vemos retornado en JSON, logica 'background task')
        print("  [La IA está analizando tu mensaje en el servidor principal...]")
        time.sleep(2)
        
        print("\n👉 REVISA LA CONSOLA DONDE CORRE TU UVICORN PARA VER LO QUE RESPONDIÓ EL BOT\n")
            
    except requests.exceptions.ReadTimeout:
        print("\n⏳ La Inteligencia Artificial tardó un poco más de lo normal en pensar, pero sigue procesando.")
        print("👉 REVISA LA CONSOLA UVICORN PARA VER LO QUE RESPONDIÓ EL BOT\n")
            
    except Exception as e:
        print(f"\n❌ ERROR de conexion: {e}")
        print("¿Asegúrate de que estás corriendo el servidor 'python -m uvicorn main:app' en otra consola?\n")
