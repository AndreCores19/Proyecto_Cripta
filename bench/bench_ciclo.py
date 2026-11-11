import gc
import random
import time

from model.enemigo_logica import Enemigo
from model.jugador_logica import Jugador
from model.partida_logica import Partida
from model.sala_logica import Sala, Salida
from structures.ordenamientos import ordenar

LIMITE_MS = 20
ACCIONES = 3000
ESCENARIOS = (
    ("normal", 20, 30),
    ("grande", 100, 100),
    ("extremo", 100, 300),
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


def ejecutar():
    print(f"{'escenario':>10} {'salas':>6} {'enemigos':>9} {'promedio':>10} {'p99':>9} {'peor':>9}   (ms)")
    for nombre, salas, enemigos in ESCENARIOS:
        tiempos = medir_ciclos(armar_partida(salas, enemigos))
        ordenados = ordenar(tiempos, lambda t: t)
        promedio = sum(tiempos) / len(tiempos)
        p99 = ordenados[int(len(ordenados) * 0.99)]
        peor = ordenados[-1]
        veredicto = "cumple" if p99 < LIMITE_MS else "NO cumple"
        print(f"{nombre:>10} {salas:>6} {enemigos:>9} {promedio:>10.3f} {p99:>9.3f} {peor:>9.3f}   {veredicto}")
    print(f"\nLimite: {LIMITE_MS} ms por ciclo (veredicto sobre el percentil 99)")


if __name__ == "__main__":
    ejecutar()