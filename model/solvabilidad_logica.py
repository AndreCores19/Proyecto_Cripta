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
        nombradas_ausentes = []         # ids que esas salidas nombran y la lista no da

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
                            nombradas_ausentes.append(salida.llave)
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
