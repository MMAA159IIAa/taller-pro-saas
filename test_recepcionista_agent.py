from agentes.recepcionista_agent import RecepcionistaAgent

def probar_recepcionista():
    print("\n--- INICIANDO AGENTE RECEPCIONISTA ---")
    print("El agente intentará conectar con local/openai/claude según lo que tengas en la BD.")
    print("Si crashea por falta de API Key, asegurate de configurarla primero.\n")
    
    agente = RecepcionistaAgent()
    
    print("Agente cargado. Usa 'salir' para terminar el chat.\n")
    
    while True:
        try:
            mensaje = input("Tú (Cliente): ")
            if mensaje.lower() in ["salir", "exit", "quit"]:
                break
                
            # Simulamos que somos un cliente llamado "Roberto"
            respuesta = agente.procesar_mensaje_entrante(1, "Roberto", mensaje)
            print(f"\nRecepcionista TallerPro: {respuesta}\n")
            
        except Exception as e:
            print(f"\n[ERROR] Algo salió mal probando el agente: {e}\n")

if __name__ == "__main__":
    probar_recepcionista()
