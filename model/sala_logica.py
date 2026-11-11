from model.tiempo_logica import COSTO_MOVER


class Salida:
    def __init__(self, direccion, destino, cerrada=False, llave=None, cierre_automatico=None, costo=None):
        self.direccion = direccion
        self.destino = destino
        self.cerrada = cerrada
        self.llave = llave
        self.cierre_automatico = cierre_automatico
        self.costo_declarado = costo  #None si los datos no lo declaran
        self.opuesta = None  #la Salida gemela

    @property
    def costo(self):
        #costo de cruzar la salida: el declarado o, si no hay, el de mover
        return self.costo_declarado if self.costo_declarado is not None else COSTO_MOVER

    def enlazar(self, otra):
        #soluciona la relación entre dos salidas
        #Une dos Salida como las dos caras de una misma puerta y si alguna viene
        #cerrada, las dos quedan cerradas
        self.opuesta = otra
        otra.opuesta = self
        cerrada = self.cerrada or otra.cerrada
        llave = self.llave if self.llave is not None else otra.llave
        cierre = (self.cierre_automatico if self.cierre_automatico is not None
                  else otra.cierre_automatico)
        #el costo declarado en un solo lado vale para los dos (FR-005)
        costo = (self.costo_declarado if self.costo_declarado is not None
                 else otra.costo_declarado)
        for cara in (self, otra):
            cara.cerrada = cerrada
            cara.llave = llave
            cara.cierre_automatico = cierre
            cara.costo_declarado = costo


class Sala:
    def __init__(self, id_sala, nombre):
        self.id = id_sala
        self.nombre = nombre
        self.salidas = []        
        self.rastro = None       #último instante en que el jugador estuvo aquí
        self.inactivos = []     
        self.objetos = []        
        self.trampas = []       

    def agregar_salida(self, salida):
        self.salidas.append(salida)

    def salida(self, direccion):
        for s in self.salidas:
            if s.direccion == direccion:
                return s
        return None