"""Menú de elección de cripta: el número que se muestra es el de la cripta (cripta-02 -> 2) y es el que se teclea."""
import builtins

from view.vista_consola import VistaConsola

CRIPTAS = [
    {"id": "cripta-02", "nombre": "Catacumbas menores", "salas": 20, "dificultad": 2},
    {"id": "cripta-03", "nombre": "Catacumbas medias", "salas": 40, "dificultad": 3},
    {"id": "cripta-06", "nombre": "Cripta de referencia", "salas": 300, "dificultad": 5},
]


def _elegir(monkeypatch, capsys, entradas, criptas=CRIPTAS):
    pendientes = list(entradas)

    def falso_input(_prompt=""):
        if not pendientes:
            raise AssertionError("el menú siguió preguntando")
        return pendientes.pop(0)

    monkeypatch.setattr(builtins, "input", falso_input)
    resultado = VistaConsola().elegir_cripta(criptas)
    return resultado, capsys.readouterr().out


def test_el_menu_muestra_el_numero_de_cada_cripta(monkeypatch, capsys):
    _, salida = _elegir(monkeypatch, capsys, ["salir"])
    assert "  2. Catacumbas menores (cripta-02) - 20 salas, dificultad 2" in salida
    assert "  3. Catacumbas medias (cripta-03)" in salida
    assert "  6. Cripta de referencia (cripta-06)" in salida
    assert "  1. " not in salida


def test_2_02_y_cripta_02_eligen_cripta_02(monkeypatch, capsys):
    for texto in ("2", "02", "cripta-02", "  CRIPTA-02 ", " 2 "):
        assert _elegir(monkeypatch, capsys, [texto])[0] == "cripta-02"


def test_6_elige_cripta_06(monkeypatch, capsys):
    assert _elegir(monkeypatch, capsys, ["6"])[0] == "cripta-06"


def test_un_numero_que_no_esta_en_la_lista_vuelve_a_preguntar(monkeypatch, capsys):
    resultado, salida = _elegir(monkeypatch, capsys, ["1", "7", "abc", "", "4", "salir"])
    assert resultado is None
    assert salida.count("No existe esa cripta. Elegí un número de la lista.") == 5


def test_un_numero_invalido_y_luego_uno_valido_elige_el_valido(monkeypatch, capsys):
    assert _elegir(monkeypatch, capsys, ["1", "3"])[0] == "cripta-03"


def test_salir_termina_sin_elegir(monkeypatch, capsys):
    assert _elegir(monkeypatch, capsys, ["salir"])[0] is None
    assert _elegir(monkeypatch, capsys, [" SALIR "])[0] is None


def test_un_id_sin_el_patron_usa_su_posicion_en_la_lista(monkeypatch, capsys):
    criptas = [{"id": "especial", "nombre": "Rara", "salas": 5, "dificultad": 1},
               {"id": "cripta-04", "nombre": "Normal", "salas": 9, "dificultad": 2}]
    resultado, salida = _elegir(monkeypatch, capsys, ["1"], criptas)
    assert resultado == "especial"
    assert "  1. Rara (especial)" in salida and "  4. Normal (cripta-04)" in salida
    assert _elegir(monkeypatch, capsys, ["04"], criptas)[0] == "cripta-04"
    assert _elegir(monkeypatch, capsys, ["especial"], criptas)[0] == "especial"
    assert _elegir(monkeypatch, capsys, ["2", "4"], criptas)[0] == "cripta-04"
