"""Registro de estado: lo que cambia de una partida, escrito a mano (sin `copy`).

`capturar(partida)` devuelve un RegistroEstado hecho solo de enteros, textos, listas y tuplas:
no comparte ningún objeto mutable con la partida viva. `restaurar(registro, mundo)` lo aplica
sobre un grafo de salas NUEVO (el esqueleto) y devuelve una Partida sin los efectos del
constructor: no programa eventos ni entra en ninguna sala.

Las salas que no están "tocadas" son el esqueleto. Una sala está tocada si el jugador sabe algo
de ella (conocimiento > 0), dejó rastro, tiene objetos, enemigos inactivos o trampas, o ya fue
poblada. De cada sala tocada se guardan todas sus salidas (cerrada, memoria): una puerta que
difiere del esqueleto siempre está en una sala tocada, y así no hace falta comparar con él.
Las referencias entre entidades se resuelven con vectores ordenados y búsqueda binaria.
"""
from array import array

from model.efectos_logica import Efecto
from model.ruta_cazador import DecisorCazador
from model.sala_logica import DESCONOCIDA, Salida
from model.trampa_logica import Trampa
from structures.agenda import Evento
from structures.ordenamientos import ordenar
from structures.vector_busqueda import VectorBusqueda

SIN_EVENTO = -1
REF_NINGUNO = ("ninguno",)
REF_JUGADOR = ("jugador",)


class ObjetoReg:
    __slots__ = ("id_instancia", "id_catalogo", "equipado")

    def __init__(self, id_instancia, id_catalogo, equipado):
        self.id_instancia = id_instancia
        self.id_catalogo = id_catalogo
        self.equipado = equipado


class EfectoReg:
    __slots__ = ("tipo", "dano", "fin", "cambio_aplicado", "cantidad", "evento")

    def __init__(self, tipo, dano, fin, cambio_aplicado, cantidad, evento):
        self.tipo = tipo
        self.dano = dano
        self.fin = fin
        self.cambio_aplicado = cambio_aplicado
        self.cantidad = cantidad
        self.evento = evento                 #posición del evento en la agenda, o SIN_EVENTO


class TrampaReg:
    __slots__ = ("id_instancia", "armada", "evento")

    def __init__(self, id_instancia, armada, evento):
        self.id_instancia = id_instancia
        self.armada = armada
        self.evento = evento


class SalidaReg:
    __slots__ = ("direccion", "cerrada", "memoria")

    def __init__(self, direccion, cerrada, memoria):
        self.direccion = direccion
        self.cerrada = cerrada
        self.memoria = memoria


class SalaReg:
    __slots__ = ("id_sala", "conocimiento", "rastro", "objetos", "inactivos", "trampas",
                 "poblada", "salidas")

    def __init__(self, id_sala, conocimiento, rastro, objetos, inactivos, trampas, poblada, salidas):
        self.id_sala = id_sala
        self.conocimiento = conocimiento
        self.rastro = rastro
        self.objetos = objetos               #del suelo, en orden
        self.inactivos = inactivos           #ids de enemigo, en orden
        self.trampas = trampas
        self.poblada = poblada
        self.salidas = salidas


class EnemigoReg:
    __slots__ = ("id_enemigo", "id_sala", "vida", "velocidad", "efectos", "evento")

    def __init__(self, id_enemigo, id_sala, vida, velocidad, efectos, evento):
        self.id_enemigo = id_enemigo
        self.id_sala = id_sala
        self.vida = vida
        self.velocidad = velocidad
        self.efectos = efectos
        self.evento = evento


class JugadorReg:
    __slots__ = ("id_sala", "vida", "velocidad", "id_arma", "id_armadura", "efectos",
                 "inventario", "cursor", "evento")

    def __init__(self, id_sala, vida, velocidad, id_arma, id_armadura, efectos, inventario,
                 cursor, evento):
        self.id_sala = id_sala
        self.vida = vida
        self.velocidad = velocidad
        self.id_arma = id_arma
        self.id_armadura = id_armadura
        self.efectos = efectos
        self.inventario = inventario         #objetos en orden
        self.cursor = cursor                 #posición del cursor, o None
        self.evento = evento


class EventoReg:
    __slots__ = ("tiempo", "num_sec", "tipo", "dueno", "datos")

    def __init__(self, tiempo, num_sec, tipo, dueno, datos):
        self.tiempo = tiempo
        self.num_sec = num_sec
        self.tipo = tipo
        self.dueno = dueno                   #referencia (tupla)
        self.datos = datos                   #referencia (tupla)


class RegistroEstado:
    def __init__(self):
        self.semilla = None
        self.reloj = 0
        self.num_sec = 0
        self.azar_version = 0
        self.azar = None                     #array('I') de 625 palabras
        self.azar_gauss = None
        self.acciones_jugador = 0
        self.enemigos_derrotados = 0
        self.terminada = False
        self.victoria = False
        self.abrio_puerta_salida = False
        self.retrocesos = 0
        self.modo_decisor = None
        self.siguiente_instancia = 0
        self.id_sala_salida = None
        self.jugador = None
        self.enemigos = []
        self.salas = []                      #solo las tocadas, por id
        self.conocidas = []                  #ids, en orden de descubrimiento
        self.agenda = []                     #en el orden interno del montículo


class Mundo:
    """Lo que `restaurar` necesita para armar un grafo nuevo.

    `salas`: VectorBusqueda con las salas recién construidas del esqueleto.
    `crear_jugador(sala)`: jugador con las estadísticas base. `crear_objeto(id_instancia, id_catalogo)`,
    `crear_enemigo(id_enemigo)` y `crear_trampa(id_instancia)` los arman en su estado inicial;
    `restaurar` pone encima lo guardado. `fabrica` (opcional) lleva el contador y las salas pobladas
    del mundo nuevo; `creador_objetos` es lo que usa la partida para el botín.
    """

    def __init__(self, salas, crear_jugador, crear_objeto, crear_enemigo, crear_trampa,
                 fabrica=None, creador_objetos=None):
        self.salas = salas
        self.crear_jugador = crear_jugador
        self.crear_objeto = crear_objeto
        self.crear_enemigo = crear_enemigo
        self.crear_trampa = crear_trampa
        self.fabrica = fabrica
        self.creador_objetos = creador_objetos


#captura
def _reg_objeto(objeto):
    return ObjetoReg(objeto.id_instancia, objeto.id_catalogo, bool(objeto.equipado))


def _pos_evento(evento):
    #el registro guarda el montículo en su orden, así que la posición del evento es su referencia
    if evento is None or evento.pos < 0:
        return SIN_EVENTO
    return evento.pos


def _ref_actor(partida, actor):
    if actor is None:
        return REF_NINGUNO
    if actor is partida.jugador:
        return REF_JUGADOR
    return ("enemigo", actor.id_enemigo)


def _indice_efecto(efecto):
    for i in range(len(efecto.dueno.efectos)):
        if efecto.dueno.efectos[i] is efecto:
            return i
    raise ValueError("El evento apunta a un efecto que ya no está en su dueño")


def _reg_efectos(actor):
    return [EfectoReg(e.tipo, e.dano, e.fin, e.cambio_aplicado, e.cantidad, _pos_evento(e.evento))
            for e in actor.efectos]


def _salas_a_revisar(partida):
    if partida.salas is not None:
        return partida.salas.valores
    #sin vector de salas (mundos armados a mano): la sala del jugador, las conocidas y sus vecinas
    halladas = []
    candidatas = [partida.jugador.sala] + list(partida.conocidas)
    for sala in list(candidatas):
        for salida in sala.salidas:
            candidatas.append(salida.destino)
    for sala in candidatas:
        esta = False
        for h in halladas:
            if h is sala:
                esta = True
                break
        if not esta:
            halladas.append(sala)
    return ordenar(halladas, lambda s: s.id)


def _esta_tocada(sala, poblada):
    return (poblada or sala.conocimiento > DESCONOCIDA or sala.rastro is not None
            or len(sala.objetos) > 0 or len(sala.inactivos) > 0 or len(sala.trampas) > 0)


def capturar(partida):
    r = RegistroEstado()
    fabrica = partida.fabrica
    r.semilla = partida.semilla
    r.reloj = partida.reloj
    r.num_sec = partida.agenda.num_sec
    estado = partida.azar.getstate()
    r.azar_version = estado[0]
    r.azar = array("I", estado[1])
    r.azar_gauss = estado[2]
    r.acciones_jugador = partida.acciones_jugador
    r.enemigos_derrotados = partida.enemigos_derrotados
    r.terminada = partida.terminada
    r.victoria = partida.victoria
    r.abrio_puerta_salida = partida.abrio_puerta_salida
    r.retrocesos = partida.retrocesos
    r.modo_decisor = partida.decisor_cazador.modo
    r.siguiente_instancia = fabrica.siguiente_instancia if fabrica is not None else 0
    r.id_sala_salida = partida.sala_salida.id if partida.sala_salida is not None else None

    j = partida.jugador
    inv = j.inventario
    objetos = []
    cursor = None
    nodo = inv.cabeza
    while nodo is not None:
        if nodo is inv.actual:
            cursor = len(objetos)
        objetos.append(_reg_objeto(nodo.objeto))
        nodo = nodo.siguiente
    r.jugador = JugadorReg(
        j.sala.id, j.vida, j.velocidad,
        inv.arma_equipada.id_instancia if inv.arma_equipada is not None else None,
        inv.armadura_equipada.id_instancia if inv.armadura_equipada is not None else None,
        _reg_efectos(j), objetos, cursor, _pos_evento(j.evento))

    for e in partida.enemigos:
        r.enemigos.append(EnemigoReg(e.id_enemigo, e.sala.id, e.vida, e.velocidad,
                                     _reg_efectos(e), _pos_evento(e.evento)))

    trampas_con_sala = []                    #(trampa, id_sala), para resolver las referencias de la agenda
    for sala in _salas_a_revisar(partida):
        poblada = bool(fabrica.esta_poblada(sala)) if fabrica is not None else False
        if not _esta_tocada(sala, poblada):
            continue
        trampas = []
        for t in sala.trampas:
            trampas.append(TrampaReg(t.id_instancia, t.armada, _pos_evento(t.evento)))
            trampas_con_sala.append((t, sala.id))
        salidas = [SalidaReg(s.direccion, bool(s.cerrada), s.memoria) for s in sala.salidas]
        r.salas.append(SalaReg(sala.id, sala.conocimiento, sala.rastro,
                               [_reg_objeto(o) for o in sala.objetos],
                               [e.id_enemigo for e in sala.inactivos], trampas, poblada, salidas))

    for sala in partida.conocidas:
        r.conocidas.append(sala.id)

    for ev in partida.agenda.heap:
        r.agenda.append(EventoReg(ev.tiempo, ev.num_sec, ev.tipo,
                                  _ref_actor(partida, ev.dueno),
                                  _ref_datos(partida, ev.datos, trampas_con_sala)))
    return r


def _ref_datos(partida, datos, trampas_con_sala):
    if datos is None:
        return REF_NINGUNO
    if isinstance(datos, Efecto):
        return ("efecto", _ref_actor(partida, datos.dueno), _indice_efecto(datos))
    if isinstance(datos, Trampa):
        for trampa, id_sala in trampas_con_sala:
            if trampa is datos:
                return ("trampa", id_sala, datos.id_instancia)
        raise ValueError("El evento apunta a una trampa que no está en ninguna sala")
    if isinstance(datos, Salida):
        return ("salida", datos.origen.id, datos.direccion)
    raise ValueError(f"Referencia de evento desconocida: {datos!r}")


#restauración
def _vector_por_id(pares):
    #pares: lista de (id, valor); devuelve un VectorBusqueda ordenado por id
    vector = VectorBusqueda()
    for id_elemento, valor in ordenar(pares, lambda p: p[0]):
        vector.agregar(id_elemento, valor)
    vector.preparar()
    return vector


def _crear_objeto(mundo, reg):
    objeto = mundo.crear_objeto(reg.id_instancia, reg.id_catalogo)
    objeto.equipado = reg.equipado
    return objeto


def _restaurar_efectos(regs, dueno, pendientes):
    for er in regs:
        e = Efecto(er.tipo, dueno, dano=er.dano, fin=er.fin,
                   cambio_aplicado=er.cambio_aplicado, cantidad=er.cantidad)
        dueno.efectos.append(e)
        pendientes.append((e, er.evento))


def restaurar(registro, mundo):
    from model.partida_logica import Partida
    salas = mundo.salas
    jugador = mundo.crear_jugador(salas.buscar(registro.jugador.id_sala))
    id_salida = registro.id_sala_salida
    partida = Partida.__new__(Partida)
    partida._iniciar_campos(jugador, registro.semilla,
                            salas.buscar(id_salida) if id_salida is not None else None)
    partida.salas = salas
    partida.fabrica = mundo.fabrica
    partida.creador_objetos = mundo.creador_objetos
    partida.azar.setstate((registro.azar_version, tuple(registro.azar), registro.azar_gauss))
    partida.reloj = registro.reloj
    partida.acciones_jugador = registro.acciones_jugador
    partida.enemigos_derrotados = registro.enemigos_derrotados
    partida.terminada = registro.terminada
    partida.victoria = registro.victoria
    partida.abrio_puerta_salida = registro.abrio_puerta_salida
    partida.retrocesos = registro.retrocesos
    partida.decisor_cazador = DecisorCazador(registro.modo_decisor)

    pendientes = []                          #(entidad con campo `evento`, posición en la agenda)

    #jugador
    jr = registro.jugador
    jugador.vida = jr.vida
    jugador.velocidad = jr.velocidad
    inv = jugador.inventario
    for orr in jr.inventario:
        inv.agregar(_crear_objeto(mundo, orr))
    nodo = inv.cabeza
    for i in range(len(jr.inventario)):
        objeto = nodo.objeto
        if objeto.id_instancia == jr.id_arma:
            inv.arma_equipada = objeto
            jugador.ataque += objeto.ataque_bonus
        if objeto.id_instancia == jr.id_armadura:
            inv.armadura_equipada = objeto
            jugador.defensa += objeto.defensa_bonus
        if jr.cursor == i:
            inv.actual = nodo
        nodo = nodo.siguiente
    _restaurar_efectos(jr.efectos, jugador, pendientes)
    pendientes.append((jugador, jr.evento))

    #enemigos activos
    pares = []
    for er in registro.enemigos:
        e = mundo.crear_enemigo(er.id_enemigo)
        e.sala = salas.buscar(er.id_sala)
        e.vida = er.vida
        e.velocidad = er.velocidad
        _restaurar_efectos(er.efectos, e, pendientes)
        pendientes.append((e, er.evento))
        partida.enemigos.append(e)
        pares.append((er.id_enemigo, e))
    activos = _vector_por_id(pares)

    #salas tocadas
    ids_pobladas = []
    for sr in registro.salas:
        sala = salas.buscar(sr.id_sala)
        sala.conocimiento = sr.conocimiento
        sala.rastro = sr.rastro
        for orr in sr.objetos:
            sala.objetos.append(_crear_objeto(mundo, orr))
        for id_enemigo in sr.inactivos:
            e = mundo.crear_enemigo(id_enemigo)
            e.sala = sala
            sala.inactivos.append(e)
        for tr in sr.trampas:
            t = mundo.crear_trampa(tr.id_instancia)
            t.armada = tr.armada
            sala.trampas.append(t)
            pendientes.append((t, tr.evento))
        for xr in sr.salidas:
            salida = sala.salida(xr.direccion)
            salida.cerrada = xr.cerrada
            salida.memoria = xr.memoria
        if sr.poblada:
            ids_pobladas.append(sr.id_sala)

    for id_sala in registro.conocidas:
        partida.conocidas.append(salas.buscar(id_sala))

    #agenda: el montículo vuelve en el mismo orden, así que cada evento queda en su posición
    for i in range(len(registro.agenda)):
        er = registro.agenda[i]
        ev = Evento(er.tiempo, er.num_sec, er.tipo,
                    _resolver_actor(er.dueno, jugador, activos),
                    _resolver_datos(er.datos, jugador, activos, salas))
        ev.pos = i
        partida.agenda.heap.append(ev)
    partida.agenda.num_sec = registro.num_sec
    for entidad, pos in pendientes:
        entidad.evento = partida.agenda.heap[pos] if pos != SIN_EVENTO else None

    if mundo.fabrica is not None:
        mundo.fabrica.restaurar_poblacion(registro.siguiente_instancia, ids_pobladas)
    return partida


def _resolver_actor(ref, jugador, activos):
    if ref[0] == "ninguno":
        return None
    if ref[0] == "jugador":
        return jugador
    return activos.buscar(ref[1])


def _resolver_datos(ref, jugador, activos, salas):
    clase = ref[0]
    if clase == "ninguno":
        return None
    if clase == "efecto":
        return _resolver_actor(ref[1], jugador, activos).efectos[ref[2]]
    if clase == "salida":
        return salas.buscar(ref[1]).salida(ref[2])
    if clase == "trampa":
        for t in salas.buscar(ref[1]).trampas:
            if t.id_instancia == ref[2]:
                return t
    raise ValueError(f"No se pudo resolver la referencia {ref!r}")
