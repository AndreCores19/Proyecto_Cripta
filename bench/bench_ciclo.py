import gc
import os
import random
import sys
import time

from adapters.cliente_offline import ClienteOffline
from data.repositorio_cripta import RepositorioCripta
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
#Cripta de referencia (FR-017, SC-007): (nombre, salas, cazadores, semilla); "offline" lee el paquete sin red
CARPETA_OFFLINE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "offline")
ESCENARIOS_REFERENCIA = (
    ("referencia_cripta06", "cripta-06", 30, 1),
    ("referencia_sintetica", None, 30, 1),
)
SALAS_SINTETICA = 300


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


def armar_partida_referencia(id_cripta, num_cazadores, semilla, num_salas=SALAS_SINTETICA):
    """Cazadores colocados al azar por semilla (sin repetir sala, fuera de la sala inicial), rango sorteado.
    Con `id_cripta` carga el esqueleto y los costos del paquete sin conexión (sin red); sin él, cadena sintética."""
    if id_cripta is None:
        return armar_partida_cazadores(num_salas, num_cazadores, num_cazadores, semilla)
    repo = RepositorioCripta(ClienteOffline(CARPETA_OFFLINE))
    dtos = repo.cargar_esqueleto(id_cripta)
    repo.construir_salas(dtos)
    inicial = repo.salas.buscar(repo.datos.sala_inicial)
    candidatas = [repo.salas.buscar(dto.id_sala) for dto in dtos if dto.id_sala != repo.datos.sala_inicial]
    azar = random.Random(semilla)
    elegidas = azar.sample(candidatas, num_cazadores)
    jugador = Jugador(vida_max=10**9, ataque=10, defensa=10**6, velocidad=100, inventario_max=10, sala=inicial)
    partida = Partida(jugador, semilla=semilla)
    for k, sala in enumerate(elegidas):
        rango = azar.choice(RANGOS_CAZADOR)
        partida.activar_enemigo(Enemigo(f"c{k}", "x", f"Cazador {k}", 50, 50, 5, 0, 100, "cazador", sala, rango=rango))
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


def _informar(nombre, salas, enemigos, partida):
    tiempos = medir_ciclos(partida)
    ordenados = ordenar(tiempos, lambda t: t)
    promedio = sum(tiempos) / len(tiempos)
    p99 = ordenados[int(len(ordenados) * 0.99)]
    peor = ordenados[-1]
    veredicto = "cumple" if p99 <= LIMITE_MS else "NO cumple"
    print(f"{nombre:>22} {salas:>6} {enemigos:>9} {promedio:>10.3f} {p99:>9.3f} {peor:>9.3f}   {veredicto}")


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
    for nombre, id_cripta, cazadores, semilla in ESCENARIOS_REFERENCIA:
        partida = armar_partida_referencia(id_cripta, cazadores, semilla)
        if modo is not None:
            partida.decisor_cazador = DecisorCazador(modo)
        _informar(nombre, SALAS_SINTETICA, cazadores, partida)
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