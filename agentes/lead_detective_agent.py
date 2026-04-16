from agentes.base_agent import BaseAgent
from utils.database import conectar, get_config
from datetime import datetime
from dateutil.relativedelta import relativedelta
from servicios.whatsapp_service import WhatsAppService

try:
    from agentes.crm_ia_agent import CRMAgent
except ImportError:
    CRMAgent = None

class LeadDetectiveAgent(BaseAgent):
    """
    Agente Autónomo "El Vendedor Invisible".
    Busca clientes entregados hace 3 días o 6 meses.
    Genera redacción mediante IA y se los dispara automáticamente por WhatsApp.
    """
    def __init__(self):
        # 86400 segundos = 24 horas (En producción corre 1 vez al día).
        # Para desarrollo, lo dejaremos en 1 hora, de todos modos filtramos con SQLite.
        super().__init__("LeadDetectiveCRM", intervalo_segundos=3600)
        self.wa = WhatsAppService()
        self.ia = CRMAgent() if CRMAgent else None

    def ejecutar_tarea(self):
        self.log("Encendiendo motores de búsqueda de CRM...")
        self._campaña_reseñas_3_dias()
        self._campaña_mantenimiento_6_meses()

    def _campaña_reseñas_3_dias(self):
        """
        Busca autos Entregados hace exactamente 3 días que no hayan recibido
        un mensaje del tipo 'seguimiento_3_dias'.
        """
        conn = conectar()
        ahora = datetime.now()
        hace_3_dias = (ahora - relativedelta(days=3)).strftime("%Y-%m-%d")
        
        # Filtramos los que se entregaron exactamente en esa fecha
        candidatos = conn.execute("""
            SELECT id, nombre, telefono, auto, servicio 
            FROM registros 
            WHERE estatus='Entregado' AND fecha LIKE ? AND telefono != ''
            AND id NOT IN (SELECT cliente_id FROM seguimiento WHERE tipo='seguimiento_3_dias')
        """, (f"{hace_3_dias}%",)).fetchall()
        conn.close()

        for c in candidatos:
            id_reg, nombre, tel, auto, servicio = c
            
            # 1. Usar IA para redactar si está prendida
            usar_ia = get_config("usar_ia_crm", "1") == "1"
            msg = ""
            
            if usar_ia and self.ia:
                try:
                    msg = self.ia.redactar_seguimiento_3_dias(nombre, auto, servicio)
                except Exception as e:
                    self.log(f"Fallo IA en CRM 3 Días: {e}")
            
            # 2. Si falló la IA o está apagada, usamos un texto seguro alternativo
            if not msg:
                msg = (f"Hola {nombre}, esperamos estés muy bien. Hace 3 días te entregamos tu {auto}. "
                       "Nos encantaría saber qué te pareció nuestro servicio. Si estás completamente "
                       "satisfecho, por favor ayúdanos con 5 estrellas en Google: [Link].")
            
            # 3. Enviar por WhatsApp
            enviado = self.wa.enviar(tel, msg)
            
            # 4. Registrar que ya se contactó para no ser spam
            if enviado:
                self.log(f"✅ ¡WhatsApp de Calidad 5 Estrellas enviado a {nombre} ({auto})!")
                conn = conectar()
                conn.execute("INSERT INTO seguimiento (cliente_id, fecha_envio, tipo, mensaje) VALUES (?,?,?,?)",
                             (id_reg, ahora.strftime("%Y-%m-%d %H:%M:%S"), 'seguimiento_3_dias', msg))
                conn.commit()
                conn.close()

    def _campaña_mantenimiento_6_meses(self):
        """
        Busca autos que no han vuelto en 6 meses.
        """
        conn = conectar()
        ahora = datetime.now()
        hace_6_meses = (ahora - relativedelta(months=6)).strftime("%Y-%m-%d")
        
        candidatos = conn.execute("""
            SELECT id, nombre, telefono, auto, servicio 
            FROM registros 
            WHERE estatus='Entregado' AND fecha LIKE ? AND telefono != ''
            AND id NOT IN (SELECT cliente_id FROM seguimiento WHERE tipo='seguimiento_6_meses')
        """, (f"{hace_6_meses}%",)).fetchall()
        conn.close()

        for c in candidatos:
            id_reg, nombre, tel, auto, servicio = c
            
            usar_ia = get_config("usar_ia_crm", "1") == "1"
            msg = ""
            if usar_ia and self.ia:
                try:
                    msg = self.ia.redactar_seguimiento_6_meses(nombre, auto, servicio)
                except Exception as e:
                    self.log(f"Fallo IA en CRM 6 Meses: {e}")
                    
            if not msg:
                msg = (f"¡Hola {nombre}! Han pasado 6 meses desde el último servicio que le hicimos a tu {auto}. "
                       "Prevenir es mejor que reparar. ¿Te gustaría agendar una revisión rápida de niveles y frenos hoy?")

            enviado = self.wa.enviar(tel, msg)
            if enviado:
                self.log(f"✅ ¡Recordatorio preventivo (Upsell) enviado a {nombre} ({auto})!")
                conn = conectar()
                conn.execute("INSERT INTO seguimiento (cliente_id, fecha_envio, tipo, mensaje) VALUES (?,?,?,?)",
                             (id_reg, ahora.strftime("%Y-%m-%d %H:%M:%S"), 'seguimiento_6_meses', msg))
                conn.commit()
                conn.close()
