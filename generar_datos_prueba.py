"""Genera los scripts SQL de datos de PRUEBA (ficticios):

  roles_y_usuarios.sql   -> los 4 roles + un usuario por rol para iniciar sesión
  datos_prueba.sql       -> facultades, programas, periodos y 100 estudiantes con
                            datos académicos y socioeconómicos

Uso (desde la carpeta Trabajofinal, con el entorno del backend que trae bcrypt):
  backend\\.venv\\Scripts\\python database\\generar_datos_prueba.py
"""
from __future__ import annotations

import math
import random
from pathlib import Path

import bcrypt

CARPETA = Path(__file__).resolve().parent
CLAVE_PRUEBA = "Desercion2026"   # contraseña de los usuarios de prueba (cámbiela después)
N_ESTUDIANTES = 100
r = random.Random(2026)

USUARIOS = [
    ("Ana", "Administradora", "admin@universidad.edu.co", "administrador"),
    ("Carlos", "Coordinador", "coordinador@universidad.edu.co", "coordinador"),
    ("Diana", "Docente", "docente@universidad.edu.co", "docente"),
    ("Beatriz", "Bienestar", "bienestar@universidad.edu.co", "bienestar"),
]

FACULTADES = ["Facultad de Ingeniería", "Facultad de Ciencias Económicas"]
PROGRAMAS = [  # (codigo, nombre, facultad)
    ("ISIS", "Ingeniería de Sistemas", 0),
    ("ICIV", "Ingeniería Civil", 0),
    ("ADEM", "Administración de Empresas", 1),
    ("CPUB", "Contaduría Pública", 1),
]
PERIODOS = [("2025-1", "2025-02-03", "2025-06-20", False),
            ("2025-2", "2025-08-04", "2025-12-12", False),
            ("2026-1", "2026-02-02", "2026-06-19", True)]

NOMBRES_F = ["María", "Laura", "Valentina", "Daniela", "Sofía", "Camila", "Paula", "Juliana", "Natalia", "Andrea",
             "Carolina", "Manuela", "Isabella", "Mariana", "Luisa", "Sara", "Diana", "Angie", "Yuliana", "Karen"]
NOMBRES_M = ["Juan", "Andrés", "Santiago", "Sebastián", "Daniel", "Felipe", "Camilo", "David", "Alejandro", "Diego",
             "Mateo", "Nicolás", "Julián", "Esteban", "Cristian", "Jorge", "Luis", "Miguel", "Óscar", "Brayan"]
APELLIDOS = ["García", "Rodríguez", "Martínez", "López", "González", "Pérez", "Sánchez", "Ramírez", "Torres", "Díaz",
             "Vargas", "Rojas", "Moreno", "Castro", "Ortiz", "Gómez", "Herrera", "Medina", "Cardona", "Ospina",
             "Muñoz", "Restrepo", "Quintero", "Jiménez", "Silva", "Ríos", "Mejía", "Parra", "Suárez", "Valencia"]


def q(v) -> str:
    """Valor -> literal SQL."""
    if v is None:
        return "NULL"
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    if isinstance(v, (int, float)):
        return str(v)
    return "'" + str(v).replace("'", "''") + "'"


def fila(*vals) -> str:
    return "(" + ", ".join(q(v) for v in vals) + ")"


def roles_y_usuarios() -> str:
    lineas = [
        "-- Roles base y un usuario de PRUEBA por rol",
        f"-- Contraseña de todos los usuarios de prueba: {CLAVE_PRUEBA}  (cámbiela en la pantalla Usuarios)",
        "-- Ejecutar: psql -U postgres -d desercion_db -f roles_y_usuarios.sql",
        "BEGIN;",
        "INSERT INTO roles (nombre, descripcion) VALUES",
        "    ('administrador', 'Gestiona usuarios, catálogos y el modelo de ML'),",
        "    ('coordinador',   'Coordinador de programa: consulta estudiantes, reportes y gestiona alertas'),",
        "    ('docente',       'Docente / consejero: consulta estudiantes asignados y registra intervenciones'),",
        "    ('bienestar',     'Bienestar Universitario: atiende alertas y registra intervenciones')",
        "ON CONFLICT (nombre) DO NOTHING;",
        "",
        "INSERT INTO usuarios (nombres, apellidos, email, password_hash, rol_id)",
        "SELECT v.nombres, v.apellidos, v.email, v.hash, r.id FROM (VALUES",
    ]
    valores = []
    for nombres, apellidos, email, rol in USUARIOS:
        h = bcrypt.hashpw(CLAVE_PRUEBA.encode(), bcrypt.gensalt()).decode()
        valores.append("    " + fila(nombres, apellidos, email, h, rol))
    lineas.append(",\n".join(valores))
    lineas += [") AS v(nombres, apellidos, email, hash, rol)",
               "JOIN roles r ON r.nombre = v.rol",
               "ON CONFLICT (email) DO NOTHING;",
               "COMMIT;", ""]
    return "\n".join(lineas)


def estudiante(i: int):
    """Genera un estudiante con perfil coherente y decide si desertó."""
    genero = r.choice(["femenino", "masculino"])
    nombre = r.choice(NOMBRES_F if genero == "femenino" else NOMBRES_M)
    if r.random() < 0.35:
        nombre += " " + r.choice(NOMBRES_F if genero == "femenino" else NOMBRES_M)
    apellidos = f"{r.choice(APELLIDOS)} {r.choice(APELLIDOS)}"
    programa = PROGRAMAS[i % len(PROGRAMAS)][0]
    semestre = r.randint(1, 9)
    edad = 16 + semestre // 2 + r.choice([0, 0, 1, 1, 2, 3, 6, 10])
    estrato = r.choices([1, 2, 3, 4, 5], [30, 35, 20, 10, 5])[0]
    trabaja = r.random() < 0.35
    horas = r.randint(10, 48) if trabaja else 0
    beca = r.random() < 0.15
    apoyo = r.random() < 0.2
    distancia = round(r.gammavariate(2, 6), 1)
    zona = "rural" if r.random() < 0.25 else "urbana"
    prom_acum = min(5.0, max(1.5, r.gauss(3.6, 0.45)))
    prom_per = min(5.0, max(0.8, prom_acum + r.gauss(0, 0.35)))
    asistencia = min(100.0, max(35.0, r.gauss(86, 9)))
    reprob = int(min(6, max(0, round((3.6 - prom_per) * 1.8 + r.gauss(0, 0.7)))))

    # Probabilidad de deserción según el perfil (relación inventada, solo para pruebas)
    z = (-1.3 - 1.7 * (prom_per - 3.3) - 0.05 * (asistencia - 86) + 0.35 * reprob
         + 0.03 * horas - 0.25 * (estrato - 2) - 0.8 * beca + 0.02 * distancia + r.gauss(0, 0.5))
    desertor = r.random() < 1 / (1 + math.exp(-z))

    est = {
        "codigo": f"2025{i:04d}", "tipo_documento": "CC" if edad >= 18 else "TI",
        "numero_documento": str(1_000_000_000 + r.randint(0, 99_999_999)),
        "nombres": nombre, "apellidos": apellidos,
        "fecha_nacimiento": f"{2026 - edad}-{r.randint(1, 12):02d}-{r.randint(1, 28):02d}",
        "genero": genero,
        "email": f"{nombre.split()[0].lower()}.{apellidos.split()[0].lower()}{i}@estudiantes.universidad.edu.co"
                 .translate(str.maketrans("áéíóúñÁÉÍÓÚÑ", "aeiounAEIOUN")),
        "telefono": f"3{r.randint(100000000, 299999999)}",
        "programa": programa, "periodo_ingreso": "2025-1", "semestre_actual": semestre,
        "puntaje_saber11": int(min(450, max(150, r.gauss(265, 40)))) if r.random() > 0.05 else None,
        "tipo_colegio": "publico" if r.random() < 0.7 else "privado",
        "estado": "desertor" if desertor else "activo",
    }
    socio = {
        "periodo": "2025-2", "estrato": estrato,
        "ingreso_familiar": round(estrato * 900_000 * r.uniform(0.6, 1.4), -3) if r.random() > 0.05 else None,
        "trabaja": trabaja, "horas_trabajo_semana": horas, "personas_a_cargo": min(4, int(r.expovariate(2.5))),
        "tipo_vivienda": r.choice(["propia", "arriendo", "familiar"]), "zona_residencia": zona,
        "distancia_km": distancia, "tiene_beca": beca, "apoyo_financiero": apoyo,
        "nivel_educativo_padres": r.choice(["primaria", "secundaria", "secundaria", "tecnico", "universitario"]),
        "victima_conflicto": r.random() < 0.08, "pertenece_etnia": r.random() < 0.06, "discapacidad": r.random() < 0.03,
    }

    academicos = []
    # Periodo anterior (2025-2): un poco mejor que el actual
    for periodo, delta, sem in (("2025-2", 0.15, max(1, semestre - 1)), ("2026-1", 0.0, semestre)):
        if periodo == "2025-2" and semestre == 1:
            continue
        p = round(min(5.0, max(0.5, prom_per + delta + r.gauss(0, 0.15))), 2)
        rep = max(0, reprob - (1 if delta and reprob else 0))
        ins = r.randint(12, 20)
        cred_rep = min(ins, rep * 3)
        academicos.append({
            "periodo": periodo, "semestre_cursado": sem, "creditos_inscritos": ins,
            "creditos_aprobados": ins - cred_rep, "creditos_reprobados": cred_rep,
            "promedio_periodo": p, "promedio_acumulado": round(prom_acum, 2),
            "asistencia_pct": round(min(100, asistencia + (3 if delta else 0)), 2),
            "materias_reprobadas": rep, "materias_canceladas": int(r.random() < 0.2),
            "materias_repetidas": int(r.random() < 0.25) + (1 if rep >= 3 else 0),
            "estado_matricula": "cancelado" if desertor and periodo == "2026-1" and r.random() < 0.4 else "matriculado",
        })
    return est, socio, academicos


def datos_prueba() -> str:
    ests, socios, acads = [], [], []
    for i in range(1, N_ESTUDIANTES + 1):
        e, s, a = estudiante(i)
        ests.append(e)
        socios.append({"codigo": e["codigo"], **s})
        acads += [{"codigo": e["codigo"], **x} for x in a]
    n_des = sum(e["estado"] == "desertor" for e in ests)

    L = ["-- DATOS DE PRUEBA (FICTICIOS) - no corresponden a personas reales",
         f"-- {N_ESTUDIANTES} estudiantes ({n_des} desertores), 2 facultades, 4 programas, 3 periodos",
         "-- Ejecutar después de schema.sql:  psql -U postgres -d desercion_db -f datos_prueba.sql",
         "BEGIN;", ""]
    L.append("INSERT INTO facultades (nombre) VALUES\n" + ",\n".join(f"    ({q(f)})" for f in FACULTADES)
             + "\nON CONFLICT (nombre) DO NOTHING;\n")
    L.append("INSERT INTO programas (facultad_id, codigo, nombre)\nSELECT f.id, v.codigo, v.nombre FROM (VALUES\n"
             + ",\n".join("    " + fila(c, n, FACULTADES[fi]) for c, n, fi in PROGRAMAS)
             + "\n) AS v(codigo, nombre, facultad) JOIN facultades f ON f.nombre = v.facultad\n"
               "ON CONFLICT (codigo) DO NOTHING;\n")
    L.append("INSERT INTO periodos_academicos (codigo, fecha_inicio, fecha_fin, actual) VALUES\n"
             + ",\n".join(f"    ({q(c)}, DATE {q(a)}, DATE {q(b)}, {q(act)})" for c, a, b, act in PERIODOS)
             + "\nON CONFLICT (codigo) DO NOTHING;\n")

    cols = ["codigo", "tipo_documento", "numero_documento", "nombres", "apellidos", "fecha_nacimiento", "genero",
            "email", "telefono", "programa", "periodo_ingreso", "semestre_actual", "puntaje_saber11",
            "tipo_colegio", "estado"]
    L.append("INSERT INTO estudiantes (codigo, tipo_documento, numero_documento, nombres, apellidos, fecha_nacimiento,\n"
             "    genero, email, telefono, programa_id, periodo_ingreso_id, semestre_actual, puntaje_saber11, tipo_colegio, estado)\n"
             "SELECT v.codigo, v.tipo_documento, v.numero_documento, v.nombres, v.apellidos, v.fecha_nacimiento::DATE,\n"
             "    v.genero, v.email, v.telefono, pr.id, pe.id, v.semestre_actual::SMALLINT, v.puntaje_saber11::SMALLINT,\n"
             "    v.tipo_colegio, v.estado\nFROM (VALUES\n"
             + ",\n".join("    " + fila(*[e[c] for c in cols]) for e in ests)
             + f"\n) AS v({', '.join(cols)})\n"
               "JOIN programas pr ON pr.codigo = v.programa\n"
               "JOIN periodos_academicos pe ON pe.codigo = v.periodo_ingreso\n"
               "ON CONFLICT DO NOTHING;\n")

    scols = ["codigo", "periodo", "estrato", "ingreso_familiar", "trabaja", "horas_trabajo_semana", "personas_a_cargo",
             "tipo_vivienda", "zona_residencia", "distancia_km", "tiene_beca", "apoyo_financiero",
             "nivel_educativo_padres", "victima_conflicto", "pertenece_etnia", "discapacidad"]
    L.append("INSERT INTO datos_socioeconomicos (estudiante_id, periodo_id, estrato, ingreso_familiar, trabaja,\n"
             "    horas_trabajo_semana, personas_a_cargo, tipo_vivienda, zona_residencia, distancia_km, tiene_beca,\n"
             "    apoyo_financiero, nivel_educativo_padres, victima_conflicto, pertenece_etnia, discapacidad)\n"
             "SELECT e.id, p.id, v.estrato::SMALLINT, v.ingreso_familiar::NUMERIC, v.trabaja, v.horas_trabajo_semana::SMALLINT,\n"
             "    v.personas_a_cargo::SMALLINT, v.tipo_vivienda, v.zona_residencia, v.distancia_km::NUMERIC, v.tiene_beca,\n"
             "    v.apoyo_financiero, v.nivel_educativo_padres, v.victima_conflicto, v.pertenece_etnia, v.discapacidad\n"
             "FROM (VALUES\n"
             + ",\n".join("    " + fila(*[s[c] for c in scols]) for s in socios)
             + f"\n) AS v({', '.join(scols)})\n"
               "JOIN estudiantes e ON e.codigo = v.codigo\nJOIN periodos_academicos p ON p.codigo = v.periodo\n"
               "ON CONFLICT (estudiante_id, periodo_id) DO NOTHING;\n")

    acols = ["codigo", "periodo", "semestre_cursado", "creditos_inscritos", "creditos_aprobados", "creditos_reprobados",
             "promedio_periodo", "promedio_acumulado", "asistencia_pct", "materias_reprobadas", "materias_canceladas",
             "materias_repetidas", "estado_matricula"]
    L.append("INSERT INTO datos_academicos (estudiante_id, periodo_id, semestre_cursado, creditos_inscritos,\n"
             "    creditos_aprobados, creditos_reprobados, promedio_periodo, promedio_acumulado, asistencia_pct,\n"
             "    materias_reprobadas, materias_canceladas, materias_repetidas, estado_matricula)\n"
             "SELECT e.id, p.id, v.semestre_cursado::SMALLINT, v.creditos_inscritos::SMALLINT, v.creditos_aprobados::SMALLINT,\n"
             "    v.creditos_reprobados::SMALLINT, v.promedio_periodo::NUMERIC, v.promedio_acumulado::NUMERIC,\n"
             "    v.asistencia_pct::NUMERIC, v.materias_reprobadas::SMALLINT, v.materias_canceladas::SMALLINT,\n"
             "    v.materias_repetidas::SMALLINT, v.estado_matricula\nFROM (VALUES\n"
             + ",\n".join("    " + fila(*[a[c] for c in acols]) for a in acads)
             + f"\n) AS v({', '.join(acols)})\n"
               "JOIN estudiantes e ON e.codigo = v.codigo\nJOIN periodos_academicos p ON p.codigo = v.periodo\n"
               "ON CONFLICT (estudiante_id, periodo_id) DO NOTHING;\n")
    L.append("COMMIT;\n")
    return "\n".join(L)


if __name__ == "__main__":
    (CARPETA / "roles_y_usuarios.sql").write_text(roles_y_usuarios(), encoding="utf-8")
    (CARPETA / "datos_prueba.sql").write_text(datos_prueba(), encoding="utf-8")
    print("Generados: database/roles_y_usuarios.sql y database/datos_prueba.sql")
