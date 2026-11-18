"""Benchmark de la verificación de resolubilidad (FR-018, FR-019, FR-020, FR-021).

Todo es local y sembrado con random.Random(semilla): sin red y sin dibujar nada.

1. Una cripta con la forma de la mayor publicada (300 salas, 4 llaves), resoluble y no resoluble: el veredicto
   es que el máximo de las corridas sea <= 200 ms (FR-018 dice «a lo sumo 200 ms», sin percentil).
2. Crecimiento con cadenas de llaves (cada llave abre una región nueva): la verificación y la alternativa
   ingenua (una pasada completa desde cero por cada llave tomada) con las mismas criptas y el mismo orden de
   llaves. La ingenua solo llega a 10 000 salas y 200 llaves: con 100 000 salas y 2 000 llaves necesitaría unos
   2×10⁸ recorridos de sala, muchos minutos en Python.
"""
import gc
import random
import time

from model.sala_logica import Sala, Salida
from model.solvabilidad_logica import LlaveLogica, Verificador
from structures.cola import Cola
from structures.ordenamientos import ordenar
from structures.vector_busqueda import VectorBusqueda

SEMILLA = 1
LIMITE_MS = 200
SALAS_PUBLICADA = 300           # la mayor cripta publicada
LLAVES_PUBLICADA = 4
SALAS_POR_LLAVE = 50
TOPE_INGENUA_SALAS = 10000
TOPE_INGENUA_LLAVES = 200


class Config:
    """Tamaños de una corrida."""

    def __init__(self, repeticiones, tamanos, repeticiones_por_tamano):
        self.repeticiones = repeticiones                       # corridas de la cripta de 300 salas
        self.tamanos = tamanos                                 # (salas, llaves) de las cadenas
        self.repeticiones_por_tamano = repeticiones_por_tamano


NORMAL = Config(200, ((100, 2), (1000, 20), (10000, 200), (100000, 2000)), (5, 5, 3, 1))
PEQUENO = Config(5, ((60, 2), (300, 6)), (1, 1))


class Cripta:
    """Una cripta sintética: salas en un vector de búsqueda, sala inicial y de salida, llave de salida y llaves."""

    def __init__(self, salas, sala_inicial, sala_salida, llave_salida, llaves):
        self.salas = salas                    # VectorBusqueda
        self.sala_inicial = sala_inicial
        self.sala_salida = sala_salida
        self.llave_salida = llave_salida
        self.llaves = llaves                  # tuplas (id, id_sala, id_enemigo)

    def llaves_logicas(self):
        return [LlaveLogica(i, s, e) for i, s, e in self.llaves]


def _id_llave(i):
    return f"k{i:05d}"


def _unir(a, b, llave=None):
    """Puerta entre dos salas: dos caras enlazadas, cerradas y con la misma llave si hay llave."""
    cerrada = llave is not None
    ida = Salida(f"d{len(a.salidas)}", b, cerrada=cerrada, llave=llave, costo=100)
    vuelta = Salida(f"d{len(b.salidas)}", a, cerrada=cerrada, llave=llave, costo=100)
    a.agregar_salida(ida)
    b.agregar_salida(vuelta)
    ida.enlazar(vuelta)


def _vector(salas):
    vector = VectorBusqueda()
    for sala in salas:
        vector.agregar(sala.id, sala)
    vector.preparar()
    return vector


def armar_publicada(semilla, resoluble=True, num_salas=SALAS_PUBLICADA):
    """Cripta con la forma de la mayor publicada: 300 salas y 4 llaves (tres puertas encadenadas y la de salida).

    Árbol sembrado; las puertas de cuatro salas «compuerta» se cierran con las llaves 1 a 4; la llave 1 está en la
    sala inicial y la llave t+1 está en la compuerta t-1. La puerta de la última compuerta exige la llave de
    salida. Si `resoluble` es False, la llave de salida queda en su propia compuerta (detrás de su única puerta).
    """
    azar = random.Random(semilla)
    salas = [Sala(i + 1, f"Sala {i + 1}") for i in range(num_salas)]
    compuertas = sorted(azar.sample(range(1, num_salas), LLAVES_PUBLICADA))
    for i in range(1, num_salas):
        llave = None
        if i in compuertas:
            llave = _id_llave(compuertas.index(i) + 1)
        _unir(salas[azar.randrange(i)], salas[i], llave)
    llaves = [(_id_llave(1), 1, None)]
    for t in range(1, LLAVES_PUBLICADA):
        llaves.append((_id_llave(t + 1), compuertas[t - 1] + 1, None))
    if not resoluble:
        llaves[-1] = (_id_llave(LLAVES_PUBLICADA), compuertas[-1] + 1, None)
    return Cripta(_vector(salas), 1, compuertas[-1] + 1, _id_llave(LLAVES_PUBLICADA), llaves)


def armar_cadena(semilla, num_salas, num_llaves):
    """Cadena de llaves: la llave s abre la puerta hacia el tramo s y está en el tramo s-1 (cada llave abre una región nueva).

    Hay num_llaves + 1 tramos de num_salas // (num_llaves + 1) salas; dentro de un tramo, un árbol sembrado de
    puertas abiertas; la primera sala de cada tramo s >= 1 se une a una sala del tramo anterior con una puerta
    cerrada que exige la llave s. La salida es la primera sala del último tramo, tras la puerta de la última llave.
    """
    paso = num_salas // (num_llaves + 1)
    if paso < 1:
        raise ValueError("hay más llaves que salas")
    azar = random.Random(semilla)
    total = paso * (num_llaves + 1)
    salas = [Sala(i + 1, f"Sala {i + 1}") for i in range(total)]
    llaves = []
    for tramo in range(num_llaves + 1):
        inicio = tramo * paso
        for o in range(paso):
            if o == 0 and tramo == 0:
                continue
            if o == 0:
                anterior = (tramo - 1) * paso
                _unir(salas[anterior + azar.randrange(paso)], salas[inicio], _id_llave(tramo))
            else:
                _unir(salas[inicio + azar.randrange(o)], salas[inicio + o], None)
        if tramo < num_llaves:
            llaves.append((_id_llave(tramo + 1), inicio + azar.randrange(paso) + 1, None))
    return Cripta(_vector(salas), 1, num_llaves * paso + 1, _id_llave(num_llaves), llaves)


def verificar(cripta):
    """La verificación del modelo sobre llaves nuevas (cada corrida marca sus propias llaves)."""
    return Verificador().verificar(cripta.salas, cripta.sala_inicial, cripta.sala_salida, cripta.llave_salida,
                                   cripta.llaves_logicas())


def verificar_ingenuo(cripta):
    """Alternativa descartada: una pasada completa desde cero después de cada llave tomada (siempre la de menor id).

    Costo O(K (V + E log K)). Devuelve el orden de llaves.
    """
    salas = cripta.salas
    llaves = ordenar(cripta.llaves_logicas(), lambda k: (k.id, k.id_sala))
    unicas = []
    for llave in llaves:
        if not unicas or unicas[-1].id != llave.id:
            unicas.append(llave)
    vector = VectorBusqueda()
    for llave in unicas:
        vector.agregar(llave.id, llave)
    vector.preparar()
    orden = []
    while True:
        alcanzada = [False] * salas.tamano()
        pos = salas.posicion(cripta.sala_inicial)
        alcanzada[pos] = True
        cola = Cola()
        cola.encolar(pos)
        while not cola.esta_vacia():
            sala = salas.valores[cola.desencolar()]
            for salida in sala.salidas:
                destino = salas.posicion(salida.destino.id)
                if alcanzada[destino]:
                    continue
                abre = not salida.cerrada
                if not abre and salida.llave is not None:
                    llave = vector.buscar(salida.llave)
                    abre = llave is not None and llave.obtenida
                if abre:
                    alcanzada[destino] = True
                    cola.encolar(destino)
        mejor = None
        for llave in unicas:
            if llave.obtenida:
                continue
            posicion = salas.posicion(llave.id_sala)
            if posicion != -1 and alcanzada[posicion] and (mejor is None or llave.id < mejor.id):
                mejor = llave
        if mejor is None:
            return orden
        mejor.obtenida = True
        orden.append(mejor.id)


def medir_verificacion(cripta, repeticiones):
    """Microsegundos de Verificador.verificar en cada corrida."""
    tiempos = []
    gc.disable()
    try:
        for _ in range(repeticiones):
            llaves = cripta.llaves_logicas()
            inicio = time.perf_counter()
            Verificador().verificar(cripta.salas, cripta.sala_inicial, cripta.sala_salida, cripta.llave_salida,
                                    llaves)
            tiempos.append((time.perf_counter() - inicio) * 1_000_000)
    finally:
        gc.enable()
    return tiempos


def _resumen_ms(tiempos):
    """(promedio, p99, máximo) en milisegundos, con el p99 como en bench_ciclo."""
    ordenados = ordenar(tiempos, lambda t: t)
    return (sum(tiempos) / len(tiempos) / 1000, ordenados[int(len(ordenados) * 0.99)] / 1000,
            ordenados[-1] / 1000)


def _una_vez_ms(funcion, cripta, repeticiones):
    mejor = None
    for _ in range(repeticiones):
        inicio = time.perf_counter()
        funcion(cripta)
        ms = (time.perf_counter() - inicio) * 1000
        if mejor is None or ms < mejor:
            mejor = ms
    return mejor


def _razon(actual, anterior):
    return "-" if anterior is None or actual is None else f"{actual / anterior:.1f}"


def ejecutar(pequeno=False):
    cfg = PEQUENO if pequeno else NORMAL
    print(f"Benchmark de la verificación de resolubilidad (semilla {SEMILLA}; milisegundos)")
    print(f"\nCripta con la forma de la mayor publicada ({SALAS_PUBLICADA} salas, {LLAVES_PUBLICADA} llaves), "
          f"{cfg.repeticiones} corridas")
    print(f"  {'':<13} {'prom':>9} {'p99':>9} {'max':>9}   (ms)")
    peor = 0.0
    for nombre, resoluble in (("resoluble", True), ("no resoluble", False)):
        tiempos = medir_verificacion(armar_publicada(SEMILLA, resoluble), cfg.repeticiones)
        promedio, p99, maximo = _resumen_ms(tiempos)
        peor = max(peor, maximo)
        print(f"  {nombre:<13} {promedio:>9.3f} {p99:>9.3f} {maximo:>9.3f}")
    cumple = "cumple" if peor <= LIMITE_MS else "NO cumple"
    print(f"Veredicto con {SALAS_PUBLICADA} salas: máximo = {peor:.3f} ms; límite <= {LIMITE_MS} ms: {cumple}")

    print(f"\nCrecimiento con llaves encadenadas (una llave por {SALAS_POR_LLAVE} salas); la ingenua, una pasada "
          f"completa por llave, solo hasta {TOPE_INGENUA_SALAS} salas y {TOPE_INGENUA_LLAVES} llaves")
    print(f"  {'salas':>7} {'llaves':>7} {'verif ms':>10} {'ingenua ms':>11} {'razón v.':>9} {'razón i.':>9} "
          f"{'salas vis.':>11} {'salidas ex.':>12}")
    anterior_v = anterior_i = None
    for (salas, llaves), repeticiones in zip(cfg.tamanos, cfg.repeticiones_por_tamano):
        cripta = armar_cadena(SEMILLA, salas, llaves)
        resultado = verificar(cripta)
        v = _una_vez_ms(verificar, cripta, repeticiones)
        i = None
        if salas <= TOPE_INGENUA_SALAS and llaves <= TOPE_INGENUA_LLAVES:
            i = _una_vez_ms(verificar_ingenuo, cripta, 1)
            if verificar_ingenuo(cripta) != resultado.orden:
                raise RuntimeError("la alternativa ingenua decide distinto que la verificación")
        ingenua = f"{i:>11.3f}" if i is not None else f"{'-':>11}"
        print(f"  {len(cripta.salas.valores):>7} {len(cripta.llaves):>7} {v:>10.3f} {ingenua} "
              f"{_razon(v, anterior_v):>9} {_razon(i, anterior_i):>9} "
              f"{resultado.visitas_salas:>11} {resultado.examenes_salidas:>12}")
        anterior_v, anterior_i = v, i
    print("\n(razón v. e i.: tiempo de la fila contra el de la anterior; las salas y salidas visitadas "
          "crecen con el tamaño de la cripta, no con las llaves)")


if __name__ == "__main__":
    ejecutar()
