from structures.vector_busqueda import VectorBusqueda


class FichasCongeladas(VectorBusqueda):
    """Las fichas que la fábrica viva ya resolvió, por id (un vector ordenado, sin `dict`).

    La caché del catálogo desaloja fichas; esta guarda una vez cada ficha vista para que la
    reproducción del historial nunca tenga que volver a pedirla (spec 005, investigación R8).
    """

    def guardar(self, id_ficha, ficha):
        if self.posicion(id_ficha) == -1:
            self.insertar_ordenado(id_ficha, ficha)

    def obtener(self, id_ficha):
        return self.buscar(id_ficha)
