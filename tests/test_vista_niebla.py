from dto.estado_vista_dto import EstadoVistaDTO
from tests.mapas_cazador import cadena
from tests.mapas_niebla import explorar_todo, partida_en, servicio_en
from view.vista_consola import VistaConsola


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
