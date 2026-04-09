import sqlite3
import os

def limpiar_en_ruta(p):
    if not os.path.exists(p): return
    print(f"Buscando basura en: {p}")
    conn = sqlite3.connect(p)
    try:
        # Purgar basado en lo visto en el screenshot
        patrones = ["None", "NOTA DE VENTA", "%COMIDA%", "PLAN FUNERARIO", "DEPOSITO%", "FACTURA%", "SEMANA%", "CANTIDAD", "CONCEPTO", "FECHA", "SUM(%", "=D%"]
        total = 0
        for pat in patrones:
            res = conn.execute("DELETE FROM registros WHERE nombre LIKE ? OR servicio LIKE ? OR correo LIKE ?", (pat, pat, pat))
            total += res.rowcount
        
        # Casos específicos de la captura
        res = conn.execute("DELETE FROM registros WHERE nombre IS NULL OR nombre = 'None' OR nombre = ''")
        total += res.rowcount
        
        conn.commit()
        if total > 0:
            print(f"!!! Limpiadas {total} filas de basura en {p}")
    except Exception as e:
        print(f"Error en {p}: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    rutas = [
        r"c:\Users\leech\OneDrive\Documentos\taller_pro_v3\taller_pro.db",
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "TallerPro", "taller_pro.db"),
        "taller_pro.db"
    ]
    for r in rutas:
        limpiar_en_ruta(r)
