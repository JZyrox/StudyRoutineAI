"""
Generador del dataset sintético de perfiles de estudio
120 registros — basado en técnicas Pomodoro y criterios pedagógicos
Distribución: 4 tiempos × 3 cantidades de materias × 10 variantes = 120
Cada rutina objetivo fue generada por el motor de inferencia del Sistema Experto.
Instituto Tecnológico de Ensenada — IA
Daniela Guadalupe Hernández Guzmán (21760148)
"""

import csv
import json
import random

#  CONFIGURACIÓN DEL DATASET

TIEMPOS      = [30, 60, 90, 120]   # minutos disponibles
DIFICULTADES = [1, 2, 3, 4, 5]

# Catálogo de materias — ninguna predeterminada como "la difícil"
CATALOGO_MATERIAS = [
    "Matemáticas", "Física", "Química", "Biología", "Historia",
    "Inglés", "Programación", "Cálculo", "Estadística", "Literatura",
    "Economía", "Contabilidad", "Álgebra", "Geografía", "Filosofía",
    "Redes", "Base de Datos", "Electrónica", "Derecho", "Administración"
]

#  MOTOR DE INFERENCIA DEL SISTEMA EXPERTO
#
#  Reglas SI-ENTONCES aplicadas (método Pomodoro + criterios pedagógicos):
#  - SI hay más de una materia → insertar descanso de 10 min entre ellas.
#  - SI tiempo >= 60 min → agregar repaso final del 10% del tiempo (mín. 5 min).
#  - PARA CADA materia → asignar tiempo proporcional a su dificultad relativa.
#    Ejemplo: dificultades 3 y 2 → 60% y 40% del tiempo de estudio.
#  - Ningún bloque de estudio puede ser menor a 5 minutos.

def calcular_pesos(materias_dif):
    """Convierte dificultades en proporciones del tiempo total de estudio."""
    total = sum(d for _, d in materias_dif)
    return [(m, d, d / total) for m, d in materias_dif]

def generar_rutina_objetivo(tiempo_total, materias_dif, duracion_descanso=10, repaso_final=True):
    """Aplica las reglas del Sistema Experto y devuelve la rutina estructurada."""
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


#  GENERACIÓN DE LOS 120 REGISTROS
#
#  Cada registro representa un perfil de estudiante hipotético.
#  La rutina_objetivo es la que el Sistema Experto genera para ese perfil,
#  y sirve como referencia para verificar el sistema más adelante.


def generar_dataset():
    registros  = []
    random.seed(42)   # Semilla fija para reproducibilidad
    id_usuario = 1

    # 4 tiempos × 3 cantidades de materias × 10 variantes = 120 registros
    for tiempo in TIEMPOS:
        for n_materias in [1, 2, 3]:
            for _ in range(10):

                # Elegir materias sin repetir
                materias_elegidas = random.sample(CATALOGO_MATERIAS, n_materias)

                # Asignar dificultad individual a cada materia
                materias_dif = [
                    (m, random.choice(DIFICULTADES))
                    for m in materias_elegidas
                ]

                # Dificultad general = promedio redondeado
                dif_general = round(sum(d for _, d in materias_dif) / n_materias)

                # Generar rutina aplicando las reglas del Sistema Experto
                repaso  = tiempo >= 60   # Regla: repaso solo si hay tiempo suficiente
                bloques = generar_rutina_objetivo(tiempo, materias_dif, 10, repaso)

                registros.append({
                    "id_usuario":             id_usuario,
                    "tiempo_disponible":      tiempo,
                    "materias":               ",".join(m for m, _ in materias_dif),
                    "nivel_dificultad":       dif_general,
                    "dificultad_por_materia": json.dumps(
                        {m: d for m, d in materias_dif}, ensure_ascii=False
                    ),
                    "rutina_objetivo":        json.dumps(bloques, ensure_ascii=False)
                })
                id_usuario += 1

    return registros


#  GUARDAR CSV


def guardar_csv(registros, ruta="dataset_estudio.csv"):
    campos = [
        "id_usuario", "tiempo_disponible", "materias",
        "nivel_dificultad", "dificultad_por_materia", "rutina_objetivo"
    ]
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(registros)
    print(f"Dataset guardado: {ruta}  ({len(registros)} registros)")

if __name__ == "__main__":
    datos = generar_dataset()
    guardar_csv(datos)