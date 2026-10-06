class Evento:
    def __init__(self, tiempo, num_sec, tipo, dueno=None, datos=None):
        self.tiempo = tiempo       
        self.num_sec = num_sec     
        self.tipo = tipo           
        self.dueno = dueno         
        self.datos = datos
        self.pos = -1          


class AgendaEventos:
    def __init__(self):
        self.heap = []
        self.num_sec = 0

    def __len__(self):
        return len(self.heap)

    def _menor(self, a, b):
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

    def _reubicar(self, i):
        if i > 0 and self._menor(self.heap[i], self.heap[(i - 1) // 2]):
            self._subir(i)
        else:
            self._bajar(i)

    def programar(self, tiempo, tipo, dueno=None, datos=None):
        event = Evento(tiempo, self.num_sec, tipo, dueno, datos)
        self.num_sec += 1
        event.pos = len(self.heap)
        self.heap.append(event)
        self._subir(event.pos)
        return event

    def proximo(self):
        if not self.heap:
            return None
        return self.heap[0]

    def extraer(self):
        if not self.heap:
            return None
        self._intercambiar(0, len(self.heap) - 1)
        event = self.heap.pop()
        event.pos = -1
        if self.heap:
            self._bajar(0)
        return event

    def cancelar(self, event):
        if event.pos < 0:
            return False
        i = event.pos
        ultimo = len(self.heap) - 1
        self._intercambiar(i, ultimo)
        self.heap.pop()
        event.pos = -1
        if i < len(self.heap):
            self._reubicar(i)
        return True

    def reprogramar(self, event, nuevo_tiempo):
        if event.pos < 0:
            raise ValueError("El evento no está pendiente")
        event.tiempo = nuevo_tiempo
        event.num_sec = self.num_sec
        self.num_sec += 1
        self._reubicar(event.pos)