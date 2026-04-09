from datetime import datetime
from utils.database import conectar

def log(nivel, modulo, mensaje):
    print(f"[{nivel}] {modulo}: {mensaje}")
    try:
        conn = conectar()
        conn.execute("INSERT INTO logs (fecha,nivel,modulo,mensaje) VALUES (?,?,?,?)",
                     (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), nivel, modulo, mensaje))
        conn.commit()
        conn.close()
    except:
        pass

def info(modulo, msg):  log("INFO",  modulo, msg)
def error(modulo, msg): log("ERROR", modulo, msg)
def warn(modulo, msg):  log("WARN",  modulo, msg)
