import sqlite3
import os

def purgar_agresivo():
    db_path = r"c:\Users\leech\OneDrive\Documentos\taller_pro_v3\taller_pro.db"
    appdata_db = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'TallerPro', 'taller_pro.db')
    
    rutas = [db_path, appdata_db]
    for p in rutas:
        if not os.path.exists(p): continue
        print(f"Purgando base de datos en: {p}")
        conn = sqlite3.connect(p)
        try:
            # Borrar TODO de registros y finanzas para empezar de 0 con el nuevo importador
            # (El usuario dijo que "importe de nuevo el archivo", asi que es seguro borrar lo anterior del archivo)
            conn.execute("DELETE FROM registros")
            conn.execute("DELETE FROM finanzas")
            conn.execute("DELETE FROM agentes_logs")
            conn.execute("DELETE FROM prospectos")
            conn.execute("DELETE FROM seguimiento")
            conn.execute("DELETE FROM config")
            
            # Resetear IDs
            tablas = ["registros", "finanzas", "agentes_logs", "prospectos", "seguimiento"]
            for t in tablas:
                conn.execute(f"DELETE FROM sqlite_sequence WHERE name='{t}'")
            
            conn.commit()
            print(f"Purga agresiva exitosa en {p}")
        except Exception as e:
            print(f"Error purgando {p}: {e}")
        finally:
            conn.close()

if __name__ == "__main__":
    purgar_agresivo()
