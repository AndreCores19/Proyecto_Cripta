"""Historial de retroceso de la parte uno bajo la nueva carga (spec 005, FR-027, §5.6).

Cada escenario corre dos veces con la misma semilla y las mismas acciones: sin línea de tiempo (las cifras
de la parte uno, medidas en vivo) y con la línea de tiempo activa. El benchmark maneja `Partida` directo,
así que en la corrida activa hace lo mismo que `JuegoService`: crea la `LineaTiempoPartida` cuando el mundo
ya está armado (`iniciar`), llama `registrar_accion` tras cada `esperar_jugador` y `tras_retroceso` tras
cada `retroceder`. La columna "capture checkpoint" reemplaza a la antigua "copiar todo" (deepcopy, que la
constitución prohíbe): es lo que cuesta tomar un punto de control.
"""
import gc
import time

from bench.bench_ciclo import armar_partida
from model.linea_tiempo_logica import K_POR_DEFECTO, LineaTiempoPartida
from model.registro_estado import capturar

ESCENARIOS = (
    ("pequeño", 10, 10),
    ("larga", 300, 10),
    ("normal", 20, 30),
    ("grande", 100, 100),
    ("extremo", 100, 300),
)
REPETICIONES = 300


def promedio_us(funcion, repeticiones):
    gc.disable()
    try:
        inicio = time.perf_counter()
        for _ in range(repeticiones):
            funcion()
        return (time.perf_counter() - inicio) / repeticiones * 1_000_000
    finally:
        gc.enable()


def _sin_mundo():
    raise RuntimeError("el benchmark del historial no consulta la línea de tiempo")


def medir(salas, enemigos, con_linea):
    """(acción µs, deshacer µs, cierres guardados, cuadros, captura de un punto µs o None)."""
    partida = armar_partida(salas, enemigos)
    linea = None
    if con_linea:
        linea = LineaTiempoPartida()
        linea.iniciar(partida, _sin_mundo, K_POR_DEFECTO)

    def accion():
        reloj = partida.reloj
        partida.esperar_jugador()
        if linea is not None:
            linea.registrar_accion(partida, "esperar", None, reloj)

    def deshacer():
        if partida.retroceder() and linea is not None:
            linea.tras_retroceso(partida)

    for _ in range(20):
        accion()
    t_accion = promedio_us(accion, REPETICIONES)

    tiempos = []
    for _ in range(REPETICIONES):
        accion()
        gc.disable()
        inicio = time.perf_counter()
        deshacer()
        tiempos.append((time.perf_counter() - inicio) * 1_000_000)
        gc.enable()
    t_deshacer = sum(tiempos) / len(tiempos)

    t_captura = promedio_us(lambda: capturar(partida), 20) if con_linea else None

    for _ in range(10):
        accion()
    h = partida.historial
    guardadas = 0
    for i in range(h.cantidad):
        guardadas += len(h.cuadros[(h.inicio + i) % h.capacidad])
    return t_accion, t_deshacer, guardadas, h.cantidad, t_captura


def ejecutar():
    """Imprime la tabla lado a lado y devuelve sus filas:
    (escenario, acción parte uno, acción con línea, deshacer parte uno, deshacer con línea, cierres, cuadros, captura)."""
    print(f" Historial de retroceso: parte uno y bajo la nueva carga (microsegundos; K={K_POR_DEFECTO}) ")
    print(f"{'escenario':>10}{'salas':>7}{'enemigos':>10} | {'action (part one)':>17} | {'action (timeline)':>17} | "
          f"{'undo (part one)':>15} | {'undo (timeline)':>15} | {'closures kept (max 5 frames)':>28} | "
          f"{'capture checkpoint (us)':>23}")
    filas = []
    for nombre, salas, enemigos in ESCENARIOS:
        accion_uno, deshacer_uno, guardadas_uno, cuadros_uno, _ = medir(salas, enemigos, False)
        accion_linea, deshacer_linea, guardadas, cuadros, captura = medir(salas, enemigos, True)
        assert guardadas == guardadas_uno and cuadros == cuadros_uno   #la línea no cambia lo que guarda el historial
        print(f"{nombre:>10}{salas:>7}{enemigos:>10} | {accion_uno:>17.1f} | {accion_linea:>17.1f} | "
              f"{deshacer_uno:>15.1f} | {deshacer_linea:>15.1f} | {guardadas:>20} en {cuadros:<5} | {captura:>23.1f}")
        filas.append((nombre, accion_uno, accion_linea, deshacer_uno, deshacer_linea, guardadas, cuadros, captura))
    print("\naction (part one)  = una acción del jugador con el historial activo, sin línea de tiempo")
    print(f"action (timeline)  = la misma acción con la línea de tiempo anotando (un punto cada {K_POR_DEFECTO})")
    print("undo               = revertir la última acción con el historial (con la línea: más el recorte)")
    print("closures kept      = funciones de deshacer guardadas en total (máximo 5 cuadros)")
    print("capture checkpoint = tomar un punto de control (reemplaza la copia completa con deepcopy, descartada)")
    return filas


if __name__ == "__main__":
    ejecutar()
