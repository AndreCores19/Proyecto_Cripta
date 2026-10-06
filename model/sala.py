class Salida:
    def __init__(self, direccion, destino, cerrada=False, llave=None, cierre_automatico=None):
        self.direccion = direccion
        self.destino = destino  
        self.cerrada = cerrada
        self.llave = llave                  
        self.cierre_automatico = cierre_automatico  


class Sala:
    def __init__(self, id_sala, nombre):
        self.id = id_sala
        self.nombre = nombre
        self.salidas = []        
        self.rastro = None       # último instante en que el jugador estuvo aquí
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