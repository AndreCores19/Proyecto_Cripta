"""Constructores y oráculo de ruta para las pruebas de la niebla de guerra (no es módulo de pruebas).

Solo importa de model/, service/, tests/mapas_cazador.py y tests/estado_fijo.py.
Los números de estado (conocimiento 2 = explorada; memoria 1 = abierta,
2 = cerrada) se escriben aquí como literales a propósito: el oráculo no debe
depender de las constantes ni de los métodos del modelo que prueba.
"""
from model.jugador_logica import Jugador
from model.partida_logica import Partida
from service.juego_service import JuegoService
from tests.estado_fijo import FabricaFalsa

INFINITO = float("inf")

_EXPLORADA = 2
_ABIERTA = 1
_CERRADA = 2


def partida_en(salas, sala_jugador, velocidad=100):
    """Partida sembrada (semilla 1) con un jugador casi invulnerable en `sala_jugador`."""
    jugador = Jugador(vida_max=10 ** 6, ataque=10, defensa=10 ** 6, velocidad=velocidad,
                      inventario_max=10, sala=sala_jugador)
    return Partida(jugador, semilla=1)


def servicio_en(partida):
    """JuegoService sobre `partida` con la fábrica falsa (FabricaFalsa.pobladas lista lo pedido)."""
    return JuegoService(partida, FabricaFalsa())


def explorar_todo(salas):
    """Deja todas las salas exploradas y cada cara de puerta recordada como está en realidad.

    Asignación directa: es preparación de la prueba, fuera del historial.
    """
    for sala in salas:
        sala.conocimiento = _EXPLORADA
        for salida in sala.salidas:
            salida.memoria = _CERRADA if salida.cerrada else _ABIERTA


def _recordada_abierta(salida, sala_jugador):
    """Regla propia del oráculo: estado real si la puerta toca la sala del jugador, si no `memoria`."""
    if salida.origen is sala_jugador or salida.destino is sala_jugador:
        return not salida.cerrada
    return salida.memoria == _ABIERTA


def _usable(salida, sala_jugador):
    return (salida.origen.conocimiento == _EXPLORADA
            and salida.destino.conocimiento == _EXPLORADA
            and _recordada_abierta(salida, sala_jugador))


def _posicion(salas, sala):
    for i, s in enumerate(salas):
        if s is sala:
            return i
    raise ValueError("sala fuera de la cripta")


def ruta_referencia(salas, partida, destino):
    """Oráculo de «ir a»: listas y relajación repetida, sin montículo, estampas ni campos busq_*.

    Devuelve (d, salida): `salida` es la salida abierta de la sala del jugador con
    costo + dist[destino de la salida] == d y menor (destino.id, direccion);
    (0, None) si el jugador ya está en `destino`; (None, None) si no hay ruta.
    """
    aqui = partida.jugador.sala
    dist = [INFINITO] * len(salas)
    dist[_posicion(salas, destino)] = 0
    cambio = True
    while cambio:
        cambio = False
        for i, sala in enumerate(salas):
            for s in sala.salidas:
                if not _usable(s, aqui):
                    continue
                nd = s.costo + dist[_posicion(salas, s.destino)]
                if nd < dist[i]:
                    dist[i] = nd
                    cambio = True
    d = dist[_posicion(salas, aqui)]
    if aqui is destino:
        return 0, None
    if d == INFINITO:
        return None, None
    mejor = None
    for s in aqui.salidas:
        if not _usable(s, aqui) or s.costo + dist[_posicion(salas, s.destino)] != d:
            continue
        if mejor is None or (s.destino.id, s.direccion) < (mejor.destino.id, mejor.direccion):
            mejor = s
    return d, mejor
