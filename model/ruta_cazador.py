from model.sala_logica import Salida
from structures.monticulo import MonticuloMinimo


class Busqueda:
    """Dijkstra acotado hacia atrás desde la sala del jugador.

    Marca las salas con una estampa en Sala.busq_marca / busq_dist: no hay nada
    que limpiar entre búsquedas. El contador de estampas es de la clase, así que
    una estampa nunca se repite aunque alternen varios objetos Busqueda.
    """

    ultima_estampa = -1
    busquedas = 0  #cuántas búsquedas se han hecho (para medir)

    @classmethod
    def nueva_estampa(cls):
        cls.ultima_estampa += 1
        return cls.ultima_estampa

    def calcular(self, origen, limite):
        """Calcula la distancia de cada sala alcanzable (<= limite) hasta `origen`. Devuelve la estampa."""
        Busqueda.busquedas += 1
        estampa = Busqueda.nueva_estampa()
        origen.busq_marca = estampa
        origen.busq_dist = 0
        frontera = MonticuloMinimo()
        frontera.insertar(0, origen)
        while True:
            nodo = frontera.extraer()
            if nodo is None:
                break
            d, sala = nodo
            if d > limite:
                break
            if d > sala.busq_dist:
                continue  #entrada vieja: ya se halló algo mejor
            for entrada in sala.entradas:
                if entrada.cerrada:
                    continue
                nd = d + entrada.costo
                if nd > limite:
                    continue
                vecina = entrada.origen
                if vecina.busq_marca != estampa or nd < vecina.busq_dist:
                    vecina.busq_marca = estampa
                    vecina.busq_dist = nd
                    frontera.insertar(nd, vecina)
        return estampa

    def distancia(self, sala, estampa):
        if sala.busq_marca == estampa:
            return sala.busq_dist
        return None


MODOS = ("individual", "compartido_sin_reuso", "compartido")


class DecisorCazador:
    """Decide la salida de un cazador.

    individual: una búsqueda por turno con el rango del cazador.
    compartido_sin_reuso: una búsqueda por turno con el mayor rango entre los cazadores vivos.
    compartido: igual, pero reutiliza la búsqueda mientras el estado no cambie.
    """

    def __init__(self, modo="individual"):
        if modo not in MODOS:
            raise ValueError(f"modo de decisor desconocido: {modo}")
        self.modo = modo
        self.busqueda = Busqueda()
        #búsqueda guardada (solo modo compartido)
        self.sala_jugador = None
        self.epoca = -1
        self.limite = -1
        self.estampa = -1

    def _limite(self, partida, cazador):
        limite = cazador.rango
        if self.modo == "individual":
            return limite
        for e in partida.enemigos:
            if e.es_cazador() and e.esta_vivo() and e.rango > limite:
                limite = e.rango
        return limite

    def _cache_valida(self, partida, cazador):
        return (partida.jugador.sala is self.sala_jugador
                and Salida.epoca_puertas == self.epoca
                and cazador.rango <= self.limite
                and Busqueda.ultima_estampa == self.estampa)

    def _estampa(self, partida, cazador, limite):
        if self.modo != "compartido":
            return self.busqueda.calcular(partida.jugador.sala, limite)
        if not self._cache_valida(partida, cazador):
            self.estampa = self.busqueda.calcular(partida.jugador.sala, limite)
            self.sala_jugador = partida.jugador.sala
            self.epoca = Salida.epoca_puertas
            self.limite = limite
        return self.estampa

    def decidir(self, partida, cazador, limite_forzado=None):
        limite = limite_forzado if limite_forzado is not None else self._limite(partida, cazador)
        if limite < cazador.rango:
            raise RuntimeError("el límite de la búsqueda es menor que el rango del cazador")
        estampa = self._estampa(partida, cazador, limite)
        d = self.busqueda.distancia(cazador.sala, estampa)
        if d is None or d > cazador.rango:
            return None
        mejor = None
        for s in cazador.sala.salidas:
            if s.cerrada:
                continue
            resto = self.busqueda.distancia(s.destino, estampa)
            if resto is None or s.costo + resto != d:
                continue
            if mejor is None or (s.destino.id, s.direccion) < (mejor.destino.id, mejor.direccion):
                mejor = s
        return mejor
