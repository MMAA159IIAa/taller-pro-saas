import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, request, jsonify
from agentes.sales_chat_agent import SalesChatAgent
from servicios.whatsapp_service import WhatsAppService
from utils.database import conectar, get_config
from utils.logger import info, error
from datetime import datetime

app = Flask(__name__)

# Contexto por numero — guarda estado de conversacion
conversaciones = {}

def get_contexto(telefono):
    if telefono not in conversaciones:
        conversaciones[telefono] = {
            "agente":    SalesChatAgent(),
            "esperando": None,
            "datos_cita": {}
        }
    return conversaciones[telefono]

def guardar_cliente_si_nuevo(nombre, telefono):
    try:
        tel_limpio = telefono.replace("@c.us", "").replace("+", "")
        conn = conectar()
        existe = conn.execute(
            "SELECT id FROM registros WHERE telefono=?", (tel_limpio,)
        ).fetchone()
        if not existe and nombre and telefono:
            conn.execute("""
                INSERT INTO registros
                (nombre, telefono, correo, auto, numero_economico, placas,
                 servicio, fecha, costo, estatus)
                VALUES (?,?,?,?,?,?,?,?,?,?)
            """, (nombre, tel_limpio, "", "", "", "", "Consulta WhatsApp",
                  datetime.now().strftime("%Y-%m-%d"), 0, "Pendiente"))
            conn.commit()
            info("Webhook", f"Nuevo cliente: {nombre} - {tel_limpio}")
        conn.close()
    except Exception as ex:
        error("Webhook", f"Error guardando cliente: {ex}")

def procesar_mensaje(sender, nombre, msg):
    ctx    = get_contexto(sender)
    agente = ctx["agente"]
    wa     = WhatsAppService()
    taller = get_config("taller_nombre", "Multiservicios Loredo")
    tel_jefe = get_config("taller_tel", "6621480247")
    msg_lower = msg.lower().strip()

    afirmaciones = ["si","sí","ok","claro","dale","andale","va","perfecto",
                    "por favor","porfavor","quiero","adelante","yes","bueno",
                    "agendame","agenda","agendar","cita","una cita","quiero cita"]

    dias = ["lunes","martes","miercoles","miércoles","jueves","viernes",
            "sabado","sábado","domingo","mañana","hoy","pasado"]

    horas = ["1","2","3","4","5","6","7","8","9","10","11","12",
             "tarde","mañana","mediodía","mediodia","am","pm"]

    # ── FLUJO DE CITA ─────────────────────────────────────────────────────────
    if ctx["esperando"] == "fecha_cita":
        ctx["datos_cita"]["fecha"] = msg
        ctx["esperando"] = "nombre_cita"
        return f"Perfecto! ✅ El {msg}.\n¿Me das tu nombre completo para confirmar la cita?"

    if ctx["esperando"] == "nombre_cita":
        ctx["datos_cita"]["nombre"] = msg
        ctx["esperando"] = "tel_cita"
        return f"Gracias {msg}! 😊\n¿Y tu número de teléfono para confirmarte?"

    if ctx["esperando"] == "tel_cita":
        ctx["datos_cita"]["tel"] = msg
        ctx["esperando"] = None
        serv  = agente.contexto_servicio or "servicio"
        fecha = ctx["datos_cita"].get("fecha", "")
        nom   = ctx["datos_cita"].get("nombre", nombre)
        ctx["datos_cita"] = {}
        return (f"✅ *Cita confirmada!*\n\n"
                f"👤 {nom}\n"
                f"🔧 {serv.title()}\n"
                f"📅 {fecha}\n\n"
                f"Te esperamos en *{taller}*.\n"
                f"Para mayor atención personalizada contacta directo al:\n"
                f"📞 *{tel_jefe}*\n\n"
                f"¡Hasta pronto! 🚗")

    # ── DETECTAR INTENCION DE CITA ────────────────────────────────────────────
    quiere_cita = any(p in msg_lower for p in afirmaciones)
    da_fecha    = any(p in msg_lower for p in dias) or any(p in msg_lower for p in horas)
    tiene_contexto = agente.contexto_servicio is not None

    if (quiere_cita and tiene_contexto) or da_fecha:
        # Si ya dio la fecha directamente
        if da_fecha and not quiere_cita:
            ctx["datos_cita"]["fecha"] = msg
            ctx["esperando"] = "nombre_cita"
            return f"Perfecto! ✅ El {msg}.\n¿Me das tu nombre completo para confirmar la cita?"
        else:
            ctx["esperando"] = "fecha_cita"
            serv = agente.contexto_servicio or "servicio"
            return f"Con gusto te agendo la cita para *{serv}*. 📅\n¿Qué día y hora te viene mejor?"

    # ── RESPUESTA NORMAL DEL AGENTE ───────────────────────────────────────────
    respuesta = agente.responder(msg)

    # Agregar numero del jefe si pregunta por precio o quiere mas info
    if any(p in msg_lower for p in ["precio","costo","cuanto","cotizacion","mas informacion","info"]):
        respuesta += f"\n\nPara una cotización exacta llama directo al:\n📞 *{tel_jefe}*"

    return respuesta

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.json or request.form.to_dict()

        if "data" in data:
            msg_data = data["data"]
        else:
            msg_data = data

        msg_body = str(msg_data.get("body") or "").strip()
        sender   = str(msg_data.get("from") or "").strip()
        nombre   = str(msg_data.get("pushname") or "Cliente").strip()
        from_me  = msg_data.get("fromMe", False)

        if from_me:
            return jsonify({"status": "ignored"})

        if not msg_body or not sender or msg_data.get("type") != "chat":
            return jsonify({"status": "empty"})

        info("Webhook", f"{nombre}: {msg_body}")

        respuesta = procesar_mensaje(sender, nombre, msg_body)
        guardar_cliente_si_nuevo(nombre, sender)

        wa = WhatsAppService()
        wa.enviar(sender, respuesta)

        info("Webhook", f"Respondido a {nombre}: {respuesta[:60]}")
        return jsonify({"status": "ok"})

    except Exception as ex:
        error("Webhook", f"Error: {ex}")
        return jsonify({"status": "error", "message": str(ex)}), 500

@app.route("/", methods=["GET"])
def index():
    return jsonify({"status": "TallerPro Webhook activo"})

if __name__ == "__main__":
    print("=" * 50)
    print("TALLERPRO WEBHOOK INICIADO")
    print("Escuchando mensajes de WhatsApp...")
    print("=" * 50)
    app.run(host="0.0.0.0", port=5000, debug=False)
