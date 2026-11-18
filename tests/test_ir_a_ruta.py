import random

from model.ruta_conocida import RutaConocida
from model.sala_logica import ABIERTA, AVISTADA, CERRADA, Sala, Salida
from tests.mapas_cazador import _unir, cadena, cripta_aleatoria, grilla
from tests.mapas_niebla import explorar_todo, partida_en, ruta_referencia


def _listo(salas, jugador):
    """Partida con todo explorado y recordado como está, el jugador en `jugador`."""
    partida = partida_en(salas, jugador)
    explorar_todo(salas)
    return partida


def _como_referencia(salas, partida, destino):
    """El oráculo en la forma de RutaConocida: (salida, d)."""
    d, salida = ruta_referencia(salas, partida, destino)
    if d == 0:
        return None, 0
    return salida, d


def test_gana_la_ruta_mas_barata_aunque_tenga_mas_salidas():
    """FR-017, FR-018 · US6-3"""
    a, b, c, d, e = (Sala(i, f"S{i}") for i in range(1, 6))
    _unir(a, "E", b, "O", 500)                        # A-B directo cuesta 500
    _unir(a, "N", c, "S", 100)                        # A-C-D-B cuesta 300
    _unir(c, "E", d, "O", 100)
    _unir(d, "E", b, "N", 100)
    _unir(b, "E", e, "O", 100)
    salas = [a, b, c, d, e]
    partida = _listo(salas, a)
    salida, costo = RutaConocida().siguiente_paso(partida, b)
    assert costo == 300
    assert salida.destino is c and salida.direccion == "N"
    assert (salida, costo) == _como_referencia(salas, partida, b)


def test_empate_entre_vecinas_gana_el_menor_id_de_destino():
    """FR-018 · US6-4"""
    a, s2, s3, z = Sala(1, "A"), Sala(2, "S2"), Sala(3, "S3"), Sala(4, "Z")
    _unir(a, "N", s3, "S", 100)                       # N va hacia la sala 3
    _unir(a, "E", s2, "O", 100)                       # E va hacia la sala 2
    _unir(s2, "E", z, "O", 100)
    _unir(s3, "E", z, "N", 100)
    salas = [a, s2, s3, z]
    partida = _listo(salas, a)
    salida, costo = RutaConocida().siguiente_paso(partida, z)
    assert costo == 200 and salida.destino is s2


def test_empate_con_el_mismo_destino_gana_la_menor_direccion():
    """FR-018 · US6-4 (mismo id de destino: menor nombre de dirección)"""
    a, b = Sala(1, "A"), Sala(2, "B")
    a.agregar_salida(Salida("N", b, costo=100))
    a.agregar_salida(Salida("E", b, costo=100))
    b.agregar_salida(Salida("S", a, costo=100))
    salas = [a, b]
    partida = _listo(salas, a)
    salida, costo = RutaConocida().siguiente_paso(partida, b)
    assert costo == 100 and salida.direccion == "E"


def test_grilla_con_muchas_rutas_iguales_coincide_con_el_oraculo():
    """FR-018 · US6-4 (cripta en grilla)"""
    salas, _ = grilla(4, 4, 100)
    for origen in (0, 5, 10, 15):
        partida = _listo(salas, salas[origen])
        for destino in salas:
            assert (RutaConocida().siguiente_paso(partida, destino)
                    == _como_referencia(salas, partida, destino))


def test_una_sala_avistada_nunca_se_usa_aunque_acorte_la_ruta():
    """FR-017 · US6-5"""
    a, b, atajo, c = Sala(1, "A"), Sala(2, "B"), Sala(3, "atajo"), Sala(4, "C")
    _unir(a, "E", b, "O", 500)
    _unir(b, "E", c, "O", 500)
    _unir(a, "N", atajo, "S", 10)
    _unir(atajo, "E", c, "N", 10)
    salas = [a, b, atajo, c]
    partida = _listo(salas, a)
    atajo.conocimiento = AVISTADA
    salida, costo = RutaConocida().siguiente_paso(partida, c)
    assert costo == 1000 and salida.destino is b


def test_puerta_recordada_cerrada_no_se_usa_y_nunca_se_abre():
    """FR-017, FR-021 · US6-6"""
    a, b, c = Sala(1, "A"), Sala(2, "B"), Sala(3, "C")
    _unir(a, "E", b, "O", 100)
    _unir(b, "E", c, "O", 100, cerrada=True, llave="llave1")   # barata pero cerrada
    _unir(a, "N", c, "S", 900)
    salas = [a, b, c]
    partida = _listo(salas, a)
    llamadas = []
    original = partida.abrir_puerta
    partida.abrir_puerta = lambda direccion: llamadas.append(direccion) or original(direccion)
    salida, costo = RutaConocida().siguiente_paso(partida, c)
    assert costo == 900 and salida.direccion == "N"
    assert llamadas == []


def test_jugador_ya_en_el_destino_y_sin_ruta():
    """FR-017 · (None, 0) en el destino y (None, None) sin ruta"""
    salas, pares = cadena([100, 100])
    partida = _listo(salas, salas[0])
    assert RutaConocida().siguiente_paso(partida, salas[0]) == (None, 0)
    for cara in pares[1]:
        cara.memoria = CERRADA
    assert RutaConocida().siguiente_paso(partida, salas[2]) == (None, None)


def test_la_salida_hacia_una_puerta_sin_observar_no_se_usa():
    """FR-017 · puerta con memoria NO_OBSERVADA lejos del jugador"""
    salas, pares = cadena([100, 100])
    partida = _listo(salas, salas[0])
    for cara in pares[1]:
        cara.memoria = 0
    assert RutaConocida().siguiente_paso(partida, salas[2]) == (None, None)
    for cara in pares[1]:
        cara.memoria = ABIERTA
    assert RutaConocida().siguiente_paso(partida, salas[2])[1] == 200


def test_la_puerta_que_toca_la_sala_del_jugador_se_lee_en_vivo():
    """FR-017 · la memoria vieja de una puerta que toca la sala del jugador no cuenta"""
    salas, pares = cadena([100, 100])
    partida = _listo(salas, salas[0])
    for cara in pares[0]:
        cara.cerrada = True                    # real: cerrada; memoria: abierta
    assert RutaConocida().siguiente_paso(partida, salas[2]) == (None, None)


def _permutar(salas, modo):
    for sala in salas:
        for lista in (sala.salidas, sala.entradas):
            if modo == "reversa":
                lista.reverse()
            elif lista:
                lista.append(lista.pop(0))


def test_el_orden_de_salidas_y_entradas_no_cambia_el_resultado():
    """FR-018 · independiente del orden de Sala.salidas y Sala.entradas"""
    for semilla in range(20):
        salas = cripta_aleatoria(semilla, 12)
        partida = _listo(salas, salas[semilla % 12])
        destino = salas[(semilla * 5 + 3) % 12]
        esperado = RutaConocida().siguiente_paso(partida, destino)
        for modo in ("reversa", "rotar", "rotar"):
            _permutar(salas, modo)
            assert RutaConocida().siguiente_paso(partida, destino) == esperado


def test_reusar_el_objeto_da_lo_mismo_que_objetos_nuevos():
    """FR-018 · el montículo se vacía al empezar cada búsqueda"""
    salas = cripta_aleatoria(3, 15)
    partida = _listo(salas, salas[0])
    reutilizado = RutaConocida()
    for destino in salas:
        for _ in range(2):
            assert (reutilizado.siguiente_paso(partida, destino)
                    == RutaConocida().siguiente_paso(partida, destino))


def test_aleatorio_200_criptas_contra_el_oraculo():
    """FR-017, FR-018, FR-021 · salas sin explorar y puertas sin observar al azar"""
    for semilla in range(200):
        azar = random.Random(semilla)
        salas = cripta_aleatoria(semilla, azar.randint(4, 14))
        aqui = azar.choice(salas)
        destino = azar.choice(salas)
        partida = partida_en(salas, aqui)
        explorar_todo(salas)
        for sala in salas:
            if sala is not aqui and sala is not destino and azar.random() < 0.25:
                sala.conocimiento = azar.choice((0, 1))
            for salida in sala.salidas:
                if azar.random() < 0.2:
                    salida.memoria = 0
                    if salida.opuesta is not None:
                        salida.opuesta.memoria = 0
        assert (RutaConocida().siguiente_paso(partida, destino)
                == _como_referencia(salas, partida, destino)), semilla
