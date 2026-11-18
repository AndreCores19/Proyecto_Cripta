from controller.controlador import Controlador
from dto.estado_vista_dto import EstadoVistaDTO
from tests.mapas_cazador import cadena
from tests.mapas_niebla import explorar_todo, partida_en, servicio_en
from tests.test_niebla_retroceso import instantanea_conocimiento
from view.vista_consola import VistaConsola
from view.vista_silenciosa import VistaSilenciosa


def _mostrar(servicio, capsys):
    """Imprime la sala actual con la vista de consola y devuelve el texto."""
    capsys.readouterr()
    VistaConsola().mostrar_estado(servicio.estado_vista())
    return capsys.readouterr().out


def _salidas(texto):
    """Líneas de la sección «Salidas:» de la vista."""
    lineas = texto.splitlines()
    inicio = lineas.index("Salidas:") + 1
    fin = lineas.index("Enemigos en la sala:")
    return lineas[inicio:fin]


def _cripta():
    """Tres salas en cadena con nombres distintivos: Inicio, Intermedia, Lejana."""
    salas, pares = cadena([100, 300])
    salas[0].nombre, salas[1].nombre, salas[2].nombre = "Inicio", "Intermedia", "Lejana"
    return salas, pares


def test_sala_explorada_muestra_nombre_salidas_costos_y_puertas(capsys):
    """FR-003, FR-010 · US1-3"""
    salas, pares = _cripta()
    pares[0][0].cerrada = pares[0][1].cerrada = True
    explorar_todo(salas)
    servicio = servicio_en(partida_en(salas, salas[1]))
    texto = _mostrar(servicio, capsys)
    assert "Sala 2: Intermedia" in texto
    assert _salidas(texto) == ["  O -> Inicio (cerrada, costo 100)",
                               "  E -> Lejana (abierta, costo 300)"]


def test_sala_avistada_sin_nombre_y_desconocida_no_aparece(capsys):
    """FR-004, FR-005, FR-010 · US1-4, US1-5"""
    salas, _ = _cripta()
    servicio = servicio_en(partida_en(salas, salas[0]))
    estado = servicio.estado_vista()
    assert isinstance(estado, EstadoVistaDTO)
    assert [s.nombre_destino for s in estado.salidas] == [None]
    texto = _mostrar(servicio, capsys)
    assert "Intermedia" not in texto      # avistada: solo se sabe que existe
    assert "Lejana" not in texto          # desconocida: no aparece en ninguna parte


def test_la_vista_se_arma_con_el_conocimiento_no_con_el_esqueleto(capsys):
    """FR-010, FR-011 · US1-6 (el nombre del vecino falta mientras está avistado y aparece al explorarlo)"""
    salas, _ = _cripta()
    servicio = servicio_en(partida_en(salas, salas[0]))
    assert "Intermedia" not in _mostrar(servicio, capsys)      # avistada
    servicio.mover("E")
    texto = _mostrar(servicio, capsys)
    assert "Sala 2: Intermedia" in texto                      # explorada
    assert "Lejana" not in texto                              # avistada desde la sala 2
    servicio.mover("O")
    assert "  E -> Intermedia (abierta, costo 100)" in _mostrar(servicio, capsys)


def test_salida_hacia_sala_avistada_dice_sin_explorar(capsys):
    """FR-004, FR-010 · US1-8"""
    salas, pares = _cripta()
    servicio = servicio_en(partida_en(salas, salas[0]))
    assert _salidas(_mostrar(servicio, capsys)) == ["  E -> sin explorar (abierta, costo 100)"]
    servicio.mover("E")
    # Sala 2: hacia la explorada se imprime el nombre; hacia la avistada, «sin explorar».
    assert _salidas(_mostrar(servicio, capsys)) == [
        "  O -> Inicio (abierta, costo 100)",
        "  E -> sin explorar (abierta, costo 300)"]


def test_salida_cerrada_hacia_sala_avistada_conserva_puerta_y_costo(capsys):
    """FR-004, FR-010 · US1-8 (dirección, costo y puerta se imprimen aunque no se sepa el nombre)"""
    salas, pares = _cripta()
    pares[0][0].cerrada = pares[0][1].cerrada = True
    servicio = servicio_en(partida_en(salas, salas[0]))
    assert _salidas(_mostrar(servicio, capsys)) == ["  E -> sin explorar (cerrada, costo 100)"]


# --- Mapa conocido (T038) ---------------------------------------------------

def _mapa_de_cuatro():
    """S1(Entrada) -E- S2(Pasillo) -E- S3(Sala3) -E- S4(Lejana); el jugador, en S1 con la antorcha apagada."""
    salas, pares = cadena([100, 300, 150])
    for sala, nombre in zip(salas, ("Entrada", "Pasillo", "Sala3", "Lejana")):
        sala.nombre = nombre
    return salas, pares


def _plano(valor):
    """Comprueba que `valor` sea solo int, str, bool, None o listas de eso (los DTO se recorren por sus campos)."""
    if valor is None or isinstance(valor, (int, str, bool)):
        return
    if isinstance(valor, list):
        for elemento in valor:
            _plano(elemento)
        return
    assert type(valor).__module__.startswith("dto."), f"referencia al modelo: {type(valor)}"
    for campo in vars(valor).values():
        _plano(campo)


def test_el_mapa_lista_las_salas_exploradas_con_sus_salidas_y_puertas():
    """FR-005, FR-015, FR-004 · US5-1"""
    salas, pares = _mapa_de_cuatro()
    pares[1][0].cerrada = pares[1][1].cerrada = True           # S2-S3 cerrada
    partida = partida_en(salas, salas[0])
    servicio = servicio_en(partida)
    servicio.mover("E")                                         # explora S2; S3 queda avistada
    mapa = servicio.mapa_vista()
    assert mapa.id_sala_actual == 2
    assert [s.id_sala for s in mapa.salas] == [1, 2]
    entrada, pasillo = mapa.salas
    assert entrada.nombre == "Entrada" and pasillo.nombre == "Pasillo"
    assert [(x.direccion, x.id_destino, x.nombre_destino, x.costo, x.puerta) for x in entrada.salidas] == [
        ("E", 2, "Pasillo", 100, "abierta")]
    assert [(x.direccion, x.id_destino, x.nombre_destino, x.costo, x.puerta) for x in pasillo.salidas] == [
        ("O", 1, "Entrada", 100, "abierta"),
        ("E", None, None, 300, "cerrada")]                      # hacia una sala avistada: sin id ni nombre


def test_las_salas_desconocidas_no_aparecen_en_el_mapa():
    """FR-005 · US5-2"""
    salas, _ = _mapa_de_cuatro()
    servicio = servicio_en(partida_en(salas, salas[0]))
    mapa = servicio.mapa_vista()
    assert [s.id_sala for s in mapa.salas] == [1]
    texto = repr([(x.id_destino, x.nombre_destino) for s in mapa.salas for x in s.salidas])
    assert "Sala3" not in texto and "Lejana" not in texto


def test_el_comando_mapa_no_cambia_nada_ni_consume_tiempo(capsys):
    """FR-015 · US5-3"""
    salas, _ = _mapa_de_cuatro()
    partida = partida_en(salas, salas[0])
    controlador = Controlador(servicio_en(partida), VistaConsola(), None, None)
    controlador.ejecutar("d")
    antes = instantanea_conocimiento(salas, partida)
    reloj, acciones = partida.reloj, partida.acciones_jugador
    capsys.readouterr()
    controlador.ejecutar("mapa")
    assert "Mapa conocido:" in capsys.readouterr().out
    assert partida.reloj == reloj and partida.acciones_jugador == acciones
    assert instantanea_conocimiento(salas, partida) == antes
    assert controlador.comandos == ["d", "mapa"]                # se anota como un comando más, como inv


def test_el_mapa_ordena_por_id_marca_al_jugador_y_dice_sin_observar(capsys):
    """FR-015, FR-005 · puertas sin observar, orden por id y marca de la sala actual"""
    salas, _ = _mapa_de_cuatro()
    partida = partida_en(salas, salas[0])
    partida.efectos.encender_antorcha(partida.jugador, 10 ** 6)
    servicio = servicio_en(partida)
    servicio.mover("E")                    # con antorcha: S1, S2 y S3 exploradas; S4 avistada
    capsys.readouterr()
    VistaConsola().mostrar_mapa(servicio.mapa_vista())
    lineas = capsys.readouterr().out.splitlines()
    assert lineas == [
        "Mapa conocido:",
        "  Sala 1: Entrada",
        "    E -> Sala 2: Pasillo (abierta, costo 100)",
        "  Sala 2: Pasillo  (tú estás aquí)",
        "    O -> Sala 1: Entrada (abierta, costo 100)",
        "    E -> Sala 3: Sala3 (abierta, costo 300)",
        "  Sala 3: Sala3",
        "    O -> Sala 2: Pasillo (abierta, costo 300)",
        "    E -> sin explorar (sin observar, costo 150)",
    ]


def test_el_mapa_devuelve_solo_valores_simples():
    """FR-015 · MapaVistaDTO no lleva ninguna referencia al modelo"""
    salas, _ = _mapa_de_cuatro()
    partida = partida_en(salas, salas[0])
    partida.efectos.encender_antorcha(partida.jugador, 10 ** 6)
    servicio = servicio_en(partida)
    servicio.mover("E")
    _plano(servicio.mapa_vista())


def test_el_mapa_no_hace_nada_con_la_vista_silenciosa_ni_sin_vista():
    """FR-015 · VistaSilenciosa.mostrar_mapa no hace nada y sin vista el controlador no falla"""
    salas, _ = _mapa_de_cuatro()
    partida = partida_en(salas, salas[0])
    mapa = servicio_en(partida).mapa_vista()
    assert VistaSilenciosa().mostrar_mapa(mapa) is None
    sin_vista = Controlador(servicio_en(partida), None, None, None)
    sin_vista.ejecutar("mapa")
    assert sin_vista.comandos == ["mapa"]
