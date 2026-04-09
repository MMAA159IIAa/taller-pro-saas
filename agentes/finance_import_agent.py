import os
import hashlib
import threading
import time
from datetime import datetime
from utils.database import conectar
from utils.logger import info, error, warn

class FinanceImportAgent:
    """
    - Importa Excel/CSV del contador a la tabla finanzas
    - Detecta automaticamente si son ingresos o egresos
    - Valida duplicados con hash
    - Modo vigilancia: monitorea una carpeta y auto-importa archivos nuevos
    """

    PALABRAS_INGRESO = ["ingreso","venta","cobro","pago recibido","entrada","deposito","factura","servicio"]
    PALABRAS_EGRESO  = ["egreso","gasto","compra","pago","salida","retiro","proveedor","renta","luz","agua","nomina"]

    def __init__(self):
        self.activo        = False
        self.hilo          = None
        self.carpeta_watch = None

    def detectar_tipo(self, concepto):
        c = str(concepto).lower()
        for p in self.PALABRAS_EGRESO:
            if p in c: return "Egreso"
        for p in self.PALABRAS_INGRESO:
            if p in c: return "Ingreso"
        return "Ingreso"

    def generar_hash(self, tipo, concepto, monto, fecha):
        raw = f"{tipo}{concepto}{monto}{fecha}".lower().replace(" ","")
        return hashlib.md5(raw.encode()).hexdigest()

    def importar_archivo(self, ruta):
        try:
            if ruta.endswith(".xlsx"):
                import openpyxl
                wb = openpyxl.load_workbook(ruta)
                ws = wb.active
                filas = list(ws.iter_rows(min_row=2, values_only=True))
            elif ruta.endswith(".csv"):
                import csv
                with open(ruta, encoding="utf-8-sig") as f:
                    filas = list(csv.reader(f))[1:]
            else:
                warn("FinanceImportAgent", f"Formato no soportado: {ruta}")
                return 0, 0

            conn = conectar()
            importados = duplicados = 0

            for fila in filas:
                if not any(fila): continue
                try:
                    # Intentar detectar columnas flexiblemente
                    concepto = str(fila[0] or "Sin concepto")
                    monto_raw = fila[1] if len(fila) > 1 else 0
                    fecha_raw = fila[2] if len(fila) > 2 else datetime.now().strftime("%Y-%m-%d")
                    notas     = str(fila[3]) if len(fila) > 3 else ""

                    # Si hay columna de tipo explícita
                    if len(fila) > 4 and str(fila[4]).strip().lower() in ["ingreso","egreso"]:
                        tipo = str(fila[4]).strip().capitalize()
                    else:
                        tipo = self.detectar_tipo(concepto)

                    try: monto = float(str(monto_raw).replace("$","").replace(",","").strip() or 0)
                    except: monto = 0.0

                    try:
                        if isinstance(fecha_raw, datetime):
                            fecha = fecha_raw.strftime("%Y-%m-%d")
                        else:
                            fecha = str(fecha_raw)[:10]
                    except:
                        fecha = datetime.now().strftime("%Y-%m-%d")

                    hash_dup = self.generar_hash(tipo, concepto, monto, fecha)

                    try:
                        conn.execute("""INSERT INTO finanzas (tipo,concepto,monto,fecha,notas,hash_duplicado)
                                        VALUES (?,?,?,?,?,?)""",
                                     (tipo, concepto, monto, fecha, notas, hash_dup))
                        importados += 1
                    except Exception:
                        duplicados += 1

                except Exception as ex:
                    error("FinanceImportAgent", f"Error en fila {fila}: {ex}")

            conn.commit()
            conn.close()
            info("FinanceImportAgent", f"Importado: {importados} registros, {duplicados} duplicados omitidos")
            return importados, duplicados

        except Exception as ex:
            error("FinanceImportAgent", f"Error importando {ruta}: {ex}")
            return 0, 0

    def iniciar_vigilancia(self, carpeta):
        if self.activo: return
        if not os.path.exists(carpeta):
            error("FinanceImportAgent", f"Carpeta no existe: {carpeta}")
            return
        self.carpeta_watch = carpeta
        self.activo = True
        self.archivos_procesados = set(os.listdir(carpeta))
        self.hilo = threading.Thread(target=self._loop_vigilancia, daemon=True)
        self.hilo.start()
        info("FinanceImportAgent", f"Vigilando carpeta: {carpeta}")

    def detener_vigilancia(self):
        self.activo = False

    def _loop_vigilancia(self):
        while self.activo:
            try:
                actuales = set(os.listdir(self.carpeta_watch))
                nuevos   = actuales - self.archivos_procesados
                for archivo in nuevos:
                    if archivo.endswith((".xlsx",".csv")):
                        ruta = os.path.join(self.carpeta_watch, archivo)
                        time.sleep(2)  # esperar que termine de copiarse
                        imp, dup = self.importar_archivo(ruta)
                        info("FinanceImportAgent", f"Auto-importado {archivo}: {imp} registros")
                self.archivos_procesados = actuales
            except Exception as ex:
                error("FinanceImportAgent", f"Error vigilancia: {ex}")
            time.sleep(10)
