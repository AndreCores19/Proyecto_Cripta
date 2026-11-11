"""Captura la salida de las vistas de la parte uno como golden files (T003).

Se ejecuta una sola vez, antes de cambiar view/, controller/, service/ o
aplicacion.py:

    python -m tests.capturar_salida_parte1

Escribe los archivos en specs/001-exit-costs/salida-parte1/. Cada captura usa
su propia llamada a armar_estado_fijo(...) y cada reproducir su propia AppFalsa.
"""
import contextlib
import io

from aplicacion import Aplicacion
from tests.estado_fijo import CARPETA_GOLDEN, AppFalsa, LectorFalso, armar_estado_fijo
from view.vista_consola import VistaConsola
from view.vista_replay import VistaReplay

VERSION = "v1"
COMANDOS_REPLAY = ["w", "d", "esperar", "zz"]   # un movimiento bloqueado y un comando desconocido


def capturar(funcion):
    salida = io.StringIO()
    with contextlib.redirect_stdout(salida):
        funcion()
    return salida.getvalue()


def escribir(nombre, texto):
    with open(CARPETA_GOLDEN / nombre, "w", encoding="utf-8", newline="\n") as archivo:
        archivo.write(texto)
    print(f"escrito {nombre} ({len(texto.splitlines())} líneas)")


def main():
    CARPETA_GOLDEN.mkdir(parents=True, exist_ok=True)

    _, partida = armar_estado_fijo()
    escribir("estado.txt", capturar(lambda: VistaConsola().mostrar_estado(partida)))

    for final in ("victoria", "muerte", "salida"):
        _, partida = armar_estado_fijo(final)
        escribir(f"final_consola_{final}.txt",
                 capturar(lambda: VistaConsola().mostrar_final(partida)))

    _, partida = armar_estado_fijo()
    escribir("inventario.txt", capturar(lambda: VistaConsola().mostrar_inventario(partida)))

    for criterio in ("peso", "valor", "nombre"):
        servicio, _ = armar_estado_fijo()
        escribir(f"inventario_{criterio}.txt", capturar(
            lambda: VistaConsola().mostrar_inventario_ordenado(
                servicio.vista_ordenada(criterio), criterio)))

    for final in ("victoria", "muerte", "salida"):
        _, partida = armar_estado_fijo(final)
        escribir(f"final_replay_{final}.txt",
                 capturar(lambda: VistaReplay().mostrar_final(partida)))

    escribir("reporte_replay.txt",
             capturar(lambda: VistaReplay().mostrar_reporte(12, 50, 7, 3)))
    escribir("reporte_replay_sin_presupuesto.txt",
             capturar(lambda: VistaReplay().mostrar_reporte(12, None, 0, 0)))

    escribir("replay_completo.txt", capturar(lambda: Aplicacion.reproducir(
        AppFalsa(VERSION, VERSION), LectorFalso(1, COMANDOS_REPLAY, VERSION, VERSION))))
    escribir("replay_version.txt", capturar(lambda: Aplicacion.reproducir(
        AppFalsa(VERSION, VERSION), LectorFalso(1, COMANDOS_REPLAY, "v0", VERSION))))


if __name__ == "__main__":
    main()
