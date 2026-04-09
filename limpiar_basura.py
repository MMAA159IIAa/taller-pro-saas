import sqlite3
import os

def limpiar():
    db_path = r"c:\Users\leech\OneDrive\Documentos\taller_pro_v3\taller_pro.db"
    if not os.path.exists(db_path):
        print(f"No se encontro la DB en {db_path}")
        return

    conn = sqlite3.connect(db_path)
    
    # 1. Identificar basura en registros
    # Filas que no tienen cliente real, o tienen nombres de gastos
    basura_nombres = [
        'None', 'NOTA DE VENTA', 'SEMANA DEL%', 'CANTIDAD', 'CONCEPTO', 'FECHA',
        '%COMIDA%', 'PLAN FUNERARIO', 'DEPOSITO%', 'FACTURA%', 'RETIRO%', 'PAGO%'
    ]
    
    total_borrado = 0
    for patron in basura_nombres:
        res = conn.execute("DELETE FROM registros WHERE nombre LIKE ? OR servicio LIKE ?", (patron, patron))
        total_borrado += res.rowcount
        
    # Borrar filas donde casi todo es None
    res = conn.execute("DELETE FROM registros WHERE (nombre IS NULL OR nombre = 'None') AND (auto IS NULL OR auto = 'None')")
    total_borrado += res.rowcount

    conn.commit()
    print(f"Limpieza completada. Se eliminaron {total_borrado} entradas de basura de la tabla de Clientes.")
    conn.close()

if __name__ == "__main__":
    limpiar()
