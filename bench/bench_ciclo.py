import gc
import random
import sys
import time

from model.enemigo_logica import Enemigo
from model.jugador_logica import Jugador
from model.partida_logica import Partida
from model.ruta_cazador import DecisorCazador, MODOS
from model.sala_logica import Sala, Salida
from structures.ordenamientos import ordenar

LIMITE_MS = 20
ACCIONES = 3000
RANGOS_CAZADOR = (100, 300, 1000)
RANGO_TOTAL = 1_000_000  #alcanza toda la cripta
#(nombre, salas, enemigos, cazadores)
ESCENARIOS = (
    ("normal", 20, 30, 0),
    ("grande", 100, 100, 0),
    ("extremo", 100, 300, 0),
    ("cazadores", 100, 300, 30),
    ("cazadores_rango_total", 100, 300, 30),
)


def armar_partida(num_salas, num_enemigos):
    salas = [Sala(i + 1, f"Sala {i + 1}") for i in range(num_salas)]
    for i in range(num_salas - 1):
        salas[i].agregar_salida(Salida("N", salas[i + 1]))
        salas[i + 1].agregar_salida(Salida("S", salas[i]))
    jugador = Jugador(vida_max=10**9, ataque=10, defensa=10**6, velocidad=100, inventario_max=10, sala=salas[0])
    partida = Partida(jugador, semilla=1)
    for k in range(num_enemigos):
        sala = salas[k % num_salas]
        enemigo = Enemigo(f"e{k}", "x", f"Enemigo {k}", 50, 50, 5, 0, 100, "errante", sala)
        partida.activar_enemigo(enemigo)
    return partida


COSTOS_SALIDA = (1, 10, 50, 100, 250, 500, 1000)


def armar_partida_costos(num_salas, num_enemigos, semilla):
    azar = random.Random(semilla)
    salas = [Sala(i + 1, f"Sala {i + 1}") for i in range(num_salas)]
    for i in range(num_salas - 1):
        costo = azar.choice(COSTOS_SALIDA)  # el mismo costo en los dos lados de la puerta
        salas[i].agregar_salida(Salida("N", salas[i + 1], costo=costo))
        salas[i + 1].agregar_salida(Salida("S", salas[i], costo=costo))
    jugador = Jugador(vida_max=10**9, ataque=10, defensa=10**6, velocidad=100, inventario_max=10, sala=salas[0])
    partida = Partida(jugador, semilla=semilla)
    for k in range(num_enemigos):
        sala = salas[k % num_salas]
        enemigo = Enemigo(f"e{k}", "x", f"Enemigo {k}", 50, 50, 5, 0, 100, "errante", sala)
        partida.activar_enemigo(enemigo)
    return partida


def armar_partida_cazadores(num_salas, num_enemigos, num_cazadores, semilla, rango_fijo=None, modo=None):
    """Misma cadena y mismos costos que armar_partida_costos; los últimos `num_cazadores`
    enemigos son cazadores con rango sorteado (o `rango_fijo`) y el resto errantes."""
    azar = random.Random(semilla)
    salas = [Sala(i + 1, f"Sala {i + 1}") for i in range(num_salas)]
    for i in range(num_salas - 1):
        costo = azar.choice(COSTOS_SALIDA)
        salas[i].agregar_salida(Salida("N", salas[i + 1], costo=costo))
        salas[i + 1].agregar_salida(Salida("S", salas[i], costo=costo))
    jugador = Jugador(vida_max=10**9, ataque=10, defensa=10**6, velocidad=100, inventario_max=10, sala=salas[0])
    partida = Partida(jugador, semilla=semilla)
    if modo is not None:
        partida.decisor_cazador = DecisorCazador(modo)
    primero_cazador = num_enemigos - num_cazadores
    for k in range(num_enemigos):
        sala = salas[k % num_salas]
        if k >= primero_cazador:
            sorteado = azar.choice(RANGOS_CAZADOR)
            rango = rango_fijo if rango_fijo is not None else sorteado
            enemigo = Enemigo(f"c{k}", "x", f"Cazador {k}", 50, 50, 5, 0, 100, "cazador", sala, rango=rango)
        else:
            enemigo = Enemigo(f"e{k}", "x", f"Enemigo {k}", 50, 50, 5, 0, 100, "errante", sala)
        partida.activar_enemigo(enemigo)
    return partida


def medir_ciclos(partida):
    tiempos = []
    gc.disable()
    try:
        for i in range(ACCIONES):
            inicio = time.perf_counter()
            if i % 10 == 9:
                partida.retroceder()
            else:
                partida.esperar_jugador()
            tiempos.append((time.perf_counter() - inicio) * 1000)
    finally:
        gc.enable()
    return tiempos


def ejecutar(modo=None):
    """`modo` (opcional) cambia el modo del decisor de cazadores; sin él se usa el de Partida."""
    print(f"{'escenario':>22} {'salas':>6} {'enemigos':>9} {'promedio':>10} {'p99':>9} {'peor':>9}   (ms)")
    for nombre, salas, enemigos, cazadores in ESCENARIOS:
        if cazadores > 0:
            rango_fijo = RANGO_TOTAL if nombre.endswith("rango_total") else None
            partida = armar_partida_cazadores(salas, enemigos, cazadores, 1, rango_fijo, modo)
        else:
            partida = armar_partida(salas, enemigos)
        tiempos = medir_ciclos(partida)
        ordenados = ordenar(tiempos, lambda t: t)
        promedio = sum(tiempos) / len(tiempos)
        p99 = ordenados[int(len(ordenados) * 0.99)]
        peor = ordenados[-1]
        veredicto = "cumple" if p99 <= LIMITE_MS else "NO cumple"
        print(f"{nombre:>22} {salas:>6} {enemigos:>9} {promedio:>10.3f} {p99:>9.3f} {peor:>9.3f}   {veredicto}")
    print(f"\nLimite: {LIMITE_MS} ms por ciclo (veredicto sobre el percentil 99: p99 <= {LIMITE_MS} ms)")


def ejecutar_modos():
    """Corre todos los escenarios una vez por cada modo del decisor de cazadores."""
    for modo in MODOS:
        print(f"--- modo {modo} ---", flush=True)
        ejecutar(modo)


if __name__ == "__main__":
    if "--modos" in sys.argv[1:]:
        ejecutar_modos()
    else:
        ejecutar()