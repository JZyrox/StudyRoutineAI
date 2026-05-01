"""
Generador del dataset sintético de perfiles de estudio
120 registros — basado en técnicas Pomodoro y criterios pedagógicos
Instituto Tecnológico de Ensenada — IA
Daniela Guadalupe Hernández Guzmán (21760148)
"""

import csv
import json
import random

#  CONFIGURACIÓN DEL DATASET

TIEMPOS     = [30, 60, 90, 120]          # minutos disponibles
DIFICULTADES = [1, 2, 3, 4, 5]

# Materias variadas — ninguna predeterminada como "la difícil"
CATALOGO_MATERIAS = [
    "Matemáticas", "Física", "Química", "Biología", "Historia",
    "Inglés", "Programación", "Cálculo", "Estadística", "Literatura",
    "Economía", "Contabilidad", "Álgebra", "Geografía", "Filosofía",
    "Redes", "Base de Datos", "Electrónica", "Derecho", "Administración"
]

#  MOTOR DE REGLAS (igual que el programa principal)

def calcular_pesos(materias_dif):
    total = sum(d for _, d in materias_dif)
    return [(m, d, d / total) for m, d in materias_dif]

def generar_rutina_objetivo(tiempo_total, materias_dif, duracion_descanso=10, repaso_final=True):
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

def generar_dataset():
    registros = []
    random.seed(42)  # Semilla fija para reproducibilidad
    id_usuario = 1

    # Distribuir 120 registros cubriendo combinaciones representativas:
    # 4 tiempos × 3 cantidades de materias = 12 grupos × 10 registros = 120
    for tiempo in TIEMPOS:          # 30, 60, 90, 120 min
        for n_materias in [1, 2, 3]:  # 1, 2 o 3 materias
            for _ in range(10):       # 10 variantes por combinación

                # Elegir materias sin repetir
                materias_elegidas = random.sample(CATALOGO_MATERIAS, n_materias)

                # Asignar dificultad individual a cada materia (aleatoria)
                materias_dif = [
                    (m, random.choice(DIFICULTADES))
                    for m in materias_elegidas
                ]

                # Dificultad general = promedio redondeado
                dif_general = round(sum(d for _, d in materias_dif) / n_materias)

                # Generar rutina objetivo con las reglas del experto
                descanso = 10
                repaso   = tiempo >= 60  # Repaso solo si hay tiempo suficiente
                bloques  = generar_rutina_objetivo(tiempo, materias_dif, descanso, repaso)

                registros.append({
                    "id_usuario":        id_usuario,
                    "tiempo_disponible": tiempo,
                    "materias":          ",".join(m for m, _ in materias_dif),
                    "nivel_dificultad":  dif_general,
                    "dificultad_por_materia": json.dumps(
                        {m: d for m, d in materias_dif}, ensure_ascii=False
                    ),
                    "rutina_objetivo":   json.dumps(bloques, ensure_ascii=False)
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
