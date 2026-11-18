from pathlib import Path
import json


class AlmacenLlaves:
    """Guarda, por cripta, la lista de llaves con la versión de la cripta para la que se obtuvo (FR-005).

    Archivo `<carpeta>/<id_cripta>.json`: {"version": ..., "llaves": [{"id", "sala", "enemigo"?}]}.
    No importa nada de model/ ni de view/.
    """

    def __init__(self, carpeta):
        self.carpeta = Path(carpeta)
        self.carpeta.mkdir(parents=True, exist_ok=True)

    def leer(self, id_cripta):
        """Devuelve (version, llaves) o None si falta el archivo, está dañado o incompleto."""
        ruta = self._ruta(id_cripta)
        if not ruta.exists():
            return None
        try:
            with open(ruta, "r", encoding="utf-8") as archivo:
                contenido = json.load(archivo)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None
        if not isinstance(contenido, dict):
            return None
        version = contenido.get("version")
        llaves = contenido.get("llaves")
        if not isinstance(version, str) or not isinstance(llaves, list):
            return None
        return version, llaves

    def guardar(self, id_cripta, version, llaves):
        ruta = self._ruta(id_cripta)
        with open(ruta, "w", encoding="utf-8") as archivo:
            json.dump({"version": version, "llaves": llaves}, archivo, ensure_ascii=False)

    def _ruta(self, id_cripta):
        if not id_cripta or "/" in id_cripta or "\\" in id_cripta:
            raise ValueError(f"Id de cripta no válido: {id_cripta}")
        return self.carpeta / f"{id_cripta}.json"
