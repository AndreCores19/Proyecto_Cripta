"""Captura el estado de partidas sembradas sin cazadores (T005).

Se ejecutó UNA vez, con el código sin cambios, para guardar
specs/002-hunter-enemy/estado-sin-cazadores-antes.txt. Volver a ejecutarlo
después de cambiar el código sobrescribiría la referencia.
"""
from pathlib import Path

from tests.estado_sin_cazadores import resumen

SALIDA = Path(__file__).resolve().parent.parent / "specs" / "002-hunter-enemy" / "estado-sin-cazadores-antes.txt"

if __name__ == "__main__":
    partes = [f"--- semilla {s} ---\n{resumen(s)}" for s in (1, 2, 3)]
    SALIDA.write_text("\n".join(partes), encoding="utf-8")
    print(f"Escrito {SALIDA}")
