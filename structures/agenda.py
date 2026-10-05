class Evento:
    #Un evento programado en el reloj virtual

    def __init__(self, tiempo, num_sec, tipo, dueno=None, datos=None):
        self.tiempo = tiempo   #tiempo de la cita del evento
        self.num_sec = num_sec        #orden 
        self.tipo = tipo       #accion, veneno, cierre_puerta
        self.dueno = dueno     #a quién pertenece
        self.datos = datos
        self.pos = -1          #posición en el heap; -1 = no está pendiente


class AgendaEventos:
    def __init__(self):
        self.heap = []     #la lista donde vive el heap
        self.num_sec = 0       #contador de secuencia

    def __len__(self):
        return len(self.heap)

    def _menor(self, a, b):
        #True si el evento a va antes que el evento b.
        if a.tiempo != b.tiempo:
            return a.tiempo < b.tiempo
        return a.num_sec < b.num_sec

    def _intercambiar(self, i, j):
        h = self.heap
        h[i], h[j] = h[j], h[i]
        h[i].pos = i
        h[j].pos = j

    def _subir(self, i):
        h = self.heap
        while i > 0:
            padre = (i - 1) // 2
            if not self._menor(h[i], h[padre]):
                break
            self._intercambiar(i, padre)
            i = padre

    def programar(self, tiempo, tipo, dueno=None, datos=None):
        event = Evento(tiempo, self.num_sec, tipo, dueno, datos)
        self.num_sec += 1
        event.pos = len(self.heap)
        self.heap.append(event)
        self._subir(event.pos)
        return event
    
    def _bajar(self, i):
        h = self.heap
        n = len(h)
        while True:
            izq = 2 * i + 1
            der = 2 * i + 2
            menor = i
            if izq < n and self._menor(h[izq], h[menor]):
                menor = izq
            if der < n and self._menor(h[der], h[menor]):
                menor = der
            if menor == i:
                break
            self._intercambiar(i, menor)
            i = menor

    def proximo(self):
        #Mira el evento más temprano 
        if not self.heap:
            return None
        return self.heap[0]

    def extraer(self):
        #Saca y devuelve el evento más temprano
        if not self.heap:
            return None
        self._intercambiar(0, len(self.heap) - 1)
        event = self.heap.pop()
        event.pos = -1              # ya no está pendiente
        if self.heap:
            self._bajar(0)
        return event
    
    def _reubicar(self, i):
        #Acomoda el evento en la posición i donde convenga
        if i > 0 and self._menor(self.heap[i], self.heap[(i - 1) // 2]):
            self._subir(i)
        else:
            self._bajar(i)

    def cancelar(self, event):
        #Quita un evento pendiente
        if event.pos < 0:
            return False             # ya no estaba en la agenda
        i = event.pos
        ultimo = len(self.heap) - 1
        self._intercambiar(i, ultimo)
        self.heap.pop()
        event.pos = -1
        if i < len(self.heap):       # si no cancelamos justo el último
            self._reubicar(i)
        return True

    def reprogramar(self, event, nuevo_tiempo):
        #Cambia el tiempo de un evento pendiente y le da un número de secuencia nuevo
        if event.pos < 0:
            raise ValueError("El evento no está pendiente")
        event.tiempo = nuevo_tiempo
        event.num_sec = self.num_sec
        self.num_sec += 1
        self._reubicar(event.pos)
