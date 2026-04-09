import time
import os
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from agentes.contador_import_agent import importar_excel_contador
from utils.logger import info, error

CARPETA_CONTADOR = r"C:\TallerPro_Contador"

class ExcelSyncHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and (event.src_path.endswith('.xlsx') or event.src_path.endswith('.csv')):
            info("AutoSyncAgent", f"¡Nuevo archivo detectado del contador! {event.src_path}")
            # Damos 2 segundos para que el contador termine de copiar/guardar el archivo físico
            time.sleep(2)
            try:
                res = importar_excel_contador(event.src_path)
                if res:
                    info("AutoSyncAgent", f"Archivo importado silenciosamente con éxito: {res}")
            except Exception as e:
                error("AutoSyncAgent", f"Fallo importando en background: {e}")

class AutoSyncAgent:
    """
    Agente 24/7 que vigila la carpeta del contador.
    Si detecta un archivo nuevo de excel, arranca la inserción a BD automáticamente.
    """
    def __init__(self):
        self.observer = Observer()
        self.en_ejecucion = False

    def iniciar(self):
        if not os.path.exists(CARPETA_CONTADOR):
            try:
                os.makedirs(CARPETA_CONTADOR)
                info("AutoSyncAgent", f"Carpeta Mágica creada en {CARPETA_CONTADOR}")
            except Exception as e:
                error("AutoSyncAgent", f"No se pudo crear carpeta de monitoreo: {e}")
                return

        event_handler = ExcelSyncHandler()
        self.observer.schedule(event_handler, CARPETA_CONTADOR, recursive=False)
        self.observer.start()
        self.en_ejecucion = True
        info("AutoSyncAgent", f"Iniciado. Vigilando {CARPETA_CONTADOR}...")

    def detener(self):
        if self.en_ejecucion:
            self.observer.stop()
            self.observer.join()
            self.en_ejecucion = False
            info("AutoSyncAgent", "Agente Vigiilante detenido.")

def iniciar_agente_en_background():
    agente = AutoSyncAgent()
    hilo = threading.Thread(target=agente.iniciar, daemon=True)
    hilo.start()
    return agente
