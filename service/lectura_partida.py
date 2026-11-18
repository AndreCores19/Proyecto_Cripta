"""Lectura de una partida en DTOs, sin cambiar nada (FR-004, FR-029).

La usan la partida viva (`JuegoService.estado_vista`, `mapa_vista`, `inventario_vista`) y la partida del
mundo aparte de una consulta `historia` (`HistoriaService`): así lo que la consulta muestra se lee con
exactamente el mismo código que lo que el juego mostró.
"""
from model.sala_logica import ABIERTA, CERRADA, EXPLORADA
from dto.estado_vista_dto import JugadorVistaDTO, EnemigoVistaDTO
from dto.inventario_vista_dto import ObjetoInventarioDTO
from dto.mapa_vista_dto import MapaVistaDTO, SalaConocidaDTO, SalidaConocidaDTO
from structures.ordenamientos import ordenar


def jugador_vista(partida):
    j = partida.jugador
    inv = j.inventario
    return JugadorVistaDTO(
        j.nombre, j.vida, j.vida_max, j.ataque, j.defensa, j.velocidad,
        inv.arma_equipada.nombre if inv.arma_equipada is not None else None,
        inv.armadura_equipada.nombre if inv.armadura_equipada is not None else None,
        [e.tipo for e in j.efectos])


def enemigo_vista(enemigo):
    return EnemigoVistaDTO(enemigo.nombre, enemigo.id_enemigo, enemigo.vida, enemigo.vida_max,
                           [ef.tipo for ef in enemigo.efectos], enemigo.es_cazador())


def enemigos_de_la_sala(partida):
    #los enemigos activos en la sala del jugador, como los muestra la vista de sala
    sala = partida.jugador.sala
    return [enemigo_vista(e) for e in partida.enemigos if e.sala is sala]


def objeto_inventario(objeto, actual):
    return ObjetoInventarioDTO(objeto.id_instancia, objeto.nombre, objeto.peso,
                               objeto.valor, bool(objeto.equipado), actual)


def objetos_del_inventario(partida):
    #en el orden de la lista, con la marca del cursor
    inv = partida.jugador.inventario
    objetos = []
    nodo = inv.cabeza
    while nodo is not None:
        objetos.append(objeto_inventario(nodo.objeto, nodo is inv.actual))
        nodo = nodo.siguiente
    return objetos


def mapa_vista(partida):
    #solo el conocimiento del jugador de esa partida: nunca muestra lo que no conocía
    exploradas = [s for s in partida.conocidas if s.conocimiento == EXPLORADA]
    salas = []
    for sala in ordenar(exploradas, lambda s: s.id):
        salidas = []
        for s in sala.salidas:
            recordada = partida.puerta_recordada(s)
            puerta = "abierta" if recordada == ABIERTA else "cerrada" if recordada == CERRADA else "sin observar"
            if s.destino.conocimiento == EXPLORADA:
                salidas.append(SalidaConocidaDTO(s.direccion, s.destino.id, s.destino.nombre, s.costo, puerta))
            else:
                salidas.append(SalidaConocidaDTO(s.direccion, None, None, s.costo, puerta))
        salas.append(SalaConocidaDTO(sala.id, sala.nombre, salidas))
    return MapaVistaDTO(partida.jugador.sala.id, salas)
