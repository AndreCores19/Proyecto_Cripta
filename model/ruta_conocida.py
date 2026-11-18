from model.ruta_cazador import Busqueda
from model.sala_logica import ABIERTA, EXPLORADA
from structures.monticulo import MonticuloMinimo


class RutaConocida:
    """Ruta de «ir a» sobre el mapa que el jugador conoce.

    Dijkstra hacia atrás desde el destino, solo por salas exploradas y por salidas
    cuya puerta se recuerda abierta; se detiene en cuanto sale del montículo la sala
    del jugador. Marca las salas con la estampa compartida de Busqueda (busq_marca /
    busq_dist), de modo que no hay nada que limpiar y la búsqueda guardada de los
    cazadores se reconoce como vieja. Nunca abre una puerta.
    """

    def __init__(self):
        self.frontera = MonticuloMinimo()    #se reutiliza: se vacía al empezar cada búsqueda

    def siguiente_paso(self, partida, destino):
        """Devuelve (salida, d) del primer paso, (None, 0) si ya está en `destino`, (None, None) si no hay ruta."""
        estampa = Busqueda.nueva_estampa()   #lo primero, antes de cualquier retorno temprano
        aqui = partida.jugador.sala
        if aqui is destino:
            return None, 0
        if destino.conocimiento != EXPLORADA:
            return None, None
        frontera = self.frontera
        frontera.vaciar()
        destino.busq_marca = estampa
        destino.busq_dist = 0
        frontera.insertar(0, destino)
        alcanzada = False
        while True:
            nodo = frontera.extraer()
            if nodo is None:
                break
            d, sala = nodo
            if d > sala.busq_dist:
                continue                     #entrada vieja: ya se halló algo mejor
            if sala is aqui:
                alcanzada = True
                break
            for entrada in sala.entradas:
                origen = entrada.origen
                if origen.conocimiento != EXPLORADA or partida.puerta_recordada(entrada) != ABIERTA:
                    continue
                nd = d + entrada.costo
                if origen.busq_marca != estampa or nd < origen.busq_dist:
                    origen.busq_marca = estampa
                    origen.busq_dist = nd
                    frontera.insertar(nd, origen)
        if not alcanzada:
            return None, None
        total = aqui.busq_dist
        mejor = None
        for s in aqui.salidas:
            vecina = s.destino
            if (vecina.conocimiento != EXPLORADA or vecina.busq_marca != estampa
                    or partida.puerta_recordada(s) != ABIERTA
                    or s.costo + vecina.busq_dist != total):
                continue
            if mejor is None or (vecina.id, s.direccion) < (mejor.destino.id, mejor.direccion):
                mejor = s
        return mejor, total
