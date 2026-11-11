class MonticuloMinimo:
    """Montículo binario mínimo sobre una lista.

    Cada nodo es (prioridad, secuencia, valor). Se ordena por prioridad usando
    solo `<`; a igual prioridad sale primero el insertado antes (secuencia).
    """

    def __init__(self):
        self.nodos = []
        self.secuencia = 0

    def __len__(self):
        return len(self.nodos)

    def _antes(self, a, b):
        if a[0] < b[0]:
            return True
        if b[0] < a[0]:
            return False
        return a[1] < b[1]

    def insertar(self, prioridad, valor):
        self.nodos.append((prioridad, self.secuencia, valor))
        self.secuencia += 1
        i = len(self.nodos) - 1
        while i > 0:
            padre = (i - 1) // 2
            if self._antes(self.nodos[i], self.nodos[padre]):
                self.nodos[i], self.nodos[padre] = self.nodos[padre], self.nodos[i]
                i = padre
            else:
                break

    def proximo(self):
        if not self.nodos:
            return None
        return (self.nodos[0][0], self.nodos[0][2])

    def extraer(self):
        if not self.nodos:
            return None
        raiz = self.nodos[0]
        ultimo = self.nodos.pop()
        n = len(self.nodos)
        if n > 0:
            self.nodos[0] = ultimo
            i = 0
            while True:
                menor = i
                izq = 2 * i + 1
                der = izq + 1
                if izq < n and self._antes(self.nodos[izq], self.nodos[menor]):
                    menor = izq
                if der < n and self._antes(self.nodos[der], self.nodos[menor]):
                    menor = der
                if menor == i:
                    break
                self.nodos[i], self.nodos[menor] = self.nodos[menor], self.nodos[i]
                i = menor
        return (raiz[0], raiz[2])

    def vaciar(self):
        self.nodos = []
        self.secuencia = 0
