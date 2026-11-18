from structures.cola import Cola
from structures.monticulo import MonticuloMinimo
from structures.ordenamientos import ordenar
from structures.vector_busqueda import VectorBusqueda


class LlaveLogica:
    """Una llave y su ubicación. `id_sala` es None si la lista de llaves no la da (solo la nombra una puerta)."""

    def __init__(self, id, id_sala, id_enemigo=None):
        self.id = id
        self.id_sala = id_sala          # sala donde está; si la lleva un enemigo, la sala donde él empieza (FR-003)
        self.id_enemigo = id_enemigo
        self.obtenida = False
        self.pendientes = []            # salidas cerradas que esperan esta llave
        self.visita = None              # id de la llave desde la que se llegó a esta, al buscar ciclos
        self.guardia = None             # LlaveLogica que guarda su región (barrido de ciclos)
        self.puerta_guardia = None      # Salida de la frontera por la que se llega a esa región


class Eslabon:
    """Un paso de un ciclo: la llave, su sala, la llave que la guarda y la puerta de la frontera."""

    def __init__(self, llave, guardia, puerta):
        self.id_llave = llave.id
        self.id_sala = llave.id_sala
        self.id_guardia = guardia.id
        self.puerta = puerta


class ResultadoVerificacion:
    def __init__(self):
        self.resoluble = False
        self.orden = []             # ids de llaves, en el orden en que se toman
        self.inalcanzables = []     # LlaveLogica sin tomar (y las nombradas que la lista no da), por id
        self.frontera = []          # Salida cerradas desde salas alcanzadas hacia salas no alcanzadas
        self.ciclos = []            # lista de listas de Eslabon
        self.visitas_salas = 0      # salas sacadas de la cola (para comprobar que no hay una pasada por llave)
        self.examenes_salidas = 0   # salidas examinadas desde su origen


class Verificador:
    """Decide si una cripta se puede ganar y explica por qué no, en una pasada (FR-008 a FR-013).

    La región alcanzable y las llaves tomadas crecen juntas: llegar a una sala vuelve obtenibles las llaves
    que hay en ella (van a un montículo ordenado por id), se toma la de menor id, se liberan las puertas que
    la esperaban y la región vuelve a crecer. Nunca hay una pasada completa por llave. No lee el
    conocimiento del jugador (FR-001) ni modifica la cripta.
    """

    def verificar(self, salas, id_inicial, id_salida, id_llave_salida, llaves):
        """`salas`: VectorBusqueda de salas (ids en orden creciente); `llaves`: lista de LlaveLogica."""
        resultado = ResultadoVerificacion()
        n = salas.tamano()
        pos_inicial = salas.posicion(id_inicial)
        if pos_inicial == -1:
            raise ValueError(f"La sala inicial {id_inicial} no existe")

        unicas = self._unicas(llaves)
        vector_llaves = VectorBusqueda()
        for llave in unicas:
            vector_llaves.agregar(llave.id, llave)
        vector_llaves.preparar()

        alcanzada = [False] * n
        llaves_en = [[] for _ in range(n)]
        for llave in unicas:
            pos = salas.posicion(llave.id_sala)
            if pos != -1:
                llaves_en[pos].append(llave)

        cola = Cola()
        obtenibles = MonticuloMinimo()
        sin_abrir = []                  # salidas cerradas que nadie puede abrir (sin llave, o llave que la lista no da)

        alcanzada[pos_inicial] = True
        cola.encolar(pos_inicial)
        while True:
            while not cola.esta_vacia():
                pos = cola.desencolar()
                resultado.visitas_salas += 1
                sala = salas.valores[pos]
                for llave in llaves_en[pos]:
                    obtenibles.insertar(llave.id, llave)
                for salida in sala.salidas:
                    resultado.examenes_salidas += 1
                    destino = salas.posicion(salida.destino.id)
                    if alcanzada[destino]:
                        continue
                    if not salida.cerrada:
                        alcanzada[destino] = True
                        cola.encolar(destino)
                    elif salida.llave is None:
                        sin_abrir.append(salida)
                    else:
                        llave = vector_llaves.buscar(salida.llave)
                        if llave is None:
                            sin_abrir.append(salida)
                        elif llave.obtenida:
                            alcanzada[destino] = True
                            cola.encolar(destino)
                        else:
                            llave.pendientes.append(salida)
            tomada = obtenibles.extraer()
            if tomada is None:
                break
            llave = tomada[1]
            llave.obtenida = True
            resultado.orden.append(llave.id)
            for salida in llave.pendientes:
                destino = salas.posicion(salida.destino.id)
                if not alcanzada[destino]:
                    alcanzada[destino] = True
                    cola.encolar(destino)
            llave.pendientes = []

        resultado.resoluble = self._decidir(salas, alcanzada, id_salida, id_llave_salida, vector_llaves)
        self._informe(resultado, salas, alcanzada, unicas, sin_abrir, id_llave_salida, vector_llaves)
        return resultado

    @staticmethod
    def _unicas(llaves):
        """Una entrada por id: la de menor id de sala, así el resultado no depende del orden del listado (FR-002)."""
        ordenadas = ordenar(llaves, lambda k: (k.id, k.id_sala))
        unicas = []
        for llave in ordenadas:
            if not unicas or unicas[-1].id != llave.id:
                unicas.append(llave)
        return unicas

    @staticmethod
    def _decidir(salas, alcanzada, id_salida, id_llave_salida, vector_llaves):
        """Resoluble: la llave de salida se tomó y una salida que la exige lleva a la sala de salida desde una sala alcanzada."""
        llave = vector_llaves.buscar(id_llave_salida)
        if llave is None or not llave.obtenida:
            return False
        pos_salida = salas.posicion(id_salida)
        if pos_salida == -1:
            return False
        for entrada in salas.valores[pos_salida].entradas:
            if entrada.llave == id_llave_salida and alcanzada[salas.posicion(entrada.origen.id)]:
                return True
        return False

    def _informe(self, resultado, salas, alcanzada, unicas, sin_abrir, id_llave_salida, vector_llaves):
        sin_tomar = [llave for llave in unicas if not llave.obtenida]
        # frontera: las salidas que esperan una llave sin tomar y las que nadie puede abrir, hacia salas no alcanzadas
        frontera = []
        puertas_con_llave = []
        nombradas = []                  # ids que las puertas de la frontera nombran y la lista no da
        for llave in sin_tomar:
            for salida in llave.pendientes:
                if not alcanzada[salas.posicion(salida.destino.id)]:
                    frontera.append(salida)
                    puertas_con_llave.append((llave, salida))
        for salida in sin_abrir:
            if not alcanzada[salas.posicion(salida.destino.id)]:
                frontera.append(salida)
                if salida.llave is not None:
                    nombradas.append(salida.llave)
        resultado.frontera = ordenar(frontera, lambda s: (s.origen.id, s.direccion))
        # ids nombrados por una puerta de la frontera (o la salida) que la lista no da: entradas que nunca se obtienen
        nombres = ordenar(nombradas, lambda x: x)
        if id_llave_salida is not None and vector_llaves.buscar(id_llave_salida) is None:
            nombres = ordenar(nombres + [id_llave_salida], lambda x: x)
        ausentes = []
        for nombre in nombres:
            if not ausentes or ausentes[-1].id != nombre:
                ausentes.append(LlaveLogica(nombre, None, None))
        resultado.inalcanzables = ordenar(sin_tomar + ausentes, lambda k: k.id)
        resultado.ciclos = self._ciclos(salas, alcanzada, sin_tomar, puertas_con_llave)

    @staticmethod
    def _ciclos(salas, alcanzada, sin_tomar, puertas_con_llave):
        """Barrido lineal sobre las salas que la pasada no alcanzó: la guardiana de cada llave sin tomar es la
        menor llave de la frontera que llega a su sala ignorando las cerraduras; luego se siguen las guardianas."""
        if not sin_tomar:
            return []
        n = salas.tamano()
        etiqueta_llave = [None] * n
        etiqueta_puerta = [None] * n
        puertas = ordenar(puertas_con_llave, lambda x: (x[0].id, x[1].origen.id, x[1].direccion))
        for llave, puerta in puertas:
            inicio = salas.posicion(puerta.destino.id)
            if etiqueta_llave[inicio] is not None:
                continue
            etiqueta_llave[inicio] = llave
            etiqueta_puerta[inicio] = puerta
            pila = [inicio]
            while pila:
                pos = pila.pop()
                for salida in salas.valores[pos].salidas:
                    vecina = salas.posicion(salida.destino.id)
                    if not alcanzada[vecina] and etiqueta_llave[vecina] is None:
                        etiqueta_llave[vecina] = llave
                        etiqueta_puerta[vecina] = puerta
                        pila.append(vecina)
        for llave in sin_tomar:
            pos = salas.posicion(llave.id_sala)
            if pos != -1 and etiqueta_llave[pos] is not None:
                llave.guardia = etiqueta_llave[pos]
                llave.puerta_guardia = etiqueta_puerta[pos]
        ciclos = []
        for inicio in sin_tomar:            # ya ordenadas por id
            if inicio.visita is not None:
                continue
            camino = []
            actual = inicio
            while actual is not None and actual.visita is None:
                actual.visita = inicio.id
                camino.append(actual)
                actual = actual.guardia
            if actual is not None and actual.visita == inicio.id:
                ciclo = camino[camino.index(actual):]
                menor = 0
                for i in range(len(ciclo)):
                    if ciclo[i].id < ciclo[menor].id:
                        menor = i
                ciclo = ciclo[menor:] + ciclo[:menor]
                ciclos.append([Eslabon(llave, llave.guardia, llave.puerta_guardia) for llave in ciclo])
        return ordenar(ciclos, lambda c: c[0].id_llave)
