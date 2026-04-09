import openpyxl
import os

ruta = r"c:\Users\leech\OneDrive\Documentos\RELACION DE CARROS 2026.xlsx"
wb = openpyxl.load_workbook(ruta, read_only=True, data_only=True)
ws = wb['RELACION DE CARROS']

print("Filas 335 a 345 de RELACION DE CARROS:")
for i, row in enumerate(ws.iter_rows(min_row=335, max_row=345, values_only=True)):
    print(f"Fila {i+335}: {row}")
