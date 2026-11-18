"""Constructores de criptas con llaves y oráculo independiente para las pruebas de la verificación
de resolubilidad (no es módulo de pruebas).

Solo importa de model/, dto/ y structures/. El oráculo usa listas y repite un recorrido completo
desde cero después de cada llave: sin montículo, sin vector de búsqueda, sin contadores.
"""
import random

from model.sala_logica import Sala, Salida
from structures.vector_busqueda import VectorBusqueda

DIRECCIONES = ("N", "S", "E", "O", "NE", "NO", "SE", "SO")


def _direccion_libre(sala):
    usadas = [s.direccion for s in sala.salidas]
    for d in DIRECCIONES:
        if d not in usadas:
            return d
    return None


def unir(a, b, llave=None, costo=100, cierre_automatico=None):
    """Puerta entre dos salas: dos caras enlazadas; cerradas y con la misma llave si `llave` no es None."""
    da, db = _direccion_libre(a), _direccion_libre(b)
    if da is None or db is None:
        return None
    cerrada = llave is not None
    ida = Salida(da, b, cerrada=cerrada, llave=llave, costo=costo, cierre_automatico=cierre_automatico)
    vuelta = Salida(db, a, cerrada=cerrada, llave=llave, costo=costo, cierre_automatico=cierre_automatico)
    a.agregar_salida(ida)
    b.agregar_salida(vuelta)
    ida.enlazar(vuelta)
    return ida, vuelta


def cripta(n, puertas):
    """Salas 1..n y las puertas `(a, b, llave)` (ids de sala; `llave` None = puerta abierta)."""
    salas = [Sala(i + 1, f"S{i + 1}") for i in range(n)]
    for a, b, llave in puertas:
        unir(salas[a - 1], salas[b - 1], llave)
    return salas


def armar_vector(salas):
    """Vector de búsqueda binaria de las salas, como lo arma RepositorioCripta (ids en orden creciente)."""
    vector = VectorBusqueda()
    for sala in salas:
        vector.agregar(sala.id, sala)
    vector.preparar()
    return vector


def id_llave(i):
    return f"k{i:04d}"


def cadena_de_llaves(k):
    """La llave i está en la región que abre la llave i-1; la salida está tras la llave k.

    Salas 1..k+1. La puerta entre la sala j y la j+1 se abre con la llave j, y la llave j está en la sala j.
    Devuelve (salas, id_inicial, id_salida, id_llave_salida, llaves) con llaves como tuplas (id, sala, enemigo).
    """
    puertas = [(j, j + 1, id_llave(j)) for j in range(1, k + 1)]
    salas = cripta(k + 1, puertas)
    llaves = [(id_llave(j), j, None) for j in range(1, k + 1)]
    return salas, 1, k + 1, id_llave(k), llaves


def cripta_aleatoria_con_llaves(semilla, n_salas, n_llaves):
    """Cripta sembrada con puertas cerradas, llaves en salas y en enemigos, llaves repetidas y puertas
    cuya llave falta en la lista o no existe. Devuelve (salas, id_inicial, id_salida, id_llave_salida, llaves)."""
    azar = random.Random(semilla)
    salas = [Sala(i + 1, f"S{i + 1}") for i in range(n_salas)]
    ids = [id_llave(i) for i in range(n_llaves)]

    def llave_de_puerta():
        x = azar.random()
        if x < 0.55:
            return None
        if x < 0.62:
            return "sin-lista"                      # nombrada por la puerta pero ausente de la lista
        return azar.choice(ids)

    def conectar(a, b):
        llave = llave_de_puerta()
        if llave is None and azar.random() < 0.08:
            # puerta cerrada sin llave: no se puede abrir
            par = unir(a, b)
            if par is not None:
                for cara in par:
                    cara.cerrada = True
            return
        unir(a, b, llave)

    for i in range(1, n_salas):
        conectar(salas[azar.randrange(i)], salas[i])
    for _ in range(n_salas // 2):
        a, b = azar.choice(salas), azar.choice(salas)
        if a is not b:
            conectar(a, b)
    llaves = []
    for i, nombre in enumerate(ids):
        sala = azar.randrange(1, n_salas + 1)
        enemigo = f"e{i}" if azar.random() < 0.3 else None
        llaves.append((nombre, sala, enemigo))
        if azar.random() < 0.1:                     # la misma llave listada dos veces
            llaves.append((nombre, azar.randrange(1, n_salas + 1), None))
    id_salida = azar.randrange(1, n_salas + 1)
    llave_salida = azar.choice(ids + ["sin-lista"]) if ids else "sin-lista"
    return salas, 1, id_salida, llave_salida, llaves


def barajar(salas, llaves, semilla):
    """La misma cripta con las salidas de cada sala y la lista de llaves en otro orden (las salas no se mueven)."""
    azar = random.Random(semilla)
    for sala in salas:
        azar.shuffle(sala.salidas)
        azar.shuffle(sala.entradas)
    otras = list(llaves)
    azar.shuffle(otras)
    return otras


# ---- el oráculo ---------------------------------------------------------------------------------

class Referencia:
    """Resultado del oráculo, en valores simples (mismo formato que `resumen`)."""

    def __init__(self):
        self.resoluble = False
        self.orden = []
        self.inalcanzables = []   # (id, id_sala, id_enemigo), por id
        self.frontera = []        # (id_origen, direccion, id_destino, llave), por (id_origen, direccion)
        self.ciclos = []          # lista de ciclos; cada uno, lista de (id, id_sala, id_guardia, (origen, dir, destino))


def _posicion(salas, sala):
    for i, s in enumerate(salas):
        if s is sala:
            return i
    raise ValueError("sala fuera de la cripta")


def _unicas(llaves):
    """Una entrada por id: la de menor sala (FR-002)."""
    ordenadas = sorted(llaves, key=lambda x: (x[0], x[1]))
    unicas = []
    for x in ordenadas:
        if not unicas or unicas[-1][0] != x[0]:
            unicas.append(x)
    return unicas


def _alcanzadas(salas, id_inicial, tomadas, ids_lista):
    """Recorrido completo desde cero con las llaves tomadas: lista de booleanos por posición."""
    alc = [False] * len(salas)
    for i, s in enumerate(salas):
        if s.id == id_inicial:
            alc[i] = True
    cambio = True
    while cambio:
        cambio = False
        for i, sala in enumerate(salas):
            if not alc[i]:
                continue
            for s in sala.salidas:
                j = _posicion(salas, s.destino)
                if alc[j]:
                    continue
                if not s.cerrada or (s.llave is not None and s.llave in tomadas):
                    alc[j] = True
                    cambio = True
    return alc


def resolver_referencia(salas, id_inicial, id_salida, id_llave_salida, llaves):
    """Oráculo: una pasada completa desde cero tras cada llave tomada, siempre la de menor id obtenible."""
    unicas = _unicas(llaves)
    ids_lista = [x[0] for x in unicas]
    tomadas = []
    while True:
        alc = _alcanzadas(salas, id_inicial, tomadas, ids_lista)
        obtenibles = [x for x in unicas if x[0] not in tomadas and alc[_posicion(salas, _sala_por_id(salas, x[1]))]]
        if not obtenibles:
            break
        tomadas.append(min(x[0] for x in obtenibles))
    ref = Referencia()
    ref.orden = list(tomadas)
    # solucionable: la llave de salida tomada y una salida que la exige lleva a la sala de salida desde una sala alcanzada
    if id_llave_salida in tomadas:
        for i, sala in enumerate(salas):
            if not alc[i]:
                continue
            for s in sala.salidas:
                if s.destino.id == id_salida and s.llave == id_llave_salida:
                    ref.resoluble = True
    # llaves inalcanzables: las de la lista sin tomar y las nombradas por una puerta (desde una sala alcanzada) o por la salida que la lista no da
    pendientes = [x for x in unicas if x[0] not in tomadas]
    nombradas = []
    for i, sala in enumerate(salas):
        if not alc[i]:
            continue
        for s in sala.salidas:
            if s.cerrada and s.llave is not None and s.llave not in ids_lista and s.llave not in nombradas:
                nombradas.append(s.llave)
    if id_llave_salida is not None and id_llave_salida not in ids_lista and id_llave_salida not in nombradas:
        nombradas.append(id_llave_salida)
    todas = [(x[0], x[1], x[2]) for x in pendientes] + [(n, None, None) for n in nombradas]
    ref.inalcanzables = sorted(todas, key=lambda x: x[0])
    # frontera: salidas cerradas desde salas alcanzadas hacia salas no alcanzadas
    frontera = []
    for i, sala in enumerate(salas):
        if not alc[i]:
            continue
        for s in sala.salidas:
            if s.cerrada and not alc[_posicion(salas, s.destino)]:
                frontera.append((sala.id, s.direccion, s.destino.id, s.llave))
    ref.frontera = sorted(frontera, key=lambda x: (x[0], x[1]))
    ref.ciclos = _ciclos_referencia(salas, alc, pendientes, ids_lista)
    return ref


def _sala_por_id(salas, id_sala):
    for s in salas:
        if s.id == id_sala:
            return s
    raise ValueError(f"no hay sala {id_sala}")


def _ciclos_referencia(salas, alc, pendientes, ids_lista):
    """Guardián de cada llave pendiente = la menor llave de la frontera que llega a su sala ignorando cerraduras;
    cada ciclo se cuenta una vez, desde su llave de menor id."""
    # llaves de la frontera que están en la lista (las demás no inician inundación)
    puertas = []
    for i, sala in enumerate(salas):
        if not alc[i]:
            continue
        for s in sala.salidas:
            if s.cerrada and s.llave in ids_lista and not alc[_posicion(salas, s.destino)]:
                puertas.append((s.llave, sala.id, s.direccion, s))
    puertas.sort(key=lambda x: (x[0], x[1], x[2]))
    etiqueta = [None] * len(salas)           # (llave, (origen, dir, destino))
    for llave, id_origen, direccion, s in puertas:
        alcance = [False] * len(salas)
        j0 = _posicion(salas, s.destino)
        alcance[j0] = True
        cambio = True
        while cambio:
            cambio = False
            for i, sala in enumerate(salas):
                if not alcance[i]:
                    continue
                for t in sala.salidas:
                    j = _posicion(salas, t.destino)
                    if not alc[j] and not alcance[j]:
                        alcance[j] = True
                        cambio = True
        for i in range(len(salas)):
            if alcance[i] and etiqueta[i] is None:
                etiqueta[i] = (llave, (id_origen, direccion, s.destino.id))
    pend = sorted(pendientes, key=lambda x: x[0])

    def guardia(x):
        e = etiqueta[_posicion(salas, _sala_por_id(salas, x[1]))]
        return e

    visita = [None] * len(pend)
    ciclos = []
    for a in range(len(pend)):
        if visita[a] is not None:
            continue
        camino = []
        actual = a
        while actual is not None and visita[actual] is None:
            visita[actual] = pend[a][0]
            camino.append(actual)
            e = guardia(pend[actual])
            actual = None
            if e is not None:
                for k in range(len(pend)):
                    if pend[k][0] == e[0]:
                        actual = k
        if actual is not None and visita[actual] == pend[a][0]:
            ciclo = camino[camino.index(actual):]
            inicio = ciclo.index(min(ciclo, key=lambda k: pend[k][0]))
            ciclo = ciclo[inicio:] + ciclo[:inicio]
            eslabones = []
            for k in ciclo:
                e = guardia(pend[k])
                eslabones.append((pend[k][0], pend[k][1], e[0], e[1]))
            ciclos.append(eslabones)
    return sorted(ciclos, key=lambda c: c[0][0])


def resumen(resultado):
    """Pasa un ResultadoVerificacion del modelo a valores simples, con el formato de `Referencia`."""
    ref = Referencia()
    ref.resoluble = resultado.resoluble
    ref.orden = list(resultado.orden)
    ref.inalcanzables = [(k.id, k.id_sala, k.id_enemigo) for k in resultado.inalcanzables]
    ref.frontera = [(s.origen.id, s.direccion, s.destino.id, s.llave) for s in resultado.frontera]
    ref.ciclos = [[(e.id_llave, e.id_sala, e.id_guardia, (e.puerta.origen.id, e.puerta.direccion, e.puerta.destino.id))
                   for e in ciclo] for ciclo in resultado.ciclos]
    return ref


def logicas(llaves):
    """Tuplas (id, sala, enemigo) → LlaveLogica (se importa aquí para poder escribir las pruebas antes del modelo)."""
    from model.solvabilidad_logica import LlaveLogica
    return [LlaveLogica(i, s, e) for i, s, e in llaves]
