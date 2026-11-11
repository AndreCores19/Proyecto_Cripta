"""Criptas falsas y oráculo independiente para las pruebas del cazador (no es módulo de pruebas).

Solo importa de model/. El oráculo usa listas y relajación repetida: sin montículo,
sin estampas, sin límite y sin los campos busq_*.
"""
import random

from model.sala_logica import Sala, Salida

COSTOS = (1, 10, 50, 100, 250, 500, 1000)
DIRECCIONES = ("N", "S", "E", "O", "NE", "NO", "SE", "SO")
INFINITO = float("inf")


def _unir(sala_a, dir_a, sala_b, dir_b, costo, cerrada=False, llave=None):
    ida = Salida(dir_a, sala_b, cerrada=cerrada, llave=llave, costo=costo)
    vuelta = Salida(dir_b, sala_a, cerrada=cerrada, llave=llave, costo=costo)
    sala_a.agregar_salida(ida)
    sala_b.agregar_salida(vuelta)
    ida.enlazar(vuelta)
    return ida, vuelta


def cadena(costos):
    """Salas 1..n+1 en línea; salida E/O entre vecinas con el costo dado.

    Devuelve (salas, salidas) con salidas = lista de pares (ida, vuelta).
    """
    salas = [Sala(i + 1, f"S{i + 1}") for i in range(len(costos) + 1)]
    salidas = []
    for i, costo in enumerate(costos):
        salidas.append(_unir(salas[i], "E", salas[i + 1], "O", costo))
    return salas, salidas


def grilla(filas, columnas, costo):
    """filas × columnas salas, ids por filas desde 1, salidas N/S/E/O con el mismo costo."""
    salas = [Sala(i + 1, f"S{i + 1}") for i in range(filas * columnas)]
    salidas = []
    for f in range(filas):
        for c in range(columnas):
            actual = salas[f * columnas + c]
            if c + 1 < columnas:
                salidas.append(_unir(actual, "E", salas[f * columnas + c + 1], "O", costo))
            if f + 1 < filas:
                salidas.append(_unir(actual, "S", salas[(f + 1) * columnas + c], "N", costo))
    return salas, salidas


def _direccion_libre(sala):
    usadas = [s.direccion for s in sala.salidas]
    for d in DIRECCIONES:
        if d not in usadas:
            return d
    return None


def cripta_aleatoria(semilla, num_salas):
    """Cripta conexa sembrada: costos variados, salidas de un solo sentido y puertas cerradas."""
    azar = random.Random(semilla)
    salas = [Sala(i + 1, f"S{i + 1}") for i in range(num_salas)]

    def conectar(a, b):
        costo = azar.choice(COSTOS)
        cerrada = azar.random() < 0.15
        unidireccional = azar.random() < 0.2
        da = _direccion_libre(a)
        db = _direccion_libre(b)
        if unidireccional:
            if azar.random() < 0.5:
                a, b, da = b, a, db
            if da is None:
                return
            a.agregar_salida(Salida(da, b, cerrada=cerrada, costo=costo))
        else:
            if da is None or db is None:
                return
            _unir(a, da, b, db, costo, cerrada=cerrada)

    for i in range(1, num_salas):
        conectar(salas[azar.randrange(i)], salas[i])
    for _ in range(num_salas):
        a, b = azar.choice(salas), azar.choice(salas)
        if a is not b:
            conectar(a, b)
    return salas


def distancias_referencia(salas, sala_jugador):
    """Oráculo: dist[r] = min sobre salidas abiertas s de r de s.costo + dist[s.destino].

    Devuelve (dist, pos): listas paralelas a `salas`; pos[k] es la sala de índice k.
    Para buscar una sala: dist[salas.index(sala)].
    """
    dist = [INFINITO] * len(salas)
    dist[_indice(salas, sala_jugador)] = 0
    cambio = True
    while cambio:
        cambio = False
        for i, sala in enumerate(salas):
            for s in sala.salidas:
                if s.cerrada:
                    continue
                nd = s.costo + dist[_indice(salas, s.destino)]
                if nd < dist[i]:
                    dist[i] = nd
                    cambio = True
    return dist


def _indice(salas, sala):
    for i, s in enumerate(salas):
        if s is sala:
            return i
    raise ValueError("sala fuera de la cripta")


def decision_referencia(salas, sala_jugador, cazador):
    """Salida que debe tomar el cazador según el oráculo, o None."""
    dist = distancias_referencia(salas, sala_jugador)
    d = dist[_indice(salas, cazador.sala)]
    if d == INFINITO or d > cazador.rango:
        return None
    mejor = None
    for s in cazador.sala.salidas:
        if s.cerrada or s.costo + dist[_indice(salas, s.destino)] != d:
            continue
        if mejor is None or (s.destino.id, s.direccion) < (mejor.destino.id, mejor.direccion):
            mejor = s
    return mejor
