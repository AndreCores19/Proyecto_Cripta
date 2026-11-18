"""El grafo de salas aparte de las consultas `historia`: se arma una vez y se limpia entre consultas.

Armar el esqueleto (crear salas, salidas y enlazar las puertas) era la mitad del tiempo de una consulta.
La estructura del grafo (ids, nombres, salidas, destinos, opuestas, entradas, llaves, costos) no cambia
nunca; lo único que un punto de control restaurado y las acciones reproducidas pueden cambiar es:

- de cada sala: conocimiento, rastro, objetos del suelo, enemigos inactivos, trampas y la marca de la
  última búsqueda del cazador (busq_marca, busq_dist);
- de cada salida: si está cerrada y la memoria de la última observación.

`limpio()` devuelve el mismo grafo con todo eso como en el esqueleto, es decir, igual a uno recién
armado. Una consulta invalida la anterior: la partida de una consulta solo vale hasta la siguiente.
"""
from model.sala_logica import DESCONOCIDA, NO_OBSERVADA, Salida


class GrafoReutilizable:

    def __init__(self, construir):
        self.construir = construir        #función que arma el esqueleto (VectorBusqueda de salas)
        self.salas = None
        self._puertas = None              #[(salida, cerrada en el esqueleto)]

    def limpio(self):
        if self.salas is None:
            self.salas = self.construir()
            self._puertas = [(salida, salida.cerrada)
                             for sala in self.salas.valores for salida in sala.salidas]
            return self.salas
        for sala in self.salas.valores:
            sala.conocimiento = DESCONOCIDA
            sala.rastro = None
            sala.objetos = []
            sala.inactivos = []
            sala.trampas = []
            sala.busq_marca = -1
            sala.busq_dist = 0
        for salida, cerrada in self._puertas:
            if salida.cerrada != cerrada:
                salida.cerrada = cerrada
            salida.memoria = NO_OBSERVADA
        #armar un grafo nuevo siempre movía la época de las puertas; las cachés que la miran la ven moverse igual
        Salida.epoca_puertas += 1
        return self.salas
