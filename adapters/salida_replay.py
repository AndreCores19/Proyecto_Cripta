"""Salida de --replay mediante funciones simples (T035 · FR-014, Constitución III).

Imprime el mismo texto que imprimía la antigua vista de replay. No importa nada de
model/ ni de view/.
"""


def imprimir_final_replay(resumen):
    print("-" * 40)
    for mensaje in resumen.bitacora[-6:]:
        print(f"  {mensaje}")
    print(f"Tiempo final: {resumen.reloj}")
    if resumen.victoria:
        print("¡Victoria! Escapaste de la cripta.")
    elif resumen.terminada:
        print("Has muerto.")
    else:
        print("Saliste de la partida.")


def imprimir_reporte(solicitudes, presupuesto, aciertos, fallos):
    print("-" * 40)
    print(f"Solicitudes realizadas: {solicitudes} de {presupuesto}")
    if presupuesto is not None:
        print(f"Presupuesto restante: {presupuesto - solicitudes}")
    print(f"Aciertos: {aciertos}, Fallos: {fallos}")
    total = aciertos + fallos
    if total > 0:
        print(f"Porcentaje de aciertos: {aciertos / total * 100:.2f}%")
    else:
        print("Porcentaje de aciertos: N/A")
    print("-" * 40)
