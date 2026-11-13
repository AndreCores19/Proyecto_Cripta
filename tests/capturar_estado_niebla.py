"""Captura el estado de partidas sembradas antes de la niebla de guerra (T004).

Se ejecutó UNA vez, con el código sin cambios, para guardar
specs/003-fog-of-war/estado-antes.txt. Volver a ejecutarlo después de cambiar
el código sobrescribiría la referencia; para comparar (T048) hay que pasar
otra ruta de salida como primer argumento.
"""
import sys
from pathlib import Path

from tests.estado_sin_cazadores import resumen

SALIDA = Path(__file__).resolve().parent.parent / "specs" / "003-fog-of-war" / "estado-antes.txt"

if __name__ == "__main__":
    destino = Path(sys.argv[1]) if len(sys.argv) > 1 else SALIDA
    partes = [f"--- semilla {s} ---\n{resumen(s)}" for s in (1, 2, 3)]
    destino.write_text("\n".join(partes), encoding="utf-8")
    print(f"Escrito {destino}")
