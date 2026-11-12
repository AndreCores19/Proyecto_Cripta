import random

import pytest

from model.enemigo_logica import Enemigo
from model.jugador_logica import Jugador
from model.objeto_logica import Objeto
from model.partida_logica import Partida
from model.ruta_cazador import Busqueda, DecisorCazador, MODOS
from model.sala_logica import Sala, Salida
from tests.mapas_cazador import (cadena, cripta_aleatoria, decision_referencia,
                                 distancias_referencia)

RANGOS = (0, 100, 300, 1000)


def test_oraculo_cadena_100_150():
    """FR-003, FR-011 · el oráculo da 0, 150 y 250 con el jugador al final de la cadena."""
    salas, _ = cadena([100, 150])
    dist = distancias_referencia(salas, salas[2])
    assert dist == [250, 150, 0]


def test_oraculo_cadena_jugador_al_inicio():
    """FR-003, FR-011 · con el jugador en la primera sala: 0, 100 y 250."""
    salas, _ = cadena([100, 150])
    assert distancias_referencia(salas, salas[0]) == [0, 100, 250]


# ---- ayudas ---------------------------------------------------------------

def nueva_partida(sala_jugador, modo):
    jugador = Jugador(vida_max=10**6, ataque=10, defensa=10**6, velocidad=100,
                      inventario_max=10, sala=sala_jugador)
    partida = Partida(jugador, semilla=1)
    partida.decisor_cazador = DecisorCazador(modo)
    return partida


def nuevo_cazador(partida, sala, rango, id_enemigo=1):
    h = Enemigo(id_enemigo, "cazador", f"h{id_enemigo}", 10, 10, 5, 0, 100,
                "cazador", sala, rango=rango)
    partida.activar_enemigo(h)
    partida.agenda.cancelar(h.evento)
    partida.reloj = 1000
    return h


def turno(partida, h):
    partida.agenda.cancelar(h.evento)
    partida._actuar_enemigo(h)


def decidir_y_comparar(partida, salas, h):
    """La decisión del modo bajo prueba es la del oráculo (misma salida o None)."""
    esperada = decision_referencia(salas, partida.jugador.sala, h)
    obtenida = partida.decisor_cazador.decidir(partida, h)
    assert obtenida is esperada
    return obtenida


def _sala(i):
    return Sala(i, f"S{i}")


def _unir(x, dx, y, dy, costo):
    i, v = Salida(dx, y, costo=costo), Salida(dy, x, costo=costo)
    x.agregar_salida(i)
    y.agregar_salida(v)
    i.enlazar(v)
    return i, v


def _con_alternativa():
    """A–B–C (100, 100) y A–D–C (150, 150)."""
    a, b, c, d = _sala(1), _sala(2), _sala(3), _sala(4)
    _unir(a, "E", b, "O", 100)
    pbc = _unir(b, "E", c, "O", 100)
    _unir(a, "S", d, "N", 150)
    _unir(d, "E", c, "S", 150)
    return [a, b, c, d], pbc


# ---- US3: escenarios ------------------------------------------------------

@pytest.mark.parametrize("modo", MODOS)
def test_us3_1_puerta_de_la_ruta_se_cierra_y_hay_alternativa(modo):
    """FR-011, FR-012 · US3-1"""
    salas, pbc = _con_alternativa()
    a, b, c, d = salas
    partida = nueva_partida(c, modo)
    h = nuevo_cazador(partida, a, 1000)
    decidir_y_comparar(partida, salas, h)
    turno(partida, h)
    assert h.sala is b
    partida._poner_cerrada(pbc[0], True)
    h.sala = a
    assert decidir_y_comparar(partida, salas, h).destino is d
    turno(partida, h)
    assert h.sala is d


@pytest.mark.parametrize("modo", MODOS)
def test_us3_1_puerta_de_la_ruta_se_cierra_sin_alternativa(modo):
    """FR-011, FR-012 · US3-1: sin otra ruta el cazador espera."""
    salas, pares = cadena([100, 100])
    partida = nueva_partida(salas[2], modo)
    h = nuevo_cazador(partida, salas[0], 1000)
    decidir_y_comparar(partida, salas, h)
    turno(partida, h)
    assert h.sala is salas[1]
    partida._poner_cerrada(pares[1][0], True)
    assert decidir_y_comparar(partida, salas, h) is None
    turno(partida, h)
    assert h.sala is salas[1]


@pytest.mark.parametrize("modo", MODOS)
def test_us3_2_la_puerta_se_abre_y_el_cazador_avanza(modo):
    """FR-011, FR-012 · US3-2"""
    salas, pares = cadena([100, 100])
    for cara in pares[0]:
        cara.cerrada = True
    partida = nueva_partida(salas[2], modo)
    h = nuevo_cazador(partida, salas[0], 1000)
    assert decidir_y_comparar(partida, salas, h) is None
    turno(partida, h)
    assert h.sala is salas[0]
    partida._poner_cerrada(pares[0][0], False)
    assert decidir_y_comparar(partida, salas, h) is pares[0][0]
    turno(partida, h)
    assert h.sala is salas[1]


@pytest.mark.parametrize("modo", MODOS)
def test_us3_3_el_jugador_cambia_de_sala(modo):
    """FR-011, FR-012 · US3-3: tras un paso hacia C el jugador se va a D y la decisión usa D."""
    salas, _ = cadena([100, 100, 100])
    a, b, c, d = salas
    partida = nueva_partida(c, modo)
    h = nuevo_cazador(partida, a, 1000)
    decidir_y_comparar(partida, salas, h)
    turno(partida, h)
    assert h.sala is b
    partida.agenda.cancelar(h.evento)
    assert partida.mover("E")
    assert partida.jugador.sala is d
    assert decidir_y_comparar(partida, salas, h).destino is c


@pytest.mark.parametrize("modo", MODOS)
def test_us3_4_un_errante_muere_entre_dos_turnos(modo):
    """FR-011 · US3-4: la decisión es la de un cazador nuevo e idéntico en el mismo estado."""
    salas, _ = cadena([100, 100])
    partida = nueva_partida(salas[2], modo)
    h = nuevo_cazador(partida, salas[0], 1000)
    w = Enemigo(50, "errante", "w", 1, 1, 1, 0, 100, "errante", salas[2])
    partida.activar_enemigo(w)
    decidir_y_comparar(partida, salas, h)
    assert partida.atacar(w)
    assert w not in partida.enemigos
    nuevo = Enemigo(2, "cazador", "h2", 10, 10, 5, 0, 100, "cazador", salas[0], rango=1000)
    esperada = decidir_y_comparar(partida, salas, h)
    assert DecisorCazador(modo).decidir(partida, nuevo) is esperada


@pytest.mark.parametrize("modo", MODOS)
def test_us3_5_cierre_automatico_de_una_puerta_de_la_ruta(modo):
    """FR-011, FR-012 · US3-5"""
    salas, pares = cadena([100])
    c, d = salas
    ida, vuelta = pares[0]
    for cara in (ida, vuelta):
        cara.cerrada = True
        cara.llave = "llave1"
        cara.cierre_automatico = 100
    partida = nueva_partida(c, modo)
    partida.jugador.inventario.agregar(Objeto(1, "llave1", "Llave", "llave", 1, 1))
    h = nuevo_cazador(partida, d, 1000)
    assert decidir_y_comparar(partida, salas, h) is None
    assert partida.abrir_puerta("E")
    assert not ida.cerrada
    assert decidir_y_comparar(partida, salas, h) is vuelta
    for _ in range(5):
        if ida.cerrada:
            break
        partida.esperar_jugador()
    assert ida.cerrada
    assert decidir_y_comparar(partida, salas, h) is None


# ---- US3: comparación aleatoria con semilla -------------------------------

def armar_juego(semilla, modo, aislado=True):
    salas = cripta_aleatoria(semilla, 40)
    azar = random.Random(semilla * 7919 + 13)
    jugador = Jugador(vida_max=10**6, ataque=10, defensa=10**6, velocidad=100,
                      inventario_max=10, sala=azar.choice(salas))
    partida = Partida(jugador, semilla=semilla)
    partida.decisor_cazador = DecisorCazador(modo)
    cazadores = [Enemigo(i + 1, "cazador", f"h{i}", 10, 10, 5, 0, 100, "cazador",
                         azar.choice(salas), rango=azar.choice(RANGOS)) for i in range(6)]
    errantes = [Enemigo(101 + i, "errante", f"w{i}", 1, 1, 1, 0, 100, "errante",
                        azar.choice(salas)) for i in range(4)]
    for e in cazadores + errantes:
        partida.activar_enemigo(e)
        if aislado:
            partida.agenda.cancelar(e.evento)
    return partida, salas, cazadores, errantes


def sortear_paso(azar, partida, salas):
    r = azar.random()
    if 0.35 <= r < 0.7:
        sala = partida.jugador.sala
        abiertas = [s for s in sala.salidas if not s.cerrada]
        if abiertas:
            return ("mover", sala.id, azar.choice(abiertas).direccion)
    elif r >= 0.85 and len(partida.historial) > 0:
        return ("retroceder", 0, "")
    elif 0.7 <= r < 0.85:
        return ("quitar", azar.choice(salas).id, "")
    while True:
        sala = azar.choice(salas)
        if sala.salidas:
            return ("puerta", sala.id, azar.choice(sala.salidas).direccion)


def aplicar_paso(partida, salas, paso):
    tipo, id_sala, direccion = paso
    sala = salas[id_sala - 1]
    if tipo == "puerta":
        salida = sala.salida(direccion)
        partida._poner_cerrada(salida, not salida.cerrada)
    elif tipo == "mover":
        assert partida.mover(direccion)
    elif tipo == "quitar":
        vivos = [e for e in partida.enemigos
                 if e.comportamiento == "errante" and e.sala is sala]
        if vivos:
            w = min(vivos, key=lambda e: e.id_enemigo)
            partida.agenda.cancelar(w.evento)
            partida.historial.lista_quitar(partida.enemigos, w)
    else:
        partida.retroceder()


def instantanea_puertas(salas):
    return [s.cerrada for sala in salas for s in sala.salidas]


def resumen(partida, salas, actores):
    lineas = [f"reloj {partida.reloj}", f"acciones {partida.acciones_jugador}",
              f"jugador {partida.jugador.sala.id} {partida.jugador.vida}"]
    for e in sorted(actores, key=lambda e: e.id_enemigo):
        lineas.append(f"{e.id_enemigo} {e.sala.id} {e.vida}")
    for sala in salas:
        for s in sorted(sala.salidas, key=lambda s: s.direccion):
            lineas.append(f"{sala.id}{s.direccion} {int(s.cerrada)}")
    return "\n".join(lineas)


def jugar_aislado(semilla, modo, reproducir=None, mezclar=False):
    partida, salas, cazadores, errantes = armar_juego(semilla, modo)
    if mezclar:
        mezcla = random.Random(semilla + 1000)
        for sala in salas:
            mezcla.shuffle(sala.salidas)
            mezcla.shuffle(sala.entradas)
    azar = random.Random(semilla)
    pasos, decisiones = [], []
    for k in range(200):
        paso = reproducir[0][k] if reproducir else sortear_paso(azar, partida, salas)
        aplicar_paso(partida, salas, paso)
        pasos.append(paso)
        del_paso = []
        dist = distancias_referencia(salas, partida.jugador.sala)  #el mismo estado para los 6 cazadores
        for h in cazadores:
            if h.sala is partida.jugador.sala:
                del_paso.append(("aqui",))
            else:
                salida = partida.decisor_cazador.decidir(partida, h)
                if reproducir is None:
                    assert salida is decision_referencia(salas, partida.jugador.sala, h, dist), (semilla, k)
                del_paso.append(None if salida is None else (salida.destino.id, salida.direccion))
            antes = instantanea_puertas(salas)
            partida.agenda.cancelar(h.evento)
            partida._actuar_enemigo(h)
            partida.agenda.cancelar(h.evento)  #solo el paso de la prueba mueve al cazador (mantiene rápida la prueba)
            assert instantanea_puertas(salas) == antes, "un cazador tocó una puerta"
        decisiones.append(del_paso)
        if reproducir:
            assert del_paso == reproducir[1][k], (semilla, k)
    return resumen(partida, salas, cazadores + errantes), pasos, decisiones


@pytest.mark.parametrize("modo", MODOS)
def test_us3_comparacion_aleatoria_con_el_oraculo_y_reproduccion(modo):
    """FR-011, FR-012, FR-009, FR-007 · SC-002, SC-003; Constitución II (el orden de las listas no importa)"""
    for semilla in range(1, 21):
        final, pasos, decisiones = jugar_aislado(semilla, modo)
        final2, _, _ = jugar_aislado(semilla, modo, reproducir=(pasos, decisiones), mezclar=True)
        assert final2 == final, semilla


# ---- US3: reglas de la caché del modo compartido --------------------------

def _busquedas():
    return Busqueda.busquedas


def test_cache_cazador_con_rango_mayor_recalcula():
    """FR-011, FR-018 · un cazador con rango mayor al de la caché fuerza una búsqueda nueva."""
    salas, _ = cadena([100, 100, 100])
    partida = nueva_partida(salas[3], "compartido")
    h1 = nuevo_cazador(partida, salas[1], 100, 1)
    decidir_y_comparar(partida, salas, h1)
    h2 = nuevo_cazador(partida, salas[0], 500, 2)
    antes = _busquedas()
    decidir_y_comparar(partida, salas, h2)
    assert _busquedas() == antes + 1


def test_cache_cazador_con_rango_menor_o_igual_reutiliza():
    """FR-011, FR-018 · con rango menor o igual no hay búsqueda nueva."""
    salas, _ = cadena([100, 100, 100])
    partida = nueva_partida(salas[3], "compartido")
    grande = nuevo_cazador(partida, salas[0], 500, 1)
    chico = nuevo_cazador(partida, salas[1], 100, 2)
    igual = nuevo_cazador(partida, salas[2], 500, 3)
    decidir_y_comparar(partida, salas, grande)
    antes = _busquedas()
    decidir_y_comparar(partida, salas, chico)
    decidir_y_comparar(partida, salas, igual)
    assert _busquedas() == antes


def test_decidir_falla_si_el_limite_forzado_es_menor_que_el_rango():
    """FR-011, FR-018"""
    salas, _ = cadena([100, 100])
    partida = nueva_partida(salas[2], "compartido")
    h = nuevo_cazador(partida, salas[0], 300)
    with pytest.raises(RuntimeError):
        partida.decisor_cazador.decidir(partida, h, limite_forzado=h.rango - 1)


def test_cache_busqueda_ajena_entre_dos_turnos():
    """FR-011 · otra búsqueda sobrescribe los campos de las salas: se recalcula (condición 4)."""
    salas, _ = cadena([100, 100, 100])
    partida = nueva_partida(salas[3], "compartido")
    h = nuevo_cazador(partida, salas[0], 1000)
    decidir_y_comparar(partida, salas, h)
    Busqueda().calcular(salas[0], 500)
    antes = _busquedas()
    decidir_y_comparar(partida, salas, h)
    assert _busquedas() == antes + 1


def test_cache_retroceso_invalida():
    """FR-011 · retroceder entre dos turnos no deja pasar una caché vieja."""
    salas, pares = cadena([100, 100, 100])
    partida = nueva_partida(salas[3], "compartido")
    h = nuevo_cazador(partida, salas[0], 1000)
    decidir_y_comparar(partida, salas, h)
    assert partida.mover("O")
    decidir_y_comparar(partida, salas, h)
    assert partida.retroceder()
    antes = _busquedas()
    decidir_y_comparar(partida, salas, h)
    assert _busquedas() == antes + 1


def test_cache_retroceso_que_deshace_una_puerta_invalida():
    """FR-011 · retroceder una apertura de puerta cambia la época y la caché se recalcula."""
    salas, pares = cadena([100, 100])
    for cara in pares[0]:
        cara.cerrada = True
        cara.llave = "k"
    partida = nueva_partida(salas[1], "compartido")
    partida.jugador.inventario.agregar(Objeto(1, "k", "Llave", "llave", 1, 1))
    h = nuevo_cazador(partida, salas[0], 1000)
    assert decidir_y_comparar(partida, salas, h) is None
    assert partida.abrir_puerta("O")
    assert decidir_y_comparar(partida, salas, h) is not None
    assert partida.retroceder()
    antes = _busquedas()
    assert decidir_y_comparar(partida, salas, h) is None
    assert _busquedas() == antes + 1


@pytest.mark.parametrize("modo,nuevas", [("individual", 1), ("compartido_sin_reuso", 1), ("compartido", 0)])
def test_cache_sin_cambios_entre_dos_turnos(modo, nuevas):
    """FR-011, FR-018 · sin cambios, solo `compartido` evita la búsqueda."""
    salas, _ = cadena([100, 100])
    partida = nueva_partida(salas[2], modo)
    h = nuevo_cazador(partida, salas[0], 1000)
    decidir_y_comparar(partida, salas, h)
    antes = _busquedas()
    decidir_y_comparar(partida, salas, h)
    assert _busquedas() == antes + nuevas


def test_modo_desconocido_falla():
    """FR-011 · un nombre de modo desconocido es un error."""
    with pytest.raises(ValueError):
        DecisorCazador("otro")


# ---- US3: determinismo ----------------------------------------------------

def jugar_completo(semilla, modo):
    partida, salas, cazadores, errantes = armar_juego(semilla, modo, aislado=False)
    azar = random.Random(semilla + 5)
    for k in range(300):
        sala = partida.jugador.sala
        abiertas = sorted((s for s in sala.salidas if not s.cerrada), key=lambda s: s.direccion)
        if k % 5 == 4 or not abiertas:
            partida.esperar_jugador()
        elif k % 7 == 3:
            s = azar.choice(sorted(sala.salidas, key=lambda s: s.direccion))
            partida._poner_cerrada(s, not s.cerrada)
        else:
            partida.mover(azar.choice(abiertas).direccion)
        if partida.terminada:
            break
    return resumen(partida, salas, cazadores + errantes)


@pytest.mark.parametrize("semilla", [1, 2, 3])
def test_determinismo_de_los_modos(semilla):
    """FR-014 · SC-005: dos corridas iguales y los tres modos dan el mismo estado final."""
    finales = []
    for modo in MODOS:
        uno = jugar_completo(semilla, modo)
        assert uno == jugar_completo(semilla, modo)
        finales.append(uno)
    assert finales[0] == finales[1] == finales[2]
