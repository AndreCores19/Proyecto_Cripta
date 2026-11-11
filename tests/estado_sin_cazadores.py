"""Estado final de partidas sembradas sin cazadores (helper, no es un módulo de pruebas).

Sirve para comprobar FR-013 y FR-014 (SC-006): el estado de una partida sin
cazadores no cambia con la llegada del cazador. Se capturó antes de cualquier
cambio de código en specs/002-hunter-enemy/estado-sin-cazadores-antes.txt.
"""
from bench.bench_ciclo import armar_partida_costos

ACCIONES = 500


def resumen(semilla):
    """Juega 500 acciones sembradas y devuelve el estado final como texto."""
    partida = armar_partida_costos(30, 50, semilla)
    for k, enemigo in enumerate(partida.enemigos):
        if k % 2 == 1:
            enemigo.comportamiento = "rastreador"
    direccion = "N"
    for i in range(ACCIONES):
        if i % 5 == 4:
            assert partida.esperar_jugador() is True
            continue
        if partida.jugador.sala.salida(direccion) is None:
            direccion = "S" if direccion == "N" else "N"
        assert partida.mover(direccion) is True
    jugador = partida.jugador
    lineas = [
        f"reloj {partida.reloj}",
        f"acciones_jugador {partida.acciones_jugador}",
        f"jugador sala {jugador.sala.id} vida {jugador.vida}",
    ]
    lineas += [f"{e.id_enemigo} {e.sala.id} {e.vida}" for e in partida.enemigos]
    return "\n".join(lineas) + "\n"
