class Salida:
    def __init__(self, direccion, destino, cerrada=False, llave=None, cierre_automatico=None):
        self.direccion = direccion    
        self.destino = destino           #Sala
        self.cerrada = cerrada
        self.llave = llave               #id de la llave que la abre
        self.cierre_automatico = cierre_automatico


class Sala:
    def __init__(self, id_sala, nombre):
        self.id = id_sala
        self.nombre = nombre
        self.salidas = []        #tiene 4 salidas como máximo
        self.rastro = None       # último instante en que el jugador estuvo aquí
        self.inactivos = []       
        self.objetos = []        # objetos en el suelo

    def agregar_salida(self, salida):
        self.salidas.append(salida)

    def salida(self, direccion):
        #Busca la salida en esa dirección y recorre como máximo 4 
        for s in self.salidas:
            if s.direccion == direccion:
                return s
        return None