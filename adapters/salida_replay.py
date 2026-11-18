"""Salida de --replay mediante funciones simples (T035 · FR-014, Constitución III).

Imprime el mismo texto que imprimía la antigua vista de replay. No importa nada de
model/ ni de view/. El resumen de `--hasta` usa las mismas líneas que el comando `historia` del juego
(adapters/formato_historia.py, FR-014).
"""
from adapters.formato_historia import lineas_historia


def imprimir_historia(respuesta):
    """El resumen de un `RespuestaHistoriaDTO` aceptado, con el mismo texto que la vista de consola."""
    for linea in lineas_historia(respuesta.resumen):
        print(linea)


def imprimir_termino_antes(reloj_final):
    """FR-015: el instante pedido es posterior al final de la partida reproducida."""
    print(f"La partida terminó antes (instante {reloj_final}).")


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
