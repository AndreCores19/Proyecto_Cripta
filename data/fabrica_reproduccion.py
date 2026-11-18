"""La fábrica del mundo aparte de la reproducción (spec 005, investigación R8).

Puebla salas con lo que ya está en `repo_cripta.contenidos` y las fichas congeladas de la fábrica viva.
No tiene catálogo: si falta una ficha o un contenido lanza `ErrorReproduccion` y nunca pide nada a la red.
Crea los objetos, enemigos y trampas con las mismas funciones de `FabricaModelo`, así que los ids de
instancia salen igual que en el juego vivo.
"""
from data.fabrica_modelo import FabricaModelo
from model.registro_estado import Mundo
from model.reproduccion_logica import ErrorReproduccion
from structures.ordenamientos import ordenar
from structures.vector_busqueda import VectorBusqueda


class _RepoReproduccion:
    #lo único que FabricaModelo lee de un repositorio de cripta
    def __init__(self, salas, contenidos, datos):
        self.salas = salas
        self.contenidos = contenidos
        self.datos = datos


def _vector_de(pares):
    vector = VectorBusqueda()
    for id_elemento, valor in ordenar(pares, lambda p: p[0]):
        vector.agregar(id_elemento, valor)
    vector.preparar()
    return vector


class FabricaReproduccion(FabricaModelo):

    def __init__(self, salas, contenidos, datos, fichas):
        super().__init__(_RepoReproduccion(salas, contenidos, datos), None)
        self.fichas = fichas                      #FichasCongeladas de la fábrica viva (solo lectura)
        self._enemigos = None                     #VectorBusqueda id -> InstanciaEnemigoDTO, al primer uso
        self._trampas = None
        self.iniciar()

    @classmethod
    def desde(cls, fabrica_viva, salas):
        repo = fabrica_viva.repo_cripta
        return cls(salas, repo.contenidos, repo.datos, fabrica_viva.fichas_vistas)

    def armar_mundo(self):
        return Mundo(self.repo_cripta.salas, self.crear_jugador, self._objeto_de_catalogo,
                     self._enemigo_por_id, self._trampa_por_id,
                     fabrica=self, creador_objetos=self.objeto_desde_id)

    #fichas y contenido: solo de lo guardado
    def _ficha(self, id_ficha):
        ficha = self.fichas.obtener(id_ficha)
        if ficha is None:
            raise ErrorReproduccion(f"La ficha {id_ficha} no está entre las que el juego ya resolvió")
        return ficha

    def objeto_desde_id(self, id_ficha):
        objeto = self.crear_objeto(self.siguiente_instancia, self._ficha(id_ficha))
        self.siguiente_instancia += 1
        return objeto

    def poblar_sala(self, sala):
        pos = self.repo_cripta.salas.posicion(sala.id)
        if self.pobladas[pos]:
            return
        contenido = self.repo_cripta.contenidos[pos]
        if contenido is None:
            raise ErrorReproduccion(f"El contenido de la sala {sala.id} no está guardado")
        self._instalar_contenido(sala, contenido, pos)

    #lo que `restaurar` necesita para armar entidades por id
    def _objeto_de_catalogo(self, id_instancia, id_catalogo):
        return self.crear_objeto(id_instancia, self._ficha(id_catalogo))

    def _indexar(self):
        enemigos = []
        trampas = []
        for contenido in self.repo_cripta.contenidos:
            if contenido is None:
                continue
            for instancia in contenido.enemigos:
                enemigos.append((instancia.instancia, instancia))
            for instancia in contenido.trampas:
                trampas.append((instancia.instancia, instancia))
        self._enemigos = _vector_de(enemigos)
        self._trampas = _vector_de(trampas)

    def _enemigo_por_id(self, id_enemigo):
        if self._enemigos is None:
            self._indexar()
        instancia = self._enemigos.buscar(id_enemigo)
        if instancia is None:
            raise ErrorReproduccion(f"El enemigo {id_enemigo} no está en el contenido guardado")
        return self.crear_enemigo(instancia, self._ficha(instancia.tipo), None)

    def _trampa_por_id(self, id_instancia):
        if self._trampas is None:
            self._indexar()
        instancia = self._trampas.buscar(id_instancia)
        if instancia is None:
            raise ErrorReproduccion(f"La trampa {id_instancia} no está en el contenido guardado")
        return self.crear_trampa(instancia, self._ficha(instancia.tipo))
