import openpyxl
import sqlite3
import os
import sys
from datetime import datetime

# Setup paths
sys.path.insert(0, os.getcwd())
from agentes.contador_import_agent import importar_excel_contador
from utils.database import crear_tablas

# Test DB
db_test = "test_import_v2.db"
if os.path.exists(db_test): os.remove(db_test)

# Parchear el DB_NAME de utils.database para el test
import utils.database
utils.database.DB_NAME = db_test

# Crear tablas reales
crear_tablas()

# También parcheamos el logger para ver errores en consola
import agentes.contador_import_agent
def log_error(mod, msg): print(f"[DB_ERROR] {mod}: {msg}")
def log_info(mod, msg): print(f"[INFO] {mod}: {msg}")
agentes.contador_import_agent.error = log_error
agentes.contador_import_agent.info = log_info

ruta_excel = r"c:\Users\leech\OneDrive\Documentos\RELACION DE CARROS 2026.xlsx"
print(f"Probando importación de: {ruta_excel}")

res = importar_excel_contador(ruta_excel)

print(f"\nResultados del importador: {res}")

if res:
    conn = sqlite3.connect(db_test)
    print("\n--- Conteo de Registros en DB ---")
    reg_count = conn.execute("SELECT COUNT(*) FROM registros").fetchone()[0]
    fin_ing_count = conn.execute("SELECT COUNT(*) FROM finanzas WHERE tipo='Ingreso'").fetchone()[0]
    fin_eg_count = conn.execute("SELECT COUNT(*) FROM finanzas WHERE tipo='Egreso'").fetchone()[0]
    print(f"Clientes (registros): {reg_count}")
    print(f"Ingresos (finanzas): {fin_ing_count}")
    print(f"Egresos (finanzas): {fin_eg_count}")
    
    print("\nUltimos 5 Egresos:")
    egresos = conn.execute("SELECT concepto, monto, fecha, notas FROM finanzas WHERE tipo='Egreso' ORDER BY id DESC LIMIT 5").fetchall()
    for eg in egresos:
        print(eg)
    conn.close()
else:
    print("La función importar_excel_contador devolvió None")
