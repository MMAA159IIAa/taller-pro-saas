import os
import subprocess
import shutil

# Este script se encarga de empaquetar TallerPro.py en un ejecutable .exe limpio.

print("Preparando Compilacion de TallerPro...")

# Asegurar dependencias de empaquetado
subprocess.run(["pip", "install", "pyinstaller"], check=True)

# Limpiar compilaciones previas para evitar basura
if os.path.exists("build"): 
    try: shutil.rmtree("build")
    except: pass
if os.path.exists("dist"): 
    try: shutil.rmtree("dist")
    except: pass

comando_pyinstaller = [
    "pyinstaller",
    "--noconfirm",
    "--onedir",
    "--windowed",
    "--name=TallerPro",
    "--distpath=./dist",
    "--workpath=./build",
    "--add-data=agentes;agentes",
    "--add-data=servicios;servicios",
    "--add-data=utils;utils",
    "--collect-all=watchdog",
    "--collect-all=tkcalendar",
    "--collect-all=babel",
    "--collect-submodules=agentes",
    "--collect-submodules=servicios",
    "--collect-submodules=utils",
    # "--icon=icono.ico",
    "main.py"
]

print("Compilando con PyInstaller... (Esto tomara 1 o 2 minutos)")
try:
    subprocess.run(comando_pyinstaller, check=True)
    print("\n" + "="*50)
    print("COMPILACION EXITOSA (AGENTIC v1)")
    print("="*50)
    print("El programa se guardo en la carpeta maestra:")
    print("📂 Carpeta: dist/TallerPro/")
    print("🚀 Archivo: TallerPro.exe")
    print("="*50)
    print("\nSiguiente Paso: Abre 'Instalador_TallerPro.iss' con Inno Setup.")
except Exception as e:
    print(f"\nERROR CRITICO EN COMPILACION: {e}")
    print("Asegurate de cerrar cualquier ventana del programa o carpetas antes de compilar.")

