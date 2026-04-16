# 🚗 Arsenal de Skills - TallerPro SaaS

Bienvenido al directorio de Skills de TallerPro. Aquí viven los "cerebros" e instrucciones de cada agente de Inteligencia Artificial que opera en el taller.

Cada agente tiene un archivo `SKILL.md` con su rol, personalidad, instrucciones específicas y el formato en el que debe devolver la información.

## 🛠 Cómo usar estas skills

### 1. Integración en código (Recomendado para TallerPro SaaS)
Tus agentes en Python (como `sales_chat_agent.py` o `lead_detective_agent.py`) pueden leer el archivo `.md` respectivo y pasarlo como el "System Prompt" inicial del LLM.

```python
with open(".taller_skills/01-Recepcionista/SKILL.md", "r", encoding="utf-8") as f:
    system_prompt = f.read()

# Usa config.md para inyectar variables de tu taller real (ej. Tu WhatsApp, Precios)
```

### 2. Uso manual en Claude/ChatGPT
Copia el contenido del archivo `SKILL.md` completo y pégalo como primer mensaje en un chat de Claude o ChatGPT, luego de eso interactúa normalmente.

## 👥 El Equipo (10 Agentes)

1. **Agente Recepcionista** (`01-Recepcionista`): Tu cara amable en WhatsApp, da estatus y agenda.
2. **Agente Vendedor de Cotizaciones** (`02-Vendedor_Cotizaciones`): Convierte presupuestos altos en "Sí acepto" justificando seguridad y calidad.
3. **Agente Seguimiento CRM** (`03-Seguimiento_CRM`): Prospecta a clientes que no han venido en mucho tiempo y pide reseñas a los recientes.
4. **Agente Maestro Mecánico** (`04-Maestro_Mecanico`): Asistente interno para los técnicos. Diagnostica problemas con códigos OBD2 o síntomas mecánicos.
5. **Agente Publicador** (`05-Publicador`): Creación de copys para Facebook, Instagram y TikTok pensados en talleres.
6. **Agente Inventario** (`06-Inventario`): Para organizar las listas de piezas a conseguir con proveedores de refacciones.
7. **Agente Reportes** (`07-Reportes`): Resume métricas financieras, servicios populares, y desempeño del personal.
8. **Agente Triage y Averías** (`08-Triage_Averias`): Filtro de 3 preguntas de diagnóstico inicial.
9. **Agente Humanizador** (`09-Humanizador`): Para traducir el dialecto técnico "rudo" del mecánico a un resumen profesional para el cliente.
10. **Agente Garantías** (`10-Garantias`): Especializado en recuperar confianza y manejar quejas por garantías.

---
**TallerPro SaaS** - Elevando el nivel de cada Taller Mecánico.
