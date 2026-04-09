import openpyxl
import os

ruta = r"c:\Users\leech\OneDrive\Documentos\RELACION DE CARROS 2026.xlsx"
wb = openpyxl.load_workbook(ruta, read_only=True, data_only=True)
ws = wb['RELACION DE CARROS']

print("Filas sin folio numérico en RELACION DE CARROS:")
count = 0
for i, row in enumerate(ws.iter_rows(values_only=True)):
    if i == 0: continue # header
    if not row[0] or not isinstance(row[0], (int, float)):
        if any(row):
            print(f"Fila {i+1}: {row}")
            count += 1
    if count > 20: break

print("\nFilas totales revisadas de este tipo:", count)
