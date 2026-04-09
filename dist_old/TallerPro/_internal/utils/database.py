import sqlite3
import os
import sys

def obtener_ruta_db():
    if getattr(sys, 'frozen', False):
        base_path = os.path.join(os.environ['LOCALAPPDATA'], "TallerPro")
    else:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.makedirs(base_path, exist_ok=True)
    return os.path.join(base_path, "taller_pro.db")

DB_NAME = obtener_ruta_db()

def conectar():
    return sqlite3.connect(DB_NAME)

def crear_tablas():
    conn = conectar()
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS registros (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT, telefono TEXT, correo TEXT,
        auto TEXT, numero_economico TEXT, placas TEXT,
        servicio TEXT, fecha TEXT, costo REAL DEFAULT 0,
        estatus TEXT DEFAULT 'Pendiente',
        notificado INTEGER DEFAULT 0,
        recibo_enviado INTEGER DEFAULT 0)""")
    c.execute("""CREATE TABLE IF NOT EXISTS finanzas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tipo TEXT, concepto TEXT, monto REAL,
        fecha TEXT, notas TEXT,
        hash_duplicado TEXT UNIQUE)""")
    c.execute("""CREATE TABLE IF NOT EXISTS config (
        clave TEXT PRIMARY KEY, valor TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TEXT, nivel TEXT, modulo TEXT, mensaje TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS seguimiento (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente_id INTEGER, fecha_envio TEXT,
        tipo TEXT, mensaje TEXT)""")
    conn.commit()
    conn.close()

def get_config(clave, default=""):
    conn = conectar()
    row = conn.execute("SELECT valor FROM config WHERE clave=?", (clave,)).fetchone()
    conn.close()
    return row[0] if row else default

def set_config(clave, valor):
    conn = conectar()
    conn.execute("INSERT OR REPLACE INTO config (clave,valor) VALUES (?,?)", (clave, valor))
    conn.commit()
    conn.close()
