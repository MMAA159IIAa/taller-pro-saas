# compile.py - Script de compilacion TallerPro
import subprocess
import sys
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

cmd = [
    sys.executable, "-m", "PyInstaller",
    "--onefile",
    "--windowed",
    "--icon=icono.ico",
    "--name=TallerPro",
    # Datos
    "--add-data=agentes;agentes",
    "--add-data=servicios;servicios",
    "--add-data=utils;utils",
    "--add-data=.taller_skills;.taller_skills",
    "--add-data=icono.ico;.",
    # Modulos ocultos - agentes
    "--hidden-import=agentes",
    "--hidden-import=agentes.notification_agent",
    "--hidden-import=agentes.sales_agent",
    "--hidden-import=agentes.finance_import_agent",
    "--hidden-import=agentes.sales_chat_agent",
    "--hidden-import=agentes.base_agent",
    "--hidden-import=agentes.lead_detective_agent",
    "--hidden-import=agentes.humanizador_agent",
    "--hidden-import=agentes.crm_ia_agent",
    "--hidden-import=agentes.auto_sync_agent",
    "--hidden-import=agentes.contador_import_agent",
    "--hidden-import=agentes.gemma_agent",
    # Modulos ocultos - servicios
    "--hidden-import=servicios",
    "--hidden-import=servicios.email_service",
    "--hidden-import=servicios.whatsapp_service",
    "--hidden-import=servicios.recibo_generator",
    # Modulos ocultos - utils
    "--hidden-import=utils",
    "--hidden-import=utils.database",
    "--hidden-import=utils.logger",
    "--hidden-import=utils.license_utils",
    # Dependencias
    "--hidden-import=requests",
    "--hidden-import=tkcalendar",
    "--hidden-import=dateutil",
    "--hidden-import=dateutil.relativedelta",
    "--hidden-import=openpyxl",
    "--hidden-import=openpyxl.styles",
    "--hidden-import=openpyxl.chart",
    "--hidden-import=reportlab",
    "--hidden-import=watchdog",
    "--hidden-import=watchdog.observers",
    "--hidden-import=watchdog.events",
    "--collect-all=tkcalendar",
    "--collect-all=openpyxl",
    "main.py"
]

print("Compilando TallerPro...")
print("Esto puede tardar 2-5 minutos...\n")
result = subprocess.run(cmd)

if result.returncode == 0:
    print("\n✅ Compilacion exitosa!")
    print("El .exe esta en: dist\\TallerPro.exe")
else:
    print("\n❌ Error en compilacion")
