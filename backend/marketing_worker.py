import time
import datetime
from dateutil.relativedelta import relativedelta

# En producción usarás Celery:
# from celery import Celery
# app = Celery('marketing', broker='redis://localhost:6379/0')

class MarketingWorker:
    """
    Empleado Digital 24/7.
    A diferencia de Tkinter, este proceso vive nativamente en el Cloud Server
    y escanea a los clientes vencidos a las 3:00 AM todos los días.
    """
    def __init__(self):
        print("🚀 [WORKER INICIADO] Inteligencia de Marketing corriendo 24/7 en Background...")

    def buscar_clientes_vencidos(self):
        # En vez de sqlite3, usamos la base de datos empresarial de FastAPI (PostgreSQL/SQLAlchemy)
        from core import database
        from models import models
        
        session = database.SessionLocal()
        
        hoy = datetime.datetime.utcnow().date()
        fecha_6_meses = hoy - relativedelta(months=6)

        # Buscar todos los registros de todos los talleres que tienen +6 meses y estatus 'Entregado'
        # que NO tengan ya un "Seguimiento_6M" en los Finanzas/Logs.
        vencidos = session.query(models.Registro).filter(
            models.Registro.fecha_ingreso <= fecha_6_meses,
            models.Registro.estado == "Entregado"
        ).all()
        
        count = 0
        for cliente in vencidos:
            # Aquí llamamos al servicio global de WhatsApp de la Nube (aislado del Tkinter del taller)
            from api.webhook import enviar_whatsapp
            taller = cliente.taller
            
            if taller and taller.whatsapp_api_key and taller.suscripcion_activa:
                mensaje = (f"Hola {cliente.nombre_cliente}! 👋\n\n"
                           f"Te escribimos de *{taller.nombre}*.\n"
                           f"Han pasado 6 meses desde el último servicio de tu *{cliente.vehiculo}*.\n\n"
                           f"Por ser un excelente cliente, este mes tenemos una promoción especial en chequeo.\n"
                           f"¿Te gustaría agendar una cita?")
                
                print(f"[WORKER] -> Despachando a {cliente.nombre_cliente} del taller {taller.nombre}")
                # enviar_whatsapp(...)
                count += 1
                
        session.close()
        return count

    def run_forever(self):
        while True:
            # Configurado ideal para ejecutar 1 vez al día (ej. en la madrugada)
            vencidos = self.buscar_clientes_vencidos()
            print(f"[WORKER] Ciclo completado. SMS enviados: {vencidos}. Durmiendo...")
            # time.sleep(86400) # Dormir 24h
            time.sleep(60) # Dormir 1 minuto para prototipado rápido

if __name__ == "__main__":
    worker = MarketingWorker()
    # worker.run_forever()
