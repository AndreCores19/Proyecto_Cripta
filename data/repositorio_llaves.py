from dto.llave_dto import LlaveUbicacionDTO


class RepositorioLlaves:
    """Ubicación de las llaves de una cripta: del archivo guardado si es de la misma versión, si no del servicio.

    El servicio cuenta la consulta en el presupuesto (FR-004). Una versión nueva de la cripta invalida lo
    guardado (FR-005): se vuelve a preguntar y se sobreescribe el archivo.
    """

    def __init__(self, fuente, almacen):
        self.fuente = fuente
        self.almacen = almacen

    def cargar(self, id_cripta, version):
        guardado = self.almacen.leer(id_cripta)
        if guardado is not None and guardado[0] == version:
            elementos = guardado[1]
        else:
            elementos = self.fuente.llaves(id_cripta)["llaves"]
            self.almacen.guardar(id_cripta, version, elementos)
        return [LlaveUbicacionDTO.desde_json(elemento) for elemento in elementos]
