import sqlite3
import os

db_path = "taller_pro.db"
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    print("=== Ultimos 10 Logs del Sistema ===")
    logs = conn.execute("SELECT * FROM logs ORDER BY id DESC LIMIT 10").fetchall()
    for log in logs:
        print(log)
    
    print("\n=== Conteo de Finanzas ===")
    ingresos = conn.execute("SELECT COUNT(*) FROM finanzas WHERE tipo='Ingreso'").fetchone()[0]
    egresos = conn.execute("SELECT COUNT(*) FROM finanzas WHERE tipo='Egreso'").fetchone()[0]
    print(f"Ingresos: {ingresos}")
    print(f"Egresos: {egresos}")
    
    print("\n=== Ultimos 5 movimientos de finanzas ===")
    movs = conn.execute("SELECT tipo, concepto, monto, fecha FROM finanzas ORDER BY id DESC LIMIT 5").fetchall()
    for m in movs:
        print(m)
    conn.close()
else:
    print("DB no encontrada")
