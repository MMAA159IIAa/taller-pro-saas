from fastapi import APIRouter, Request, HTTPException, BackgroundTasks, Depends
from typing import Dict, Any
import requests
import urllib.parse
import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

from core import database
from models import models

router = APIRouter()

# ========================================================
# 🧠 MEMORIA REDIS (MOCKEADA PARA PROTOTIPO LOCAL)
# Para producción SaaS, esto se cambia a redis.Redis()
# ========================================================
class RedisMock:
    def __init__(self):
        self.storage = {}
        
    def get(self, key):
        return self.storage.get(key)
        
    def set(self, key, value):
        self.storage[key] = value

redis_client = RedisMock()

# ========================================================
# SERVICIO WHATSAPP (Aislado)
# ========================================================
def enviar_whatsapp(instance_id: str, token: str, telefono: str, mensaje: str):
    tel = str(telefono).strip().replace(" ","").replace("-","").replace("(","").replace(")","")
    if tel.startswith("+"): tel = tel[1:]
    elif len(tel) == 10: tel = "52" + tel
        
    url = f"https://api.ultramsg.com/{instance_id}/messages/chat"
    payload = urllib.parse.urlencode({
        "token": token,
        "to": tel,
        "body": mensaje,
        "priority": "1"
    }).encode("utf-8")
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    
    try:
        req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            print(f"[WA WA WA] Enviado a {tel}. Respuesta: {data}")
    except Exception as e:
        print(f"[Error enviando WA a {tel}]: {e}")

# ========================================================
# LÓGICA DEL AGENTE DE IA (LLM Genuino OpenIA)
# ========================================================
def procesar_mensaje_vendedor_ia(db, taller_id: int, sender: str, msg: str):
    # 1. Recuperar contexto de redis_client
    context_key = f"taller_{taller_id}_client_{sender}"
    ctx = redis_client.get(context_key)
    
    if not ctx:
        # Historial de mensajes en formato OpenAI
        system_prompt = (
            "Eres el asistente y vendedor virtual experto de TallerPro. "
            "Tu objetivo principal es ayudar a los clientes a agendar una cita (fecha y hora) para su vehículo (marca/modelo) y el servicio que necesitan. "
            "⚠️ ESTRATEGIA DE VENTA (IMPORTANTE): Este taller TallerPro cuenta con una calificación impecable de 5 ESTRELLAS en Google Reviews. "
            "Si el cliente tiene dudas sobre la calidad o viene desde Google Maps, menciónale de forma muy persuasiva que somos los mejores calificados de la ciudad para darle máxima confianza. "
            "Sé breve, amable y usa emojis. Si el cliente dice 'mañana', asume la fecha. Pregunta los datos faltantes y NUNCA reveles que eres una IA."
        )
        ctx = [{"role": "system", "content": system_prompt}]
    else:
        ctx = json.loads(ctx)
        
    # Añadir mensaje del cliente actual
    ctx.append({"role": "user", "content": msg})
    
    # 2. Conectar a OpenAI Genuino (Garantizar que tienes tu OPENAI_API_KEY en variables de entorno)
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        return "⚠️ Hola, el administrador aún no ha configurado su Key de Inteligencia Artificial."

    try:
        client = OpenAI(api_key=api_key)
        
        # Llamada a IA con Herramientas (Function Calling)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=ctx,
            tools=[{
                "type": "function",
                "function": {
                    "name": "agendar_cita",
                    "description": "Agenda una cita en el taller cuando ya tengas el vehiculo, el servicio y la fecha del cliente.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "cliente_nombre": {"type": "string", "description": "Nombre del cliente si lo dio, sino vacio"},
                            "vehiculo": {"type": "string", "description": "Auto del cliente (ej. Mazda 3)"},
                            "servicio": {"type": "string", "description": "Servicio que necesita (ej. Cambio de Aceite)"},
                            "fecha": {"type": "string", "description": "Fecha y hora exacta que el cliente pida (ej. Mañana a la 1pm)"}
                        },
                        "required": ["vehiculo", "servicio", "fecha"]
                    }
                }
            }]
        )
        
        ai_message = response.choices[0].message
        
        if ai_message.tool_calls:
            # La IA decidió que ya tiene todos los datos para "agendar_cita"
            args = json.loads(ai_message.tool_calls[0].function.arguments)
            vehiculo = args.get('vehiculo')
            servicio = args.get('servicio')
            fecha = args.get('fecha')
            cliente = args.get('cliente_nombre', sender)
            
            # ¡AQUÍ GUARDARÍAMOS EN POSTGRESQL DIRECTAMENTE!
            # db.add(Registro(nombre_cliente=cliente, vehiculo=vehiculo, servicio=servicio, ...))
            # db.commit()
            
            respuesta_final = f"¡Excelente! 🎉 Acabo de agendar tu cita firmemente en nuestro sistema para: {servicio} de tu {vehiculo}.\n📅 Fecha: {fecha}\n\n¡Te esperamos en el taller!"
            
            # Limpiamos caché porque ya se cerró la venta
            redis_client.set(context_key, json.dumps([ctx[0]]))
            return respuesta_final
            
        else:
            # Respuesta conversacional natural de la IA (Guarda en Caché)
            texto_respuesta = ai_message.content
            ctx.append({"role": "assistant", "content": texto_respuesta})
            # Mantener contexto corto (últimos 10 mensajes)
            if len(ctx) > 10: ctx = [ctx[0]] + ctx[-9:]
            redis_client.set(context_key, json.dumps(ctx))
            return texto_respuesta

    except Exception as e:
        print(f"Error IA: {e}")
        return "Tuvimos un pequeño problema técnico, pero seguimos atendiéndote. ¿En qué te podemos ayudar?"

# ========================================================
# WEBHOOK ENDPOINT
# ========================================================
@router.post("/v1/webhook/{taller_id}")
async def webhook_receiver(taller_id: int, request: Request, background_tasks: BackgroundTasks):
    try:
        data = await request.json()
        
        # Formato habitual de UltraMsg
        msg_data = data.get("data", data)
        msg_body = str(msg_data.get("body") or "").strip()
        sender   = str(msg_data.get("from") or "").strip()
        from_me  = msg_data.get("fromMe", False)

        if from_me or not msg_body or msg_data.get("type") != "chat":
            return {"status": "ignored"}
            
        print(f"WEBHOOK Recibido en SaaS para Taller {taller_id} -> De: {sender} | Msg: {msg_body}")

        # Aquí obtendrías las credenciales de WhatsApp del Taller desde PostgreSQL
        # session = database.SessionLocal()
        # taller = session.query(models.Taller).filter(models.Taller.id == taller_id).first()
        # if not taller: return {"status": "error"}
        
        # Simulación de generacion de respuesta inteligente (Function Calling / NLP)
        respuesta = procesar_mensaje_vendedor_ia(db=None, taller_id=taller_id, sender=sender, msg=msg_body)
        
        # Lanzar el envio al worker en background para no trabar el webhook
        # background_tasks.add_task(enviar_whatsapp, taller.whatsapp_instance, taller.whatsapp_token, sender, respuesta)
        
        # Para test, solo imprimimos
        print(f"I.A. RESPUESTA: {respuesta}")
        
        return {"status": "ok", "procesado": True}
        
    except Exception as e:
        return {"status": "error", "detalles": str(e)}
