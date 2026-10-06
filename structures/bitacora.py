class Bitacora:
    #Guarda los últimos N mensajes del juego 
 
    def __init__(self, capacidad=20):
        self.capacidad = capacidad
        self.buffer = [None] * capacidad
        self.siguiente = 0     
        self.cantidad = 0     
 
    def agregar(self, mensaje):
        self.buffer[self.siguiente] = mensaje
        self.siguiente = (self.siguiente + 1) % self.capacidad
        if self.cantidad < self.capacidad:
            self.cantidad += 1
 
    def obtener_todos(self):
        #Devuelve los mensajes del más antiguo al más reciente
        if self.cantidad < self.capacidad:
            return self.buffer[:self.cantidad]
        return self.buffer[self.siguiente:] + self.buffer[:self.siguiente]