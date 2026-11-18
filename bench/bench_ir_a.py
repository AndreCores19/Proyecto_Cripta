"""Benchmark de «ir a» (FR-026, FR-027): un cálculo de ruta con todo el mapa conocido.

Todo es local y sembrado con random.Random(semilla): sin red y sin dibujar nada.
El veredicto es el percentil 99 del cálculo de la ruta (RutaConocida.siguiente_paso solo)
con 100 salas, que debe ser <= 5 ms; también se imprime el máximo. El paso completo
(ruta, movimiento y ciclo de eventos) y los tamaños de 500 y 1000 salas son informativos.
"""
import gc
import random
import time

from bench.bench_ciclo import COSTOS_SALIDA
from bench.bench_cazador import _conectar, _jugador
from model.partida_logica import Partida
from model.ruta_conocida import RutaConocida
from model.sala_logica import ABIERTA, CERRADA, EXPLORADA, Sala
from structures.ordenamientos import ordenar

SEMILLA = 1
LIMITE_MS = 5
CANDIDATAS = 3       #destinos sorteados por repetición; se queda el más lejano en costo


class Config:
    """Tamaños de una corrida: (salas, repeticiones) por tamaño; el primero lleva el veredicto."""

    def __init__(self, tamanos):
        self.tamanos = tamanos


NORMAL = Config(((100, 2000), (500, 300), (1000, 300)))
PEQUENO = Config(((30, 30), (60, 10)))


class Medicion:
    """Lo que devuelve medir(): la cripta, los pares sorteados, las rutas halladas y los tiempos en us."""

    def __init__(self, partida, salas, pares, rutas, us_ruta):
        self.partida = partida
        self.salas = salas
        self.pares = pares          # (sala del jugador, destino) de cada repetición
        self.rutas = rutas          # (salida, d) de cada repetición
        self.us_ruta = us_ruta


def armar_cripta(semilla, num_salas):
    """Cripta conexa sembrada con costos de COSTOS_SALIDA y todo el mapa conocido.

    Árbol de puertas abiertas más puertas extra abiertas. Marca cada sala como explorada y
    cada cara de puerta como recordada abierta por asignación directa: es preparación, no juego.
    Devuelve (partida, salas).
    """
    azar = random.Random(semilla)
    salas = [Sala(i + 1, f"Sala {i + 1}") for i in range(num_salas)]
    for i in range(1, num_salas):
        costo = azar.choice(COSTOS_SALIDA)
        for _ in range(20):
            if _conectar(salas[azar.randrange(i)], salas[i], costo):
                break
    for _ in range(num_salas // 2):
        a, b = azar.choice(salas), azar.choice(salas)
        costo = azar.choice(COSTOS_SALIDA)
        if a is not b:
            _conectar(a, b, costo)
    partida = Partida(_jugador(salas[0]), semilla=semilla)
    for sala in salas:
        sala.conocimiento = EXPLORADA
        for salida in sala.salidas:
            salida.memoria = CERRADA if salida.cerrada else ABIERTA
    return partida, salas


def _elegir_pares(partida, salas, repeticiones, semilla):
    """Jugador y destino por repetición, lejos entre sí: de CANDIDATAS destinos, el de mayor costo de ruta."""
    azar = random.Random(semilla + 1)
    ruta = RutaConocida()
    pares = []
    for _ in range(repeticiones):
        aqui = azar.choice(salas)
        partida.jugador.sala = aqui
        mejor, mejor_d = None, -1
        for _ in range(CANDIDATAS):
            destino = azar.choice(salas)
            _, d = ruta.siguiente_paso(partida, destino)
            if d is not None and d > mejor_d:
                mejor, mejor_d = destino, d
        pares.append((aqui, mejor if mejor is not None else aqui))
    return pares


def medir(num_salas, repeticiones, semilla=SEMILLA):
    """Mide RutaConocida.siguiente_paso solo, en microsegundos, sobre pares sorteados de la semilla."""
    partida, salas = armar_cripta(semilla, num_salas)
    pares = _elegir_pares(partida, salas, repeticiones, semilla)
    ruta = RutaConocida()
    rutas, tiempos = [], []
    gc.disable()
    try:
        for aqui, destino in pares:
            partida.jugador.sala = aqui
            inicio = time.perf_counter()
            resultado = ruta.siguiente_paso(partida, destino)
            tiempos.append((time.perf_counter() - inicio) * 1_000_000)
            rutas.append(resultado)
    finally:
        gc.enable()
    return Medicion(partida, salas, pares, rutas, tiempos)


def medir_paso_completo(num_salas, repeticiones, semilla=SEMILLA):
    """Para información: ruta más movimiento más ciclo de eventos, en microsegundos por paso."""
    partida, salas = armar_cripta(semilla, num_salas)
    pares = _elegir_pares(partida, salas, repeticiones, semilla)
    ruta = RutaConocida()
    tiempos = []
    gc.disable()
    try:
        for aqui, destino in pares:
            partida.jugador.sala = aqui
            inicio = time.perf_counter()
            salida, _ = ruta.siguiente_paso(partida, destino)
            if salida is not None:
                partida.mover(salida.direccion)
            tiempos.append((time.perf_counter() - inicio) * 1_000_000)
    finally:
        gc.enable()
    return tiempos


def resumen(tiempos):
    """(promedio, p99, máximo) de una lista de tiempos, con el p99 como en bench_ciclo."""
    ordenados = ordenar(tiempos, lambda t: t)
    return sum(tiempos) / len(tiempos), ordenados[int(len(ordenados) * 0.99)], ordenados[-1]


def _fila(salas, repeticiones, ruta, paso):
    return (f"{salas:>6} {repeticiones:>6}   ruta {ruta[0]:>9.1f} {ruta[1]:>9.1f} {ruta[2]:>9.1f}"
            f"   paso completo {paso[0]:>9.1f} {paso[1]:>9.1f} {paso[2]:>9.1f}")


def ejecutar(pequeno=False):
    cfg = PEQUENO if pequeno else NORMAL
    print(f"Benchmark de «ir a» (semilla {SEMILLA}; microsegundos; promedio, p99 y máximo)")
    print(f"{'salas':>6} {'reps':>6}   {'':<4} {'prom':>9} {'p99':>9} {'max':>9}"
          f"   {'':<13} {'prom':>9} {'p99':>9} {'max':>9}")
    veredicto = None
    for k, (salas, repeticiones) in enumerate(cfg.tamanos):
        ruta = resumen(medir(salas, repeticiones).us_ruta)
        paso = resumen(medir_paso_completo(salas, repeticiones))
        print(_fila(salas, repeticiones, ruta, paso))
        if k == 0:
            veredicto = (salas, ruta)
    salas, ruta = veredicto
    p99_ms = ruta[1] / 1000
    cumple = "cumple" if p99_ms <= LIMITE_MS else "NO cumple"
    print(f"\nVeredicto con {salas} salas: p99 de la ruta = {p99_ms:.3f} ms, máximo = {ruta[2] / 1000:.3f} ms; "
          f"límite p99 <= {LIMITE_MS} ms: {cumple}")
    print("(el paso completo y los tamaños de más salas son solo informativos)")


if __name__ == "__main__":
    ejecutar()
