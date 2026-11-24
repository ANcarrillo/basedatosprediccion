"""Carga a desercion_db un Excel con el formato de docs/estudiantes_actuales.xlsx
(hojas: Estudiantes, Datos académicos, Datos socioeconómicos).

- Solo AGREGA: los estudiantes (por código) y los registros (estudiante + periodo)
  que ya existen se dejan como están.
- Todo se hace en una sola transacción: si algo falla, no se guarda nada.
- Los programas y periodos deben existir antes (hoja Catálogos / pantalla Catálogos).

Uso (desde Trabajofinal):
  ml\\.venv\\Scripts\\python database\\importar_excel.py "ruta\\al\\archivo.xlsx"
"""
import sys
from pathlib import Path

import pandas as pd
from dotenv import dotenv_values
from sqlalchemy import create_engine, text

RAIZ = Path(__file__).resolve().parents[1]
SI = {"si", "sí", "s", "true", "1", "x"}


def limpiar(df: pd.DataFrame) -> pd.DataFrame:
    df = df.dropna(how="all").copy()
    df.columns = [c.strip().lower() for c in df.columns]
    for c in df.columns:
        df[c] = df[c].map(lambda v: v.strip() if isinstance(v, str) else v)
    df = df.astype(object)
    return df.where(df.notna() & (df != ""), None)   # celdas vacías -> None (NULL)


def num(v, entero=False):
    if v is None:
        return None
    v = float(str(v).replace(",", "."))
    return int(round(v)) if entero else v


def sino(v):
    return v is not None and str(v).lower() in SI


def fecha(v):
    return None if v is None else pd.to_datetime(v).date()


def main(ruta: str):
    hojas = pd.read_excel(ruta, sheet_name=None, dtype=str)
    est = limpiar(hojas["Estudiantes"])
    aca = limpiar(hojas["Datos académicos"])
    soc = limpiar(hojas["Datos socioeconómicos"])

    motor = create_engine(dotenv_values(RAIZ / "ml" / ".env")["DATABASE_URL"])
    with motor.begin() as con:
        programas = dict(con.execute(text("SELECT codigo, id FROM programas")).all())
        periodos = dict(con.execute(text("SELECT codigo, id FROM periodos_academicos")).all())
        faltan = (set(est.programa) - set(programas)) | ((set(est.periodo_ingreso.dropna()) |
                  set(aca.periodo) | set(soc.periodo)) - set(periodos))
        if faltan:
            raise SystemExit(f"Cree primero estos programas/periodos: {sorted(faltan)}")

        filas = [{
            "codigo": r.codigo, "tipo_documento": r.tipo_documento or "CC", "numero_documento": r.numero_documento,
            "nombres": r.nombres, "apellidos": r.apellidos, "fecha_nacimiento": fecha(r.fecha_nacimiento),
            "genero": r.genero, "email": r.email, "telefono": r.telefono, "programa_id": programas[r.programa],
            "periodo_ingreso_id": periodos.get(r.periodo_ingreso), "semestre_actual": num(r.semestre_actual, True) or 1,
            "puntaje_saber11": num(r.puntaje_saber11, True), "tipo_colegio": r.tipo_colegio, "estado": r.estado or "activo",
        } for r in est.itertuples(index=False)]
        n_est = con.execute(text("""
            INSERT INTO estudiantes (codigo, tipo_documento, numero_documento, nombres, apellidos, fecha_nacimiento,
                genero, email, telefono, programa_id, periodo_ingreso_id, semestre_actual, puntaje_saber11,
                tipo_colegio, estado)
            VALUES (:codigo, :tipo_documento, :numero_documento, :nombres, :apellidos, :fecha_nacimiento, :genero,
                :email, :telefono, :programa_id, :periodo_ingreso_id, :semestre_actual, :puntaje_saber11,
                :tipo_colegio, :estado)
            ON CONFLICT (codigo) DO NOTHING"""), filas).rowcount

        ids = dict(con.execute(text("SELECT codigo, id FROM estudiantes")).all())
        sin_estudiante = (set(aca.codigo_estudiante) | set(soc.codigo_estudiante)) - set(ids)
        if sin_estudiante:
            raise SystemExit(f"Hay datos de estudiantes que no existen: {sorted(sin_estudiante)[:10]}")

        filas = [{
            "estudiante_id": ids[r.codigo_estudiante], "periodo_id": periodos[r.periodo],
            "semestre_cursado": num(r.semestre_cursado, True), "creditos_inscritos": num(r.creditos_inscritos, True) or 0,
            "creditos_aprobados": num(r.creditos_aprobados, True) or 0,
            "creditos_reprobados": num(r.creditos_reprobados, True) or 0,
            "promedio_periodo": num(r.promedio_periodo), "promedio_acumulado": num(r.promedio_acumulado),
            "asistencia_pct": num(r.asistencia_pct), "materias_reprobadas": num(r.materias_reprobadas, True) or 0,
            "materias_canceladas": num(r.materias_canceladas, True) or 0,
            "materias_repetidas": num(r.materias_repetidas, True) or 0,
            "estado_matricula": r.estado_matricula or "matriculado",
        } for r in aca.itertuples(index=False)]
        n_aca = con.execute(text("""
            INSERT INTO datos_academicos (estudiante_id, periodo_id, semestre_cursado, creditos_inscritos,
                creditos_aprobados, creditos_reprobados, promedio_periodo, promedio_acumulado, asistencia_pct,
                materias_reprobadas, materias_canceladas, materias_repetidas, estado_matricula)
            VALUES (:estudiante_id, :periodo_id, :semestre_cursado, :creditos_inscritos, :creditos_aprobados,
                :creditos_reprobados, :promedio_periodo, :promedio_acumulado, :asistencia_pct, :materias_reprobadas,
                :materias_canceladas, :materias_repetidas, :estado_matricula)
            ON CONFLICT (estudiante_id, periodo_id) DO NOTHING"""), filas).rowcount

        filas = [{
            "estudiante_id": ids[r.codigo_estudiante], "periodo_id": periodos[r.periodo],
            "estrato": num(r.estrato, True), "ingreso_familiar": num(r.ingreso_familiar), "trabaja": sino(r.trabaja),
            "horas_trabajo_semana": (num(r.horas_trabajo_semana, True) or 0) if sino(r.trabaja) else 0,
            "personas_a_cargo": num(r.personas_a_cargo, True) or 0, "tipo_vivienda": r.tipo_vivienda,
            "zona_residencia": r.zona_residencia, "distancia_km": num(r.distancia_km), "tiene_beca": sino(r.tiene_beca),
            "apoyo_financiero": sino(r.apoyo_financiero), "nivel_educativo_padres": r.nivel_educativo_padres,
            "victima_conflicto": sino(r.victima_conflicto), "pertenece_etnia": sino(r.pertenece_etnia),
            "discapacidad": sino(r.discapacidad),
        } for r in soc.itertuples(index=False)]
        n_soc = con.execute(text("""
            INSERT INTO datos_socioeconomicos (estudiante_id, periodo_id, estrato, ingreso_familiar, trabaja,
                horas_trabajo_semana, personas_a_cargo, tipo_vivienda, zona_residencia, distancia_km, tiene_beca,
                apoyo_financiero, nivel_educativo_padres, victima_conflicto, pertenece_etnia, discapacidad)
            VALUES (:estudiante_id, :periodo_id, :estrato, :ingreso_familiar, :trabaja, :horas_trabajo_semana,
                :personas_a_cargo, :tipo_vivienda, :zona_residencia, :distancia_km, :tiene_beca, :apoyo_financiero,
                :nivel_educativo_padres, :victima_conflicto, :pertenece_etnia, :discapacidad)
            ON CONFLICT (estudiante_id, periodo_id) DO NOTHING"""), filas).rowcount

    print(f"Estudiantes nuevos: {n_est} de {len(est)} (los demás ya existían)")
    print(f"Datos académicos nuevos: {n_aca} de {len(aca)}")
    print(f"Datos socioeconómicos nuevos: {n_soc} de {len(soc)}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    main(sys.argv[1])
