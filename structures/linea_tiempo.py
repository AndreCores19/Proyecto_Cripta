class LineaTiempo:
    """Las acciones del jugador que sobreviven y los puntos de control cada K acciones.

    Tres vectores paralelos (índice = número de acción − 1) para que la búsqueda por reloj solo
    toque enteros. `puntos[i]` es el estado con i·K acciones hechas; nunca hay uno fuera de esa
    cuadrícula. Solo se agrega y se recorta por el final.
    """

    def __init__(self, k):
        if type(k) is not int or k <= 0:
            raise ValueError("K debe ser un entero positivo")
        self.k = k
        self.relojes = []        #reloj de la decisión de cada acción, estrictamente creciente
        self.tipos = []
        self.argumentos = []
        self.puntos = []         #puntos[i]: estado con i·K acciones hechas
        self.omitidos = []       #libro de efectos omitidos, cronológico (lo llena la fase 5)
        self.reloj_decision_pendiente = None
        self.reloj_final = 0
        self.comparaciones = 0   #para medir que la búsqueda por reloj es O(log n)
        self.operaciones_retroceso = 0   #trabajo de los recortes: registros y puntos borrados, entradas reetiquetadas

    def __len__(self):
        return len(self.relojes)

    def agregar_accion(self, reloj, tipo, argumento=None):
        if self.relojes and reloj <= self.relojes[-1]:
            raise ValueError("Los relojes de las acciones deben ser estrictamente crecientes")
        self.relojes.append(reloj)
        self.tipos.append(tipo)
        self.argumentos.append(argumento)

    def agregar_punto(self, punto):
        #el punto que se agrega es el de la frontera len(puntos)·K; no puede haber otro
        if len(self.puntos) * self.k > len(self.relojes):
            raise ValueError("Ese punto de control queda fuera de la cuadrícula de K")
        self.puntos.append(punto)

    def punto_para(self, frontera):
        #frontera = acciones ya hechas; el punto que le sirve es el de la casilla frontera // K
        if frontera < 0:
            raise ValueError("La frontera no puede ser negativa")
        casilla = frontera // self.k
        if casilla >= len(self.puntos):
            raise IndexError("Todavía no hay un punto de control para esa frontera")
        return self.puntos[casilla]

    def ultimo_menor_o_igual(self, t):
        #índice (desde 0) de la última acción cuyo reloj es <= t, o -1 si t es menor que todos
        bajo = 0
        alto = len(self.relojes) - 1
        resultado = -1
        while bajo <= alto:
            medio = (bajo + alto) // 2
            self.comparaciones += 1
            if self.relojes[medio] <= t:
                resultado = medio
                bajo = medio + 1
            else:
                alto = medio - 1
        return resultado

    def recortar(self, n):
        #deja las primeras n acciones y los puntos con frontera <= n; borra solo desde el final.
        #Las entradas del libro con etiqueta > n pasan a n y a `reaplicar` (el trabajo es el de lo recortado)
        if n < 0 or n > len(self.relojes):
            raise ValueError("No se puede recortar a esa cantidad de acciones")
        while len(self.relojes) > n:
            del self.relojes[-1]
            del self.tipos[-1]
            del self.argumentos[-1]
            self.operaciones_retroceso += 1
        while len(self.puntos) > 0 and (len(self.puntos) - 1) * self.k > n:
            del self.puntos[-1]
            self.operaciones_retroceso += 1
        #las etiquetas no bajan a lo largo del libro: se mira desde el final y se para al llegar a una menor que n
        i = len(self.omitidos) - 1
        while i >= 0 and self.omitidos[i].etiqueta >= n:
            entrada = self.omitidos[i]
            if entrada.etiqueta > n:                    #de una acción revertida: se guarda para aplicarlo en n
                entrada.etiqueta = n
                entrada.reaplicar = True
                self.operaciones_retroceso += 1
            i -= 1                                      #(con etiqueta n: o ya guardada, o de una acción que sobrevivió)

    def omitidos_en(self, frontera):
        #las entradas guardadas por un pergamino que se aplican con `frontera` acciones hechas, en orden
        return [e for e in self.omitidos if e.reaplicar and e.etiqueta == frontera]

    def descartar_vencidos(self, limite):
        #quita las candidatas (no guardadas) con etiqueta <= limite: su acción ya no se puede revertir.
        #Las etiquetas no bajan, así que solo se mira el comienzo del libro.
        fin = 0
        while fin < len(self.omitidos) and self.omitidos[fin].etiqueta <= limite:
            fin += 1
        if fin == 0:
            return
        escritura = 0
        for lectura in range(len(self.omitidos)):
            entrada = self.omitidos[lectura]
            if lectura < fin and not entrada.reaplicar:
                continue
            self.omitidos[escritura] = entrada
            escritura += 1
        while len(self.omitidos) > escritura:
            del self.omitidos[-1]
