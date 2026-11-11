from model.sala_logica import Sala, Salida
from model.jugador_logica import Jugador
from model.objeto_logica import Objeto
from model.partida_logica import Partida

def test_puerta_se_abre_y_cierra_por_los_dos_lados():
    sala1, sala2 = Sala(1, "A"), Sala(2, "B")
    ida = Salida("E", sala2, cerrada=True, llave="llave1", cierre_automatico=100)
    vuelta = Salida("O", sala1)
    sala1.agregar_salida(ida)
    sala2.agregar_salida(vuelta)
    ida.enlazar(vuelta)
    assert vuelta.cerrada is True and vuelta.llave == "llave1"

    jugador = Jugador(vida_max=50, ataque=10, defensa=0, velocidad=100, inventario_max=10, sala=sala1)
    jugador.inventario.agregar(Objeto(1, "llave1", "Llave", "llave", 1, 1))
    partida = Partida(jugador, semilla=1)

    partida.abrir_puerta("E")
    assert ida.cerrada is False and vuelta.cerrada is False

    partida.esperar_jugador()
    partida.esperar_jugador()
    assert ida.cerrada is True and vuelta.cerrada is True


def _puerta(costo_ida, costo_vuelta):
    sala1, sala2 = Sala(1, "A"), Sala(2, "B")
    ida = Salida("E", sala2, costo=costo_ida)
    vuelta = Salida("O", sala1, costo=costo_vuelta)
    sala1.agregar_salida(ida)
    sala2.agregar_salida(vuelta)
    ida.enlazar(vuelta)
    return ida, vuelta


def test_costo_sin_declarar_en_ningun_lado_es_100():
    """FR-002, FR-005 · None/None → los dos lados cuestan 100."""
    ida, vuelta = _puerta(None, None)
    assert ida.costo == 100 and vuelta.costo == 100


def test_costo_declarado_solo_en_la_ida_se_comparte():
    """FR-005 · x/None → los dos lados cuestan x."""
    ida, vuelta = _puerta(300, None)
    assert ida.costo == 300 and vuelta.costo == 300


def test_costo_declarado_solo_en_la_vuelta_se_comparte():
    """FR-005 · None/y → los dos lados cuestan y."""
    ida, vuelta = _puerta(None, 40)
    assert ida.costo == 40 and vuelta.costo == 40


def test_costo_igual_en_los_dos_lados():
    """FR-005 · x/x → los dos lados cuestan x."""
    ida, vuelta = _puerta(250, 250)
    assert ida.costo == 250 and vuelta.costo == 250


def test_salida_sin_opuesta_usa_su_costo_o_100():
    """FR-002 · una salida sin opuesta devuelve su valor declarado, o 100."""
    sala = Sala(2, "B")
    assert Salida("N", sala, costo=70).costo == 70
    assert Salida("N", sala).costo == 100


def test_costo_declarado_sigue_none_si_nadie_lo_declara():
    """FR-002 · enlazar no inventa un costo declarado."""
    ida, vuelta = _puerta(None, None)
    assert ida.costo_declarado is None and vuelta.costo_declarado is None


def test_agregar_salida_registra_origen_y_entradas():
    """FR-008 · agregar_salida fija origen y anota la entrada en el destino."""
    sala1, sala2 = Sala(1, "A"), Sala(2, "B")
    ida = Salida("E", sala2)
    vuelta = Salida("O", sala1)
    sala1.agregar_salida(ida)
    sala2.agregar_salida(vuelta)
    assert ida.origen is sala1 and vuelta.origen is sala2
    assert sala2.entradas == [ida]
    assert sala1.entradas == [vuelta]


def test_salida_de_un_solo_sentido_solo_da_entrada_al_destino():
    """FR-008 · una salida unidireccional deja entrada solo en el destino."""
    sala1, sala2 = Sala(1, "A"), Sala(2, "B")
    ida = Salida("E", sala2)
    sala1.agregar_salida(ida)
    assert sala2.entradas == [ida]
    assert sala1.entradas == []


def test_sala_nueva_tiene_campos_de_busqueda_limpios():
    """FR-009 · busq_marca == -1 y busq_dist == 0."""
    sala = Sala(1, "A")
    assert sala.busq_marca == -1 and sala.busq_dist == 0


def test_asignar_cerrada_sube_la_epoca_y_leer_no():
    """FR-011 · cada asignación de cerrada suma 1 a Salida.epoca_puertas; leer no."""
    salida = Salida("E", Sala(2, "B"))
    antes = Salida.epoca_puertas
    _ = salida.cerrada
    assert Salida.epoca_puertas == antes
    salida.cerrada = True
    assert Salida.epoca_puertas == antes + 1
    salida.cerrada = False
    assert Salida.epoca_puertas == antes + 2


def test_abrir_puerta_y_retroceder_suben_la_epoca():
    """FR-011 · abrir_puerta y el retroceso que reescribe cerrada suben el contador."""
    sala1, sala2 = Sala(1, "A"), Sala(2, "B")
    ida = Salida("E", sala2, cerrada=True, llave="llave1")
    vuelta = Salida("O", sala1)
    sala1.agregar_salida(ida)
    sala2.agregar_salida(vuelta)
    ida.enlazar(vuelta)
    jugador = Jugador(vida_max=50, ataque=10, defensa=0, velocidad=100, inventario_max=10, sala=sala1)
    jugador.inventario.agregar(Objeto(1, "llave1", "Llave", "llave", 1, 1))
    partida = Partida(jugador, semilla=1)
    e0 = Salida.epoca_puertas
    partida.abrir_puerta("E")
    e1 = Salida.epoca_puertas
    assert e1 > e0
    partida.retroceder()
    assert Salida.epoca_puertas > e1
    assert ida.cerrada is True
