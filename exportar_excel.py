"""Exporta los estudiantes actuales de desercion_db a un Excel de referencia.

Uso (desde Trabajofinal):  ml\\.venv\\Scripts\\python database\\exportar_excel.py
Requiere openpyxl (pip install openpyxl) y el archivo ml\\.env con DATABASE_URL.
"""
from pathlib import Path

import pandas as pd
from dotenv import dotenv_values
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from sqlalchemy import create_engine

RAIZ = Path(__file__).resolve().parents[1]
SALIDA = RAIZ / "docs" / "estudiantes_actuales.xlsx"
url = dotenv_values(RAIZ / "ml" / ".env")["DATABASE_URL"]
motor = create_engine(url)

CONSULTAS = {
    "Estudiantes": """
        SELECT e.codigo, e.tipo_documento, e.numero_documento, e.nombres, e.apellidos, e.fecha_nacimiento,
               e.genero, e.email, e.telefono, p.codigo AS programa, pi.codigo AS periodo_ingreso,
               e.semestre_actual, e.puntaje_saber11, e.tipo_colegio, e.estado
        FROM estudiantes e JOIN programas p ON p.id = e.programa_id
        LEFT JOIN periodos_academicos pi ON pi.id = e.periodo_ingreso_id
        ORDER BY e.codigo""",
    "Datos académicos": """
        SELECT e.codigo AS codigo_estudiante, pe.codigo AS periodo, d.semestre_cursado, d.creditos_inscritos,
               d.creditos_aprobados, d.creditos_reprobados, d.promedio_periodo, d.promedio_acumulado,
               d.asistencia_pct, d.materias_reprobadas, d.materias_canceladas, d.materias_repetidas,
               d.estado_matricula
        FROM datos_academicos d JOIN estudiantes e ON e.id = d.estudiante_id
        JOIN periodos_academicos pe ON pe.id = d.periodo_id
        ORDER BY e.codigo, pe.fecha_inicio""",
    "Datos socioeconómicos": """
        SELECT e.codigo AS codigo_estudiante, pe.codigo AS periodo, s.estrato, s.ingreso_familiar, s.trabaja,
               s.horas_trabajo_semana, s.personas_a_cargo, s.tipo_vivienda, s.zona_residencia, s.distancia_km,
               s.tiene_beca, s.apoyo_financiero, s.nivel_educativo_padres, s.victima_conflicto,
               s.pertenece_etnia, s.discapacidad
        FROM datos_socioeconomicos s JOIN estudiantes e ON e.id = s.estudiante_id
        JOIN periodos_academicos pe ON pe.id = s.periodo_id
        ORDER BY e.codigo, pe.fecha_inicio""",
}

# Valores permitidos por columna (listas desplegables y hoja "Valores permitidos")
LISTAS = {
    "tipo_documento": ["CC", "TI", "CE", "PA", "PPT"],
    "genero": ["masculino", "femenino", "otro"],
    "tipo_colegio": ["publico", "privado"],
    "estado": ["activo", "desertor", "graduado", "retirado", "inactivo"],
    "estado_matricula": ["matriculado", "cancelado", "aplazado", "no_matriculado"],
    "tipo_vivienda": ["propia", "arriendo", "familiar", "residencia", "otra"],
    "zona_residencia": ["urbana", "rural"],
    "nivel_educativo_padres": ["ninguno", "primaria", "secundaria", "tecnico", "universitario", "posgrado"],
    "trabaja": ["si", "no"], "tiene_beca": ["si", "no"], "apoyo_financiero": ["si", "no"],
    "victima_conflicto": ["si", "no"], "pertenece_etnia": ["si", "no"], "discapacidad": ["si", "no"],
}
RANGOS = {  # columna: (descripción, mínimo, máximo)
    "semestre_actual": ("Entero de 1 a 14", 1, 14), "semestre_cursado": ("Entero de 1 a 14", 1, 14),
    "puntaje_saber11": ("Entero de 0 a 500", 0, 500), "estrato": ("Entero de 0 a 6", 0, 6),
    "promedio_periodo": ("Decimal de 0.0 a 5.0", 0, 5), "promedio_acumulado": ("Decimal de 0.0 a 5.0", 0, 5),
    "asistencia_pct": ("Porcentaje de 0 a 100", 0, 100), "horas_trabajo_semana": ("Entero de 0 a 80", 0, 80),
}
OBLIGATORIAS = {"codigo", "numero_documento", "nombres", "apellidos", "programa", "codigo_estudiante",
                "periodo", "semestre_cursado"}

FUENTE = "Arial"
ENC_FILL = PatternFill("solid", fgColor="1E3A8A")
OBL_FILL = PatternFill("solid", fgColor="B91C1C")
BORDE = Border(bottom=Side(style="thin", color="D1D5DB"))


def formato_hoja(ws, df: pd.DataFrame, filas_extra: int = 200):
    for j, col in enumerate(df.columns, start=1):
        c = ws.cell(row=1, column=j, value=col)
        c.font = Font(name=FUENTE, bold=True, color="FFFFFF")
        c.fill = OBL_FILL if col in OBLIGATORIAS else ENC_FILL
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    for i, fila in enumerate(df.itertuples(index=False), start=2):
        for j, v in enumerate(fila, start=1):
            if isinstance(v, bool):
                v = "si" if v else "no"
            elif pd.isna(v):
                v = None
            c = ws.cell(row=i, column=j, value=v)
            c.font = Font(name=FUENTE)
            c.border = BORDE
    ultima = len(df) + 1 + filas_extra
    for j, col in enumerate(df.columns, start=1):
        letra = get_column_letter(j)
        ancho = max(len(col), *(len(str(x)) for x in df[col].head(200) if x is not None)) if len(df) else len(col)
        ws.column_dimensions[letra].width = min(max(ancho + 2, 10), 40)
        rango = f"{letra}2:{letra}{ultima}"
        if col in LISTAS:
            dv = DataValidation(type="list", formula1='"' + ",".join(LISTAS[col]) + '"', allow_blank=True,
                                error=f"Use uno de: {', '.join(LISTAS[col])}", showErrorMessage=True)
            dv.add(rango)
            ws.add_data_validation(dv)
        elif col in RANGOS:
            _, mn, mx = RANGOS[col]
            dv = DataValidation(type="decimal", operator="between", formula1=str(mn), formula2=str(mx),
                                allow_blank=True, showErrorMessage=True, error=f"Valor entre {mn} y {mx}")
            dv.add(rango)
            ws.add_data_validation(dv)
        if col == "fecha_nacimiento":
            for i in range(2, ultima + 1):
                ws.cell(row=i, column=j).number_format = "yyyy-mm-dd"
        if col == "ingreso_familiar":
            for i in range(2, ultima + 1):
                ws.cell(row=i, column=j).number_format = "#,##0"
    ws.freeze_panes = "B2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(df.columns))}{len(df) + 1}"
    ws.row_dimensions[1].height = 30


def hoja_guia(wb, resumen: dict):
    ws = wb.create_sheet("Guía", 0)
    ws.column_dimensions["A"].width = 30
    ws.column_dimensions["B"].width = 95
    lineas = [
        ("Estudiantes actuales de desercion_db", None),
        ("Datos FICTICIOS de prueba, exportados de la base para usar como guía al agregar estudiantes reales.", None),
        ("", None),
        ("Hoja", "Contenido"),
        ("Estudiantes", f"{resumen['Estudiantes']} estudiantes. Un registro por estudiante."),
        ("Datos académicos", f"{resumen['Datos académicos']} registros. Uno por estudiante y periodo."),
        ("Datos socioeconómicos", f"{resumen['Datos socioeconómicos']} registros. Uno por estudiante y periodo."),
        ("Catálogos", "Programas y periodos que ya existen. Use estos códigos en las demás hojas."),
        ("Valores permitidos", "Lista de valores válidos y rangos de cada columna."),
        ("", None),
        ("Leyenda", None),
        ("Encabezado rojo", "Columna obligatoria."),
        ("Encabezado azul", "Columna opcional (pero entre más completa, mejor predice el modelo)."),
        ("Celdas con lista", "Las columnas de categorías tienen lista desplegable; los números, validación de rango."),
        ("", None),
        ("Cómo agregar estudiantes nuevos", None),
        ("1.", "Escriba las filas nuevas debajo de las existentes, siguiendo el mismo formato."),
        ("2.", "Cree primero el estudiante (web: Estudiantes → + Nuevo estudiante, o SQL)."),
        ("3.", "Las hojas Datos académicos y Datos socioeconómicos tienen el formato de la pantalla "
               "Carga de datos: guárdelas como CSV (Archivo → Guardar como → CSV UTF-8) e impórtelas."),
        ("4.", "Créditos aprobados + reprobados no pueden superar los inscritos. Decimales con punto o coma."),
        ("5.", "Estado 'desertor' es lo que el modelo aprende a predecir: márquelo solo en quienes sí desertaron."),
    ]
    for i, (a, b) in enumerate(lineas, start=1):
        ca, cb = ws.cell(row=i, column=1, value=a), ws.cell(row=i, column=2, value=b)
        for c in (ca, cb):
            c.font = Font(name=FUENTE)
            c.alignment = Alignment(wrap_text=True, vertical="top")
    ws["A1"].font = Font(name=FUENTE, bold=True, size=14, color="1E3A8A")
    ws["A2"].font = Font(name=FUENTE, italic=True, color="B91C1C")
    for r in (4, 11, 16):
        ws.cell(row=r, column=1).font = Font(name=FUENTE, bold=True)
        ws.cell(row=r, column=2).font = Font(name=FUENTE, bold=True)
    ws["A12"].fill = OBL_FILL
    ws["A12"].font = Font(name=FUENTE, bold=True, color="FFFFFF")
    ws["A13"].fill = ENC_FILL
    ws["A13"].font = Font(name=FUENTE, bold=True, color="FFFFFF")


def hoja_valores(wb):
    ws = wb.create_sheet("Valores permitidos")
    filas = [("Columna", "Valores permitidos")]
    filas += [(k, ", ".join(v)) for k, v in LISTAS.items()]
    filas += [(k, d) for k, (d, _, _) in RANGOS.items()]
    filas += [("fecha_nacimiento", "Fecha AAAA-MM-DD"), ("ingreso_familiar", "Pesos mensuales, sin puntos"),
              ("distancia_km", "Kilómetros a la sede, decimal"),
              ("creditos_inscritos / aprobados / reprobados", "Enteros ≥ 0; aprobados + reprobados ≤ inscritos"),
              ("materias_reprobadas / canceladas / repetidas", "Enteros ≥ 0"),
              ("programa", "Código de la hoja Catálogos (ej. ISIS)"),
              ("periodo / periodo_ingreso", "Código de la hoja Catálogos (ej. 2026-1)")]
    for i, (a, b) in enumerate(filas, start=1):
        for j, v in enumerate((a, b), start=1):
            c = ws.cell(row=i, column=j, value=v)
            c.font = Font(name=FUENTE, bold=(i == 1), color="FFFFFF" if i == 1 else "000000")
            if i == 1:
                c.fill = ENC_FILL
    ws.column_dimensions["A"].width = 44
    ws.column_dimensions["B"].width = 70


def main():
    with motor.connect() as con:
        datos = {nombre: pd.read_sql(sql, con) for nombre, sql in CONSULTAS.items()}
        programas = pd.read_sql("SELECT p.codigo, p.nombre, f.nombre AS facultad, p.nivel FROM programas p "
                                "JOIN facultades f ON f.id = p.facultad_id ORDER BY p.codigo", con)
        periodos = pd.read_sql("SELECT codigo, fecha_inicio, fecha_fin, actual FROM periodos_academicos "
                               "ORDER BY fecha_inicio", con)
    wb = Workbook()
    wb.remove(wb.active)
    for nombre, df in datos.items():
        formato_hoja(wb.create_sheet(nombre), df)

    ws = wb.create_sheet("Catálogos")
    formato_hoja(ws, programas, filas_extra=0)
    inicio = len(programas) + 4
    for j, col in enumerate(periodos.columns, start=1):
        c = ws.cell(row=inicio, column=j, value=col)
        c.font = Font(name=FUENTE, bold=True, color="FFFFFF")
        c.fill = ENC_FILL
    for i, fila in enumerate(periodos.itertuples(index=False), start=inicio + 1):
        for j, v in enumerate(fila, start=1):
            if isinstance(v, bool):
                v = "si" if v else "no"
            c = ws.cell(row=i, column=j, value=v)
            c.font = Font(name=FUENTE)
            if j in (2, 3):
                c.number_format = "yyyy-mm-dd"
    ws.auto_filter.ref = None
    ws.column_dimensions["B"].width = 30
    ws.column_dimensions["C"].width = 32

    hoja_valores(wb)
    hoja_guia(wb, {k: len(v) for k, v in datos.items()})
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    wb.save(SALIDA)
    print(f"Excel guardado en {SALIDA}")
    for k, v in datos.items():
        print(f"  {k}: {len(v)} filas")


if __name__ == "__main__":
    main()
