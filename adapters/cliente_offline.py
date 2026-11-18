import json
import os

## Nota: Se hace esta clase cliente_offline porque no se encontró el paquete offline que decía el enunciado, así que hacemos el propio
class ErrorOffline(Exception):
    """Falta un archivo del paquete sin conexión."""


class ClienteOffline:
    def __init__(self, carpeta="offline"):
        self.carpeta = carpeta
        self.solicitudes = 0          ## offline nunca cuenta como solicitud de red
        self.presupuesto = None

    def asignar_presupuesto(self, n):
        self.presupuesto = n

    def solicitudes_realizadas(self):
        return 0

    def _leer(self, *partes):
        ruta = os.path.join(self.carpeta, *partes)
        if not os.path.exists(ruta):
            raise ErrorOffline(f"Falta en el paquete sin conexión: {ruta}")
        with open(ruta, encoding="utf-8") as archivo:
            return json.load(archivo)

    def listar_criptas(self):
        return self._leer("criptas.json")

    def datos_cripta(self, id_cripta):
        return self._leer(id_cripta, "datos.json")

    def version_cripta(self, id_cripta):
        datos = self.datos_cripta(id_cripta)
        return {"id": datos["id"], "version": datos["version"]}

    def version_catalogo(self):
        return self._leer("catalogo_version.json")

    def pagina_esqueleto(self, id_cripta, pagina):
        return self._leer(id_cripta, f"esqueleto_{pagina}.json")

    def contenido_salas(self, id_cripta, ids_salas):
        todo = self._leer(id_cripta, "contenido.json")
        elegidas = []
        for elemento in todo["contenido"]:
            if elemento["sala"] in ids_salas:
                elegidas.append(elemento)
        return {"contenido": elegidas}

    def catalogo(self, ids):
        todo = self._leer("catalogo.json")
        elegidas = []
        for entidad in todo["entidades"]:
            if entidad["id"] in ids:
                elegidas.append(entidad)
        return {"entidades": elegidas}

    def llaves(self, id_cripta):
        return self._leer(id_cripta, "llaves.json")
