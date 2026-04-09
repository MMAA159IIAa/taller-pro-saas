import os
import shutil
import time

folders = ['build', 'dist']
for folder in folders:
    if os.path.exists(folder):
        print(f"Intentando borrar {folder}...")
        for i in range(5):
            try:
                shutil.rmtree(folder)
                print(f"{folder} borrada con éxito.")
                break
            except Exception as e:
                print(f"Error borrando {folder} (intento {i+1}): {e}")
                time.sleep(2)

print("\nCleanup finalizado.")
