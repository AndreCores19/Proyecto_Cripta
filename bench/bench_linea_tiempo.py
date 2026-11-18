"""Benchmark de la línea de tiempo (spec 005, FR-021, FR-024 … FR-027; contrato reporte-bench-linea-tiempo).

Para cada mundo sintético y cada K (10, 50, 200 y "none": solo el punto 0, que reproduce desde el inicio)
mide la memoria de los puntos de control y de acciones + libro (tracemalloc sobre la línea de tiempo sola),
el tiempo de un conjunto de consultas `historia t` elegidas por semilla en toda la partida (p99, promedio y
peor), la parte del tiempo que es armar el grafo y el máximo de acciones reproducidas. Elige el K por
defecto con la regla fijada en plan.md ("Default K"). Sin red y sin vista.
"""
import gc
import random
import sys
import time
import tracemalloc

from bench.juego_sintetico import MUNDOS, MundoSintetico, jugar
from data.grafo_reutilizable import GrafoReutilizable
from model.reproduccion_logica import Reproductor
from service.historia_service import resumen_de
from structures.ordenamientos import ordenar

KS = (10, 50, 200)
SIN_PUNTOS = 10 ** 9                 #"none": K mayor que cualquier partida, solo existe el punto 0
ACCIONES = 5000
SEMILLA = 7
CONSULTAS = 200
CONSULTAS_SIN_PUNTOS = 20            #cada una reproduce hasta toda la partida: pocas bastan para el p99
LIMITE_MS = 50                       #FR-024
REGLA_MS = 25                        #plan.md: el mayor K con p99 <= 25 ms en `referencia`
MUNDO_VEREDICTO = "referencia"

FILTROS_PUNTOS = (tracemalloc.Filter(True, "*registro_estado.py"),)
FILTROS_ACCIONES = (tracemalloc.Filter(True, "*structures*linea_tiempo.py"),
                    tracemalloc.Filter(True, "*linea_tiempo_logica.py"),
                    tracemalloc.Filter(True, "*efectos_omitidos.py"))


def _bytes(instantanea, filtros):
    total = 0
    for estadistica in instantanea.filter_traces(filtros).statistics("filename"):
        total += estadistica.size
    return total


def grabar(nombre, semilla, acciones, k, mundo=None):
    """Juega con la línea de tiempo bajo tracemalloc. Devuelve (juego, bytes de puntos, bytes de acciones + libro)."""
    gc.collect()
    tracemalloc.start()
    try:
        juego = jugar(nombre, semilla, acciones, k, mundo=mundo)
        instantanea = tracemalloc.take_snapshot()
    finally:
        tracemalloc.stop()
    return juego, _bytes(instantanea, FILTROS_PUNTOS), _bytes(instantanea, FILTROS_ACCIONES)


def instantes(juego, cantidad, semilla):
    """Instantes por semilla repartidos en toda la partida, con el más viejo (0) y el más reciente."""
    reloj = juego.partida.reloj
    azar = random.Random(semilla)
    elegidos = [0, reloj]
    for _ in range(max(0, cantidad - 2)):
        elegidos.append(azar.randint(0, reloj))
    return elegidos


def p99(tiempos):
    ordenados = ordenar(tiempos, lambda t: t)
    return ordenados[int(len(ordenados) * 0.99)]


class Medicion:
    def __init__(self, k, puntos, mem_puntos, mem_acciones, tiempos, t_grafo, max_reproducidas):
        self.k = k
        self.puntos = puntos
        self.mem_puntos = mem_puntos
        self.mem_acciones = mem_acciones
        self.tiempos = tiempos
        self.t_grafo = t_grafo
        self.max_reproducidas = max_reproducidas

    @property
    def p99(self):
        return p99(self.tiempos)

    @property
    def promedio(self):
        return sum(self.tiempos) / len(self.tiempos)

    @property
    def peor(self):
        return max(self.tiempos)

    @property
    def parte_grafo(self):
        return self.t_grafo / sum(self.tiempos)


def medir_consultas(juego, lista):
    """Cada consulta: el Reproductor desde el punto más cercano y el resumen (lo que hace `historia t`).

    Como el servicio, el grafo aparte se arma una vez por partida y se limpia en cada consulta
    (`GrafoReutilizable`); "graph build" es el tiempo de esa limpieza (y del primer armado)."""
    t_grafo = [0.0]
    mundo = juego.mundo
    grafo = GrafoReutilizable(mundo.constructor)

    def armar():
        inicio = time.perf_counter()
        resultado = mundo.mundo_sobre(grafo.limpio())
        t_grafo[0] += (time.perf_counter() - inicio) * 1000
        return resultado

    tiempos = []
    maximo = 0
    for t in lista:
        gc.disable()
        try:
            inicio = time.perf_counter()
            reproductor = Reproductor(juego.linea, armar)
            resumen_de(reproductor.en_instante(t), t)
            tiempos.append((time.perf_counter() - inicio) * 1000)
        finally:
            gc.enable()
        maximo = max(maximo, reproductor.acciones_aplicadas)
    return tiempos, t_grafo[0], maximo


def medir(nombre, k, acciones, consultas, semilla=SEMILLA, mundo=None):
    juego, mem_puntos, mem_acciones = grabar(nombre, semilla, acciones, k, mundo)
    tiempos, t_grafo, maximo = medir_consultas(juego, instantes(juego, consultas, semilla + 1))
    return juego, Medicion(k, len(juego.linea.puntos), mem_puntos, mem_acciones, tiempos, t_grafo, maximo)


def elegir_k(filas, umbral_ms=REGLA_MS):
    """La regla de plan.md: el mayor K (sin contar "none") con p99 <= umbral; None si ninguno cumple."""
    elegido = None
    for k, p in filas:
        if k != SIN_PUNTOS and p <= umbral_ms and (elegido is None or k > elegido):
            elegido = k
    return elegido


def fuera_de_la_rejilla(linea):
    """Puntos de control cuyo número de acciones no es índice·K (debe ser 0, FR-019)."""
    fuera = 0
    for i, punto in enumerate(linea.puntos):
        if punto.acciones_jugador != i * linea.k:
            fuera += 1
    return fuera


def _kb(n):
    return f"{n / 1024:.1f} KB"


def _nombre_k(k):
    return "none" if k == SIN_PUNTOS else str(k)


def lineas_tabla(nombre, acciones, semilla, mediciones):
    lineas = [f"== Timeline: memory and query time (world={nombre}, actions={acciones}, seed={semilla}, "
              f"queries={CONSULTAS}; none: {CONSULTAS_SIN_PUNTOS}) ==",
              f"{'K':>6} | {'checkpoints':>11} | {'memory checkpoints':>18} | {'memory actions + ledger':>23} | "
              f"{'graph build':>11} | {'max actions re-played':>21} | {'p99 (ms)':>9} | {'mean (ms)':>9} | "
              f"{'worst (ms)':>10} | verdict p99 <= {LIMITE_MS} ms"]
    for m in mediciones:
        puntos = "1 (start)" if m.k == SIN_PUNTOS else str(m.puntos)
        veredicto = "cumple" if m.p99 <= LIMITE_MS else "NO cumple"
        maximo = f"{m.max_reproducidas} (whole game)" if m.k == SIN_PUNTOS else str(m.max_reproducidas)
        lineas.append(f"{_nombre_k(m.k):>6} | {puntos:>11} | {_kb(m.mem_puntos):>18} | {_kb(m.mem_acciones):>23} | "
                      f"{m.parte_grafo * 100:>10.1f}% | {maximo:>21} | {m.p99:>9.2f} | {m.promedio:>9.2f} | "
                      f"{m.peor:>10.2f} | {veredicto}")
    return lineas


def linea_k_por_defecto(mediciones):
    filas = [(m.k, m.p99) for m in mediciones]
    elegido = elegir_k(filas)
    memorias = ", ".join(f"K={_nombre_k(m.k)}: {_kb(m.mem_puntos + m.mem_acciones)}" for m in mediciones)
    if elegido is None:
        return elegido, (f"Default K: none qualifies (no K with p99 <= {REGLA_MS} ms on {MUNDO_VEREDICTO}) "
                         f"-> the group decides with the table above; memory: {memorias}")
    fila = next(m for m in mediciones if m.k == elegido)
    return elegido, (f"Default K: {elegido}   rule: largest K with p99 <= {REGLA_MS} ms on {MUNDO_VEREDICTO}; "
                     f"memory of every K: {memorias}   -> row K={elegido} (p99 {fila.p99:.2f} ms)")


def medir_linealidad(nombre, k, acciones, semilla=SEMILLA):
    """La misma semilla con A y 2A acciones y K fijo: la memoria debe crecer ~2 veces (FR-021)."""
    mundo = MundoSintetico(nombre)
    _, p1, a1 = grabar(nombre, semilla, acciones, k, mundo)
    _, p2, a2 = grabar(nombre, semilla, 2 * acciones, k, mundo)
    return p1 + a1, p2 + a2


def _bytes_cuadros(historial):
    """Bytes que guardan los cuadros del Historial (cierres, sus celdas y lo que apuntan, superficial)."""
    total = 0
    for i in range(historial.cantidad):
        for cierre in historial.cuadros[(historial.inicio + i) % historial.capacidad]:
            total += sys.getsizeof(cierre)
            celdas = getattr(cierre, "__closure__", None) or ()
            total += sys.getsizeof(celdas)
            for celda in celdas:
                total += sys.getsizeof(celda)
                try:
                    total += sys.getsizeof(celda.cell_contents)
                except ValueError:
                    pass
    return total


def adelante_atras(nombre, acciones, semilla=SEMILLA):
    """Costo de reproducir hacia adelante por acción vs. invertir hacia atrás por acción (investigación R1)."""
    juego = jugar(nombre, semilla, acciones, SIN_PUNTOS)
    frontera = len(juego.linea)
    reproductor = Reproductor(juego.linea, juego.mundo.armar_mundo)
    gc.disable()
    try:
        inicio = time.perf_counter()
        reproductor._hasta_frontera(frontera)
        adelante = (time.perf_counter() - inicio) * 1_000_000 / max(1, frontera)
    finally:
        gc.enable()
    partida = juego.partida
    tiempos = []
    for _ in range(300):
        partida.esperar_jugador()
        gc.disable()
        try:
            inicio = time.perf_counter()
            partida.retroceder()
            tiempos.append((time.perf_counter() - inicio) * 1_000_000)
        finally:
            gc.enable()
    for _ in range(10):
        partida.esperar_jugador()
    h = partida.historial
    cierres = 0
    for i in range(h.cantidad):
        cierres += len(h.cuadros[(h.inicio + i) % h.capacidad])
    por_accion = cierres / max(1, h.cantidad)
    bytes_por_accion = _bytes_cuadros(h) / max(1, h.cantidad)
    return adelante, sum(tiempos) / len(tiempos), por_accion, bytes_por_accion * ACCIONES


def ejecutar(acciones=ACCIONES, consultas=CONSULTAS, consultas_sin_puntos=CONSULTAS_SIN_PUNTOS,
             mundos=MUNDOS, semilla=SEMILLA, imprimir=print, ks=None):
    """Corre el benchmark e imprime el reporte; devuelve (K por defecto o None, mediciones por mundo).

    `ks`: opcional, {mundo: K a medir} (SIN_PUNTOS es la fila "none"); sin él, KS y "none" en cada mundo."""
    resultados = []
    elegido = None
    juego_veredicto = None
    for nombre in mundos:
        mundo = MundoSintetico(nombre)
        mediciones = []
        for k in (ks[nombre] if ks is not None else KS + (SIN_PUNTOS,)):
            juego, m = medir(nombre, k, acciones, consultas if k != SIN_PUNTOS else consultas_sin_puntos,
                             semilla, mundo)
            mediciones.append(m)
            if nombre == MUNDO_VEREDICTO and k == KS[1]:
                juego_veredicto = juego
        for linea in lineas_tabla(nombre, acciones, semilla, mediciones):
            imprimir(linea)
        if nombre == MUNDO_VEREDICTO:
            elegido, texto = linea_k_por_defecto(mediciones)
            imprimir(texto)
        imprimir("")
        resultados.append((nombre, mediciones))
    k_lineal = elegido if elegido is not None else KS[1]
    m1, m2 = medir_linealidad(MUNDO_VEREDICTO, k_lineal, acciones, semilla)
    imprimir(f"Linearity (K={k_lineal}, world={MUNDO_VEREDICTO}): A={acciones} memory={_kb(m1)}  "
             f"A={2 * acciones} memory={_kb(m2)}  ratio={m2 / m1:.2f}   (expected ~2, not A*S)")
    if juego_veredicto is None:
        juego_veredicto = jugar(MUNDO_VEREDICTO, semilla, acciones, KS[1])
    linea = juego_veredicto.linea
    imprimir(f"Scroll reads={juego_veredicto.lecturas}  ledger entries kept={len(linea.linea.omitidos)}  "
             f"checkpoints off the K grid={fuera_de_la_rejilla(linea)}   (K={linea.k}, world={MUNDO_VEREDICTO})")
    adelante, atras, cierres, extrapolado = adelante_atras(MUNDO_VEREDICTO, min(acciones, 1000), semilla)
    imprimir(f"Forward vs backward: re-simulate forward {adelante:.1f} us/action | invert backward "
             f"{atras:.1f} us/action |")
    imprimir(f"                     closures per action in Historial {cierres:.1f} | extrapolated bytes at "
             f"A={ACCIONES} actions {extrapolado / 1024:.0f} KB (shallow size of the closures, if every action "
             f"were kept)")
    return elegido, resultados


def _leer_mundos(argumentos):
    """`--mundo referencia:5,10,50,200,none --mundo grande:10,50` -> (mundos, {mundo: K}); sin nada, None."""
    if not argumentos:
        return None
    mundos, ks = [], {}
    for texto in argumentos:
        nombre, _, lista = texto.partition(":")
        if nombre not in MUNDOS or not lista:
            raise SystemExit(f"--mundo espera <{'|'.join(MUNDOS)}>:K,K,...,none; recibió {texto!r}")
        mundos.append(nombre)
        ks[nombre] = tuple(SIN_PUNTOS if k == "none" else int(k) for k in lista.split(","))
    return tuple(mundos), ks


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Benchmark de la línea de tiempo (spec 005)")
    parser.add_argument("--mundo", action="append", help="mundo:K,K,...,none (se puede repetir)")
    elegidos = _leer_mundos(parser.parse_args().mundo)
    if elegidos is None:
        ejecutar()
    else:
        ejecutar(mundos=elegidos[0], ks=elegidos[1])
