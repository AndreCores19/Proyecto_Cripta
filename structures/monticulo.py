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
        nodos = self.nodos
        nodo = (prioridad, self.secuencia, valor)
        self.secuencia += 1
        nodos.append(nodo)
        i = len(nodos) - 1
        while i > 0:
            padre = (i - 1) // 2
            p = nodos[padre]
            #igual que _antes(nodo, p), escrito aquí para no llamar a un método en cada paso
            if prioridad < p[0] or (not p[0] < prioridad and nodo[1] < p[1]):
                nodos[i] = p
                i = padre
            else:
                break
        nodos[i] = nodo

    def proximo(self):
        if not self.nodos:
            return None
        return (self.nodos[0][0], self.nodos[0][2])

    def extraer(self):
        nodos = self.nodos
        if not nodos:
            return None
        raiz = nodos[0]
        ultimo = nodos.pop()
        n = len(nodos)
        if n > 0:
            i = 0
            pr, sq = ultimo[0], ultimo[1]
            while True:
                izq = 2 * i + 1
                if izq >= n:
                    break
                hijo = nodos[izq]
                der = izq + 1
                if der < n:
                    h2 = nodos[der]
                    #igual que _antes(h2, hijo)
                    if h2[0] < hijo[0] or (not hijo[0] < h2[0] and h2[1] < hijo[1]):
                        hijo, izq = h2, der
                #igual que _antes(hijo, ultimo)
                if hijo[0] < pr or (not pr < hijo[0] and hijo[1] < sq):
                    nodos[i] = hijo
                    i = izq
                else:
                    break
            nodos[i] = ultimo
        return (raiz[0], raiz[2])

    def vaciar(self):
        self.nodos = []
        self.secuencia = 0
