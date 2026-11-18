"""Registro de acciones y puntos de control durante el juego (spec 005, Fase 3, US6).

Todo con datos falsos y sin red: el cliente falso falla ante cualquier llamada.
"""
import random
import tracemalloc

import pytest

from controller.controlador import Controlador
from dto.contenido_sala_dto import InstanciaEnemigoDTO
from linea_tiempo_apoyo import VistaMuda, armar_mundo, jugar_semilla
from model.linea_tiempo_logica import K_POR_DEFECTO, LineaTiempoPartida
from model.registro_estado import restaurar
from service.juego_service import JuegoService
from structures.linea_tiempo import LineaTiempo

TIPOS = ("mover", "esperar", "atacar", "recoger", "soltar", "equipar", "usar", "abrir")


def _armar(semilla=1, k=3, salas=5, enemigos=0, cazadores=0, con_pergaminos=False, vida=5000):
    """Un mundo con su línea de tiempo activa: devuelve (mundo, servicio, controlador, linea)."""
    mundo = armar_mundo(semilla, salas=salas, enemigos=enemigos, cazadores=cazadores,
                        con_pergaminos=con_pergaminos, vida_jugador=vida)
    linea = LineaTiempoPartida()
    linea.iniciar(mundo.partida, mundo.constructor, k)
    servicio = JuegoService(mundo.partida, mundo.fabrica, linea_tiempo=linea)
    controlador = Controlador(servicio, VistaMuda(), None, None)
    return mundo, servicio, controlador, linea


def _poner_cursor(controlador, servicio, id_instancia):
    for _ in range(20):
        for o in servicio.inventario_vista().objetos:
            if o.actual and o.id_instancia == id_instancia:
                return
        controlador.ejecutar("sig")
    raise AssertionError(f"el objeto {id_instancia} no está en el inventario")


def _bajo_el_cursor(servicio):
    for o in servicio.inventario_vista().objetos:
        if o.actual:
            return o.id_instancia
    return None


def test_cada_accion_exitosa_queda_con_su_reloj_y_su_objetivo_resuelto():
    """FR-003, FR-006 · US6-1 · tipo, reloj de la decisión y argumento resuelto de cada acción"""
    mundo, servicio, c, linea = _armar(k=50)
    mundo.contenidos[1].enemigos.append(InstanciaEnemigoDTO("x1", "rata", None))
    p = mundo.partida
    esperadas = []                                        #(reloj antes, tipo, argumento)

    def hacer(comando, tipo=None, argumento=None):
        reloj = p.reloj
        c.ejecutar(comando)
        if tipo is not None:
            esperadas.append((reloj, tipo, argumento))

    for objeto in (2, 4, 6):                              #espada, poción de vida, antídoto
        hacer(f"recoger {objeto}", "recoger", objeto)
    _poner_cursor(c, servicio, 2)                         #`sig` mueve el cursor y no deja registro
    hacer("equipar", "equipar", 2)
    _poner_cursor(c, servicio, 4)
    assert _bajo_el_cursor(servicio) == 4
    hacer("usar", "usar", 4)                              #usar con el cursor movido por sig
    hacer("ant")
    esperado_soltar = _bajo_el_cursor(servicio)
    hacer("soltar", "soltar", esperado_soltar)            #soltar con el cursor movido por ant
    hacer("recoger 1", "recoger", 1)                      #la llave, para abrir la puerta de la sala 2
    hacer("esperar", "esperar", None)
    hacer("w", "mover", "N")                              #a la sala 2, que tiene una sola rata
    hacer("atacar", "atacar", "x1")                       #sin id: el único enemigo de la sala
    hacer("abrir w", "abrir", "N")                        #la puerta forzada, con la llave del inventario
    assert [e[1] for e in esperadas].count("mover") == 1

    assert len(linea.relojes) == len(esperadas) == p.acciones_jugador
    for i, (reloj, tipo, argumento) in enumerate(esperadas):
        assert linea.relojes[i] == reloj, f"reloj de la acción {i + 1}"
        assert linea.tipos[i] == tipo, f"tipo de la acción {i + 1}"
        assert linea.tipos[i] in TIPOS
        assert linea.argumentos[i] == argumento, f"argumento de la acción {i + 1}"
    for i in range(1, len(linea.relojes)):
        assert linea.relojes[i] > linea.relojes[i - 1]    #estrictamente crecientes


def test_lo_que_no_es_una_accion_no_deja_registro():
    """FR-006, FR-003 · US6-1 · fallos y consultas no agregan; `ir a` agrega un `mover` por paso"""
    mundo, servicio, c, linea = _armar(k=50, con_pergaminos=True)
    p = mundo.partida
    salidas = [s.direccion for s in servicio.estado_vista().salidas]
    pared = [t for d, t in (("N", "w"), ("S", "s"), ("E", "d"), ("O", "a")) if d not in salidas][0]

    def sin_registro(comando):
        antes = (len(linea), p.acciones_jugador, p.reloj)
        c.ejecutar(comando)
        assert (len(linea), p.acciones_jugador, p.reloj) == antes, comando

    for comando in (pared, f"abrir {pared}", "recoger 999", "usar", "soltar", "equipar", "atacar",
                    "mapa", "inv", "sig", "ant", "xyzzy", "retroceder", "ir a 4", "ir", "inv nombre"):
        sin_registro(comando)
    assert len(linea) == 0

    for numero in range(1, 9):                            #ocho objetos: el inventario queda lleno
        c.ejecutar(f"recoger {numero}")
    assert len(linea) == 8
    sin_registro("recoger 9")                             #inventario lleno

    c.ejecutar("w")                                       #sala 2
    sin_registro("w")                                     #la puerta de la sala 2 está cerrada
    assert len(linea) == 9
    antes = len(linea)
    c.ejecutar("ir a 1")                                  #de vuelta a la sala 1: un paso
    assert len(linea) == antes + 1
    assert (linea.tipos[-1], linea.argumentos[-1]) == ("mover", "S")


def test_abrir_sin_llave_no_deja_registro():
    """FR-006 · US6-1 · sin llave la puerta no se abre y no se registra nada"""
    mundo, servicio, c, linea = _armar(k=50)
    c.ejecutar("w")                                       #sala 2: la puerta del norte es forzada
    assert len(linea) == 1
    c.ejecutar("abrir w")
    c.ejecutar("w")
    assert len(linea) == 1


@pytest.mark.parametrize("k", [1, 3, 7, 1000])
def test_un_punto_de_control_cada_k_acciones(k):
    """FR-019 · US6-1 · el punto 0 existe antes de toda acción y hay uno exacto cada K acciones"""
    mundo, servicio, c, linea = _armar(semilla=3, k=k, salas=7, enemigos=4, cazadores=1)
    p = mundo.partida
    assert len(linea.puntos) == 1
    assert linea.puntos[0].acciones_jugador == 0
    assert linea.puntos[0].reloj == p.reloj
    comprobadas = []

    def despues(comando):
        acciones = p.acciones_jugador
        assert len(linea) == acciones
        assert len(linea.puntos) == acciones // k + 1, (comando, acciones)
        assert len(linea.puntos) <= acciones // k + 1
        for i, punto in enumerate(linea.puntos):
            assert punto.acciones_jugador == i * k
        comprobadas.append(acciones)

    jugar_semilla(servicio, 5, 120, despues=despues)
    assert comprobadas and comprobadas[-1] > 30


def test_el_k_por_defecto_es_un_entero_positivo():
    """FR-019 · el juego arranca sin la opción con el K por defecto"""
    assert type(K_POR_DEFECTO) is int and K_POR_DEFECTO > 0
    mundo = armar_mundo(1)
    linea = LineaTiempoPartida()
    linea.iniciar(mundo.partida, mundo.constructor, None)
    assert linea.linea.k == K_POR_DEFECTO


class _AzarEspia(random.Random):
    """Anota cada número que el juego saca, para poder volver a sacarlos desde el punto de control."""

    def __init__(self):
        super().__init__()
        self.registro = []

    def getrandbits(self, k):
        valor = super().getrandbits(k)
        self.registro.append(("bits", k, valor))
        return valor

    def random(self):
        valor = super().random()
        self.registro.append(("random", 0, valor))
        return valor


def test_cada_punto_guarda_el_azar_y_restaurarlo_da_los_mismos_numeros():
    """FR-023 · US6-5 · el estado del generador está en el punto y vuelve a dar lo que el juego sacó"""
    mundo = armar_mundo(2, salas=7, enemigos=5, cazadores=2, vida_jugador=5000)
    espia = _AzarEspia()
    espia.setstate(mundo.partida.azar.getstate())
    mundo.partida.azar = espia
    linea = LineaTiempoPartida()
    linea.iniciar(mundo.partida, mundo.constructor, 3)
    servicio = JuegoService(mundo.partida, mundo.fabrica, linea_tiempo=linea)
    p = mundo.partida
    vistos = []                                           #(acciones, estado vivo, cuántos números llevaba)

    def despues(comando):
        if p.acciones_jugador % 3 == 0 and (not vistos or vistos[-1][0] != p.acciones_jugador):
            vistos.append((p.acciones_jugador, p.azar.getstate(), len(espia.registro)))

    jugar_semilla(servicio, 11, 90, despues=despues)
    assert len(vistos) >= 4
    for acciones, estado, llevaba in vistos:
        punto = linea.linea.punto_para(acciones)
        assert (punto.azar_version, tuple(punto.azar), punto.azar_gauss) == estado
    #lo que el juego sacó entre dos puntos de control se repite desde el primero de ellos
    for i in range(len(vistos) - 1):
        if vistos[i + 1][2] > vistos[i][2]:
            break
    else:
        raise AssertionError("el juego tuvo que sacar números entre dos puntos")
    acciones, estado, llevaba = vistos[i]
    sacados = espia.registro[llevaba:vistos[i + 1][2]]
    punto = linea.linea.punto_para(acciones)
    otro = random.Random()
    otro.setstate((punto.azar_version, tuple(punto.azar), punto.azar_gauss))
    for clase, bits, valor in sacados:
        assert (otro.getrandbits(bits) if clase == "bits" else otro.random()) == valor


def test_un_punto_de_control_se_puede_restaurar_en_un_grafo_nuevo():
    """FR-023 · un punto guardado por el juego es un registro completo y no cambia después"""
    mundo, servicio, c, linea = _armar(semilla=4, k=4, salas=6, enemigos=3, cazadores=1)
    jugar_semilla(servicio, 9, 40)
    assert len(linea.puntos) >= 3
    punto = linea.puntos[2]
    copia = restaurar(punto, mundo.nuevo_mundo())
    assert copia.acciones_jugador == 8
    jugar_semilla(servicio, 10, 30)                       #seguir jugando no cambia el punto
    assert restaurar(punto, mundo.nuevo_mundo()).reloj == copia.reloj


def _memoria_de_la_linea(semilla, comandos, k):
    """Bytes que quedan vivos y salieron de la línea de tiempo sola (no del juego)."""
    tracemalloc.start()
    try:
        mundo = armar_mundo(semilla, salas=9, enemigos=3, cazadores=1, vida_jugador=10 ** 6)
        mundo.partida.sala_salida = None                  #sin victoria: el juego sigue y lo tocado se agota
        linea = LineaTiempoPartida()
        linea.iniciar(mundo.partida, mundo.constructor, k)
        servicio = JuegoService(mundo.partida, mundo.fabrica, linea_tiempo=linea)
        jugar_semilla(servicio, semilla, comandos)
        instantanea = tracemalloc.take_snapshot()
        acciones = len(linea.linea)
    finally:
        tracemalloc.stop()
    filtros = [tracemalloc.Filter(True, "*registro_estado.py"),
               tracemalloc.Filter(True, "*" + "linea_tiempo.py"),
               tracemalloc.Filter(True, "*linea_tiempo_logica.py")]
    total = 0
    for estadistica in instantanea.filter_traces(filtros).statistics("filename"):
        total += estadistica.size
    return total, acciones


def test_la_memoria_crece_con_las_acciones_y_no_con_acciones_por_estado():
    """FR-021 · US6-3 · el doble de acciones con K fijo es entre 1.5 y 2.5 veces la memoria"""
    corta, acciones_cortas = _memoria_de_la_linea(21, 600, 10)
    larga, acciones_largas = _memoria_de_la_linea(21, 1200, 10)
    assert 1.7 <= acciones_largas / acciones_cortas <= 2.3        #la premisa: el doble de acciones
    razon = larga / corta
    assert 1.5 <= razon <= 2.5, f"razón de memoria {razon:.2f} con {acciones_cortas} y {acciones_largas} acciones"


def test_una_partida_terminada_deja_de_registrar_y_guarda_el_reloj_final():
    """FR-002 · una partida que termina (muerte) conserva `reloj_final` y no sigue registrando"""
    mundo, servicio, c, linea = _armar(k=5, vida=4)
    p = mundo.partida
    c.ejecutar("w")                                       #sala 2: trampa de veneno con 4 de vida
    for _ in range(300):
        if p.terminada:
            break
        c.ejecutar("esperar")
    assert p.terminada and not p.victoria
    registradas = len(linea)
    assert registradas == p.acciones_jugador
    assert linea.reloj_final == p.reloj
    c.ejecutar("esperar")
    c.ejecutar("w")
    assert len(linea) == registradas
    assert linea.reloj_final == p.reloj


def test_sin_linea_de_tiempo_el_servicio_funciona_igual():
    """FR-006 · el servicio sin línea de tiempo (por defecto) no cambia nada de la parte uno"""
    mundo = armar_mundo(1)
    servicio = JuegoService(mundo.partida, mundo.fabrica)
    assert servicio.linea_tiempo is None
    c = Controlador(servicio, VistaMuda(), None, None)
    c.ejecutar("recoger 1")
    c.ejecutar("w")
    assert mundo.partida.acciones_jugador == 2


def test_el_punto_para_cada_frontera_es_la_casilla_y_deja_menos_de_k_acciones():
    """FR-020, FR-022 · US6-2, US6-4 · 3 000 acciones sintéticas: casilla `frontera // K`, sin recorrer"""
    for k in (1, 7, 50, 200):
        linea = LineaTiempo(k)
        for i in range(3001):
            if i % k == 0:
                linea.agregar_punto(("punto", i))
            if i < 3000:
                linea.agregar_accion(i * 10 + 3, "esperar")
        assert len(linea.puntos) == 3000 // k + 1
        antes = linea.comparaciones
        for frontera in range(3001):
            punto = linea.punto_para(frontera)
            assert punto == ("punto", (frontera // k) * k)
            assert 0 <= frontera - punto[1] <= k - 1      #acciones por reproducir desde ese punto
        assert linea.comparaciones == antes               #buscar el punto no recorre ni compara relojes
