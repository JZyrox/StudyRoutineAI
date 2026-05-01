"""
Preprocesamiento y Validación del Dataset (programa principal)
- Limpieza y normalización
- One-hot encoding de materias
- División 80/20 entrenamiento/validación
- Validación del sistema de reglas contra rutinas objetivo
Instituto Tecnológico de Ensenada — IA
Daniela Guadalupe Hernández Guzmán (21760148)
"""

import csv
import json
import math


#  CATÁLOGO DE MATERIAS (para one-hot)


CATALOGO_MATERIAS = [
    "Matemáticas", "Física", "Química", "Biología", "Historia",
    "Inglés", "Programación", "Cálculo", "Estadística", "Literatura",
    "Economía", "Contabilidad", "Álgebra", "Geografía", "Filosofía",
    "Redes", "Base de Datos", "Electrónica", "Derecho", "Administración"
]


#  MOTOR DE REGLAS (idéntico al programa principal)


def calcular_pesos(materias_dif):
    total = sum(d for _, d in materias_dif)
    return [(m, d, d / total) for m, d in materias_dif]

def generar_rutina(tiempo_total, materias_dif, duracion_descanso=10, repaso_final=True):
    n = len(materias_dif)
    con_pesos = calcular_pesos(materias_dif)

    num_descansos    = n - 1
    tiempo_descansos = num_descansos * duracion_descanso
    tiempo_repaso    = max(5, int(tiempo_total * 0.10)) if repaso_final else 0
    tiempo_estudio   = tiempo_total - tiempo_descansos - tiempo_repaso

    if tiempo_estudio <= 0:
        tiempo_descansos = 0
        num_descansos    = 0
        tiempo_estudio   = tiempo_total - tiempo_repaso

    bloques = []
    asignado = 0
    for i, (materia, dif, peso) in enumerate(con_pesos):
        if i < n - 1:
            mins = max(5, round(peso * tiempo_estudio))
        else:
            mins = max(5, tiempo_estudio - asignado)
        asignado += mins
        bloques.append({"materia": materia, "duracion": mins, "tipo": "estudio"})
        if i < n - 1 and num_descansos > 0:
            bloques.append({"materia": None, "duracion": duracion_descanso, "tipo": "descanso"})

    if repaso_final and tiempo_repaso > 0:
        bloques.append({"materia": "Repaso general", "duracion": tiempo_repaso, "tipo": "repaso"})

    return bloques


#  PASO 1 — CARGAR Y LIMPIAR DATASET


def cargar_dataset(ruta="dataset_estudio.csv"):
    registros = []
    with open(ruta, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for fila in reader:
            # Eliminar espacios sobrantes en campos de texto
            fila["materias"] = fila["materias"].strip()

            # Convertir tipos numéricos
            fila["id_usuario"]        = int(fila["id_usuario"])
            fila["tiempo_disponible"] = int(fila["tiempo_disponible"])
            fila["nivel_dificultad"]  = int(fila["nivel_dificultad"])

            # Parsear JSON embebido
            fila["dificultad_por_materia"] = json.loads(fila["dificultad_por_materia"])
            fila["rutina_objetivo"]        = json.loads(fila["rutina_objetivo"])

            # Separar materias en lista individual
            fila["lista_materias"] = [m.strip() for m in fila["materias"].split(",")]

            registros.append(fila)

    # Verificar que no haya registros con campos vacíos críticos
    limpios = [r for r in registros if r["materias"] and r["tiempo_disponible"] > 0]
    eliminados = len(registros) - len(limpios)
    if eliminados:
        print(f"  ⚠ Se eliminaron {eliminados} registros con datos inválidos.")

    return limpios


#  PASO 2 — NORMALIZACIÓN


def normalizar(registros):
    """Escala nivel_dificultad de 1-5 a 0-1 con fórmula (val-1)/4."""
    for r in registros:
        r["dificultad_normalizada"] = (r["nivel_dificultad"] - 1) / 4
    return registros


#  PASO 3 — ONE-HOT ENCODING DE MATERIAS


def one_hot_encoding(registros):
    """
    Crea un vector binario por registro indicando qué materias están presentes.
    Útil para futura extensión a modelos ML.
    """
    for r in registros:
        vector = {m: 0 for m in CATALOGO_MATERIAS}
        for materia in r["lista_materias"]:
            if materia in vector:
                vector[materia] = 1
        r["one_hot"] = vector
    return registros


#  PASO 4 — DIVISIÓN 80/20


def dividir_dataset(registros):
    total       = len(registros)
    corte       = math.floor(total * 0.80)   # 96 entrenamiento, 24 validación
    entrenamiento = registros[:corte]
    validacion    = registros[corte:]
    return entrenamiento, validacion


#  PASO 5 — VALIDACIÓN DEL SISTEMA DE REGLAS


def comparar_rutinas(generada, objetivo):
    """
    Métrica: coincidencia de bloques de estudio.
    Se compara materia y duración de cada bloque tipo 'estudio'.
    Tolerancia de ±2 minutos en duración.
    """
    est_gen = [b for b in generada  if b["tipo"] == "estudio"]
    est_obj = [b for b in objetivo  if b["tipo"] == "estudio"]

    if len(est_gen) != len(est_obj):
        return False

    for bg, bo in zip(est_gen, est_obj):
        if bg["materia"] != bo["materia"]:
            return False
        if abs(bg["duracion"] - bo["duracion"]) > 2:
            return False
    return True

def validar_sistema(validacion):
    correctos = 0
    errores   = []

    for r in validacion:
        tiempo  = r["tiempo_disponible"]
        repaso  = tiempo >= 60
        mat_dif = list(r["dificultad_por_materia"].items())

        rutina_generada = generar_rutina(tiempo, mat_dif, 10, repaso)
        rutina_objetivo = r["rutina_objetivo"]

        if comparar_rutinas(rutina_generada, rutina_objetivo):
            correctos += 1
        else:
            errores.append({
                "id": r["id_usuario"],
                "tiempo": tiempo,
                "materias": r["materias"],
                "generada": rutina_generada,
                "objetivo": rutina_objetivo
            })

    precision = (correctos / len(validacion)) * 100
    return precision, errores


#  REPORTE FINAL

def imprimir_reporte(entrenamiento, validacion, precision, errores):
    sep = "─" * 54
    print("\n" + "═" * 54)
    print("  REPORTE DE PREPROCESAMIENTO Y VALIDACIÓN")
    print("═" * 54)

    print(f"\n  Total de registros cargados : {len(entrenamiento) + len(validacion)}")
    print(f"  Entrenamiento (80%)         : {len(entrenamiento)} registros")
    print(f"  Validación    (20%)         : {len(validacion)} registros")

    print(f"\n{sep}")
    print("  PREPROCESAMIENTO APLICADO")
    print(sep)
    print("  ✔ Separación de materias en lista individual")
    print("  ✔ Normalización de dificultad (1-5 → 0.0-1.0)")
    print("  ✔ One-hot encoding de materias")
    print(f"  ✔ División 80/20 (sin mezcla aleatoria para reproducibilidad)")

    print(f"\n{sep}")
    print("  VALIDACIÓN DEL SISTEMA DE REGLAS")
    print(sep)
    print(f"  Registros evaluados : {len(validacion)}")
    print(f"  Coincidencias       : {len(validacion) - len(errores)}")
    print(f"  Discrepancias       : {len(errores)}")
    print(f"  Precisión           : {precision:.1f}%")

    if errores:
        print(f"\n  Primeros errores detectados (tolerancia ±2 min):")
        for e in errores[:3]:
            print(f"    ID {e['id']} | {e['tiempo']} min | {e['materias']}")

    print("\n" + "═" * 54)

#  MAIN

def main():
    print("\n  Cargando dataset...")
    registros = cargar_dataset("dataset_estudio.csv")

    print("  Aplicando preprocesamiento...")
    registros = normalizar(registros)
    registros = one_hot_encoding(registros)

    entrenamiento, validacion = dividir_dataset(registros)

    print("  Validando sistema de reglas...")
    precision, errores = validar_sistema(validacion)

    imprimir_reporte(entrenamiento, validacion, precision, errores)

if __name__ == "__main__":
    main()
