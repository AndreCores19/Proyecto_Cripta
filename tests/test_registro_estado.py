from array import array

import pytest

from controller.controlador import Controlador
from data.repositorio_cripta import RepositorioCripta, construir_grafo
from linea_tiempo_apoyo import VistaMuda, armar_mundo, jugar_semilla, resumen_plano
from model.jugador_logica import Jugador
from model.partida_logica import Partida
from model.registro_estado import RegistroEstado, capturar, restaurar
from model.sala_logica import Sala, Salida
from model.trampa_logica import Trampa


def _volcado(valor):
    """Convierte un registro en tuplas y valores simples para compararlo antes y después."""
    if isinstance(valor, (int, float, str, bool, type(None))):
        return valor
    if isinstance(valor, array):
        return ("array", valor.typecode, tuple(valor))
    if isinstance(valor, (list, tuple)):
        return tuple(_volcado(v) for v in valor)
    campos = getattr(valor, "__slots__", None)
    if campos is None:
        campos = list(vars(valor))
    return (type(valor).__name__,) + tuple((c, _volcado(getattr(valor, c))) for c in campos)


def _tipos_en(valor, hallados):
    hallados.append(type(valor))
    if isinstance(valor, (list, tuple)):
        for v in valor:
            _tipos_en(v, hallados)
    elif not isinstance(valor, (int, float, str, bool, type(None), array)):
        campos = getattr(valor, "__slots__", None) or list(vars(valor))
        for c in campos:
            _tipos_en(getattr(valor, c), hallados)


def _mundo_jugado(semilla, comandos=70):
    mundo = armar_mundo(semilla, salas=7, enemigos=5, cazadores=2, vida_jugador=2000)
    jugar_semilla(mundo.servicio, semilla, comandos)
    return mundo


def test_capturar_y_restaurar_da_el_mismo_resumen():
    """FR-023, FR-004 · capturar(partida) + restaurar en un grafo nuevo"""
    for semilla in (1, 2, 3):
        mundo = _mundo_jugado(semilla)
        registro = capturar(mundo.partida)
        copia = restaurar(registro, mundo.nuevo_mundo())
        assert copia is not mundo.partida
        assert resumen_plano(copia) == resumen_plano(mundo.partida)
        assert copia.jugador.sala is not mundo.partida.jugador.sala       #grafo distinto
        assert copia.reloj == mundo.partida.reloj
        assert copia.acciones_jugador == mundo.partida.acciones_jugador


@pytest.mark.parametrize("semilla", [4, 5, 6])
def test_tras_restaurar_ambos_juegos_siguen_iguales_en_cada_paso(semilla):
    """FR-023, FR-009 · 200 comandos con cazadores, veneno, trampas, puertas y muertes con botín:
    tras cada comando los dos resúmenes, la agenda y el azar coinciden"""
    mundo = _mundo_jugado(semilla, 25)
    nuevo = mundo.nuevo_mundo()
    copia = restaurar(capturar(mundo.partida), nuevo)
    controlador = Controlador(mundo.servicio_de(copia, nuevo), VistaMuda(), None, None)
    comparados = []

    def despues(comando):
        controlador.ejecutar(comando)
        assert resumen_plano(copia) == resumen_plano(mundo.partida), comando
        assert copia.agenda.num_sec == mundo.partida.agenda.num_sec
        assert copia.azar.getstate() == mundo.partida.azar.getstate()
        comparados.append(comando)

    jugar_semilla(mundo.servicio, semilla + 100, 200, despues=despues)
    assert len(comparados) >= 20
    assert mundo.partida.acciones_jugador > 30


def test_el_juego_de_prueba_tiene_de_verdad_todos_los_tipos_de_estado():
    """FR-023 · cazadores, veneno, velocidad, puertas que cierran solas y muertes con botín aparecen"""
    visto = {"veneno": False, "velocidad": False, "cazador": False, "botin": False, "cierre": False}
    for semilla in range(1, 9):
        mundo = armar_mundo(semilla, salas=7, enemigos=5, cazadores=2, vida_jugador=2000)

        def mirar(comando):
            p = mundo.partida
            for e in p.jugador.efectos:
                if e.tipo in visto:
                    visto[e.tipo] = True
            for ev in p.agenda.heap:
                if ev.tipo == "cierre_puerta":
                    visto["cierre"] = True
            for e in p.enemigos:
                if e.es_cazador():
                    visto["cazador"] = True

        jugar_semilla(mundo.servicio, semilla, 300, despues=mirar)
        if mundo.partida.enemigos_derrotados:
            visto["botin"] = True
    assert all(visto.values()), visto


def test_el_estado_del_generador_al_azar_se_restaura_exacto():
    """FR-023 · array('I') de 625 palabras + la marca gauss_next"""
    mundo = _mundo_jugado(2)
    mundo.partida.azar.gauss(0, 1)                     #deja un gauss_next pendiente
    registro = capturar(mundo.partida)
    assert isinstance(registro.azar, array) and registro.azar.typecode == "I"
    assert len(registro.azar) == 625
    assert registro.azar_gauss is not None
    copia = restaurar(registro, mundo.nuevo_mundo())
    assert copia.azar.getstate() == mundo.partida.azar.getstate()
    viejos = [mundo.partida.azar.random() for _ in range(5)] + [mundo.partida.azar.gauss(0, 1)]
    nuevos = [copia.azar.random() for _ in range(5)] + [copia.azar.gauss(0, 1)]
    assert viejos == nuevos


def test_el_registro_no_comparte_nada_mutable_con_la_partida_viva():
    """FR-023 · tras seguir jugando, el registro no cambia; solo contiene valores simples"""
    mundo = _mundo_jugado(3, 40)
    registro = capturar(mundo.partida)
    antes = _volcado(registro)
    tipos = []
    _tipos_en(registro, tipos)
    for t in tipos:
        assert (t in (int, str, bool, float, type(None), list, tuple, array)
                or t.__module__ == "model.registro_estado"), t
    jugar_semilla(mundo.servicio, 55, 80)
    assert mundo.partida.acciones_jugador > registro.acciones_jugador
    assert _volcado(registro) == antes
    copia = restaurar(registro, mundo.nuevo_mundo())
    copia.jugador.vida = 1
    copia.jugador.inventario.cabeza = None
    assert _volcado(registro) == antes


def test_restaurar_no_programa_ni_entra_en_salas():
    """FR-023 · desde_registro no tiene los efectos del constructor y deja el montículo igual"""
    mundo = _mundo_jugado(5, 30)
    registro = capturar(mundo.partida)
    copia = Partida.desde_registro(registro, mundo.nuevo_mundo())
    assert isinstance(registro, RegistroEstado)
    assert copia.agenda.num_sec == registro.num_sec
    assert len(copia.agenda.heap) == len(registro.agenda)
    assert len(copia.historial) == 0                   #sin retroceso heredado
    for i in range(len(copia.agenda.heap)):
        assert copia.agenda.heap[i].pos == i
        assert (copia.agenda.heap[i].tiempo, copia.agenda.heap[i].num_sec) == \
            (mundo.partida.agenda.heap[i].tiempo, mundo.partida.agenda.heap[i].num_sec)


#parte 2: el constructor puro y la cota de parada
def test_construir_grafo_no_escribe_en_el_repositorio():
    """FR-009 · el constructor puro devuelve un grafo nuevo y no toca repo.salas"""
    mundo = armar_mundo(1)
    repo = RepositorioCripta(None)
    assert repo.salas is None and repo.contenidos is None
    grafo = construir_grafo(mundo.dtos)
    assert repo.salas is None and repo.contenidos is None
    repo.construir_salas(mundo.dtos)
    guardado, contenido = repo.salas, repo.contenidos
    ids = list(guardado.ids)
    otro = repo.construir_grafo(mundo.dtos)
    assert repo.salas is guardado and repo.contenidos is contenido
    assert guardado.ids == ids and guardado is not otro and grafo is not otro


def test_dos_grafos_no_comparten_salas_ni_salidas():
    """FR-009 · cada llamada arma salas y salidas propias"""
    mundo = armar_mundo(2, salas=8)
    a, b = construir_grafo(mundo.dtos), construir_grafo(mundo.dtos)
    assert a.ids == b.ids
    for sa, sb in zip(a.valores, b.valores):
        assert sa is not sb
        for xa, xb in zip(sa.salidas, sb.salidas):
            assert xa is not xb and xa.destino is not xb.destino
            assert xa.opuesta is not xb.opuesta
            assert xa.destino is a.buscar(xa.destino.id)


def _partida_con_eventos():
    sala = Sala(1, "A")
    otra = Sala(2, "B")
    sala.agregar_salida(Salida("N", otra))
    jugador = Jugador(vida_max=10, ataque=1, defensa=0, velocidad=100, inventario_max=3, sala=sala)
    partida = Partida(jugador, semilla=1)
    trampas = [Trampa(f"t{i}", "T", 1) for i in range(5)]
    for t in trampas:
        t.armada = False
    return partida, trampas


def test_avanzar_con_limite_se_detiene_antes_de_un_evento_posterior():
    """FR-001, FR-006 · avanzar_hasta_jugador(limite=t) corre todo lo de tiempo <= t, sea cual sea su num_sec"""
    partida, trampas = _partida_con_eventos()
    partida._programar_siguiente(partida.jugador, 500)                 #decisión del jugador en t=500
    partida.agenda.programar(40, "rearme_trampa", None, trampas[0])
    partida.agenda.programar(100, "rearme_trampa", None, trampas[1])   #tiempo == límite
    partida.agenda.programar(101, "rearme_trampa", None, trampas[2])
    partida.agenda.programar(100, "rearme_trampa", None, trampas[3])   #tiempo == límite, num_sec mayor
    partida.avanzar_hasta_jugador(limite=100)
    assert [t.armada for t in trampas[:4]] == [True, True, False, True]
    assert partida.reloj == 100
    assert partida.agenda.proximo().tiempo == 101                      #quedan el de 101 y el jugador
    assert len(partida.agenda) == 2
    assert not partida.terminada


def test_avanzar_con_limite_menor_que_todo_no_extrae_nada():
    """FR-006 · el límite corta antes de extraer"""
    partida, trampas = _partida_con_eventos()
    partida._programar_siguiente(partida.jugador, 500)
    partida.agenda.programar(70, "rearme_trampa", None, trampas[0])
    antes = (partida.reloj, len(partida.agenda), partida.agenda.num_sec)
    partida.avanzar_hasta_jugador(limite=69)
    assert (partida.reloj, len(partida.agenda), partida.agenda.num_sec) == antes
    assert trampas[0].armada is False


def test_avanzar_sin_limite_se_comporta_como_siempre():
    """FR-001 · limite=None corre hasta la decisión del jugador"""
    partida, trampas = _partida_con_eventos()
    partida._programar_siguiente(partida.jugador, 500)
    partida.agenda.programar(70, "rearme_trampa", None, trampas[0])
    partida.agenda.programar(900, "rearme_trampa", None, trampas[1])
    partida.avanzar_hasta_jugador()
    assert partida.reloj == 500
    assert trampas[0].armada is True and trampas[1].armada is False
    assert len(partida.agenda) == 1
