from agentes.base_agent import BaseAgent
from utils.database import conectar
from datetime import datetime
from dateutil.relativedelta import relativedelta
import random

class LeadDetectiveAgent(BaseAgent):
    """
    Agente autónomo que busca oportunidades de venta
    analizando el historial de clientes y servicios.
    """
    def __init__(self):
        super().__init__("LeadDetective", intervalo_segundos=120) # Revisa cada 2 min para demo

    def ejecutar_tarea(self):
        self.log("Escaneando base de datos en busca de oportunidades...")
        
        conn = conectar()
        ahora = datetime.now()
        
        # 1. Buscar clientes que no han venido en 6 meses (Upsell preventivo)
        seis_meses_atras = (ahora - relativedelta(months=6)).strftime("%Y-%m-%d")
        
        prospectos = conn.execute("""
            SELECT nombre, auto, fecha FROM registros 
            WHERE fecha <= ? AND id NOT IN (SELECT id FROM prospectos WHERE estatus='Nuevo')
            LIMIT 5
        """, (seis_meses_atras,)).fetchall()
        
        encontrados = 0
        for p in prospectos:
            nombre, auto, ultima_fecha = p
            interes = f"Servicio preventivo para {auto} (última visita: {ultima_fecha})"
            
            # Registrar como prospecto detectado
            conn.execute("INSERT INTO prospectos (nombre, auto, interes, fecha) VALUES (?,?,?,?)",
                         (nombre, auto, interes, ahora.strftime("%Y-%m-%d")))
            self.log(f"Oportunidad detectada: {nombre} necesita mantenimiento para su {auto}.")
            encontrados += 1
            
        # 2. Simular 'Scouting' externo (Simulación de lo que vio en el video)
        if random.random() > 0.7:
            fuentes = ["Marketplace local", "Inquiry via Web", "Comunidad de Facebook"]
            fuente = random.choice(fuentes)
            proximos_carros = ["Toyota Hilux", "Nissan Versa", "Mazda 3", "Honda Civic"]
            carro = random.choice(proximos_carros)
            self.log(f"Rastreando {fuente}... detecté posible cliente interesado en frenos para {carro}.")
            
        conn.commit()
        conn.close()
        
        if encontrados > 0:
            self.log(f"Análisis completado. {encontrados} nuevas oportunidades añadidas al tablero.")
        else:
            self.log("No se encontraron nuevas oportunidades en este ciclo.")
