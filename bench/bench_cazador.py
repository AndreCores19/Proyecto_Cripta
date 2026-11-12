"""Benchmarks del cazador (FR-018, FR-019, FR-020): comparaciones entre modos y escalado.

Todo es local y sembrado con random.Random(semilla): sin red y sin dibujar nada.
"""
import random
import time

from bench.bench_ciclo import COSTOS_SALIDA, RANGOS_CAZADOR
from model.enemigo_logica import Enemigo
from model.jugador_logica import Jugador
from model.partida_logica import Partida
from model.ruta_cazador import Busqueda, DecisorCazador, MODOS
from model.sala_logica import Sala, Salida

SEMILLA = 1
ACCIONES = 3000
DIRECCIONES = ("N", "S", "E", "O", "NE", "NO", "SE", "SO")
SEGUIDO = 1       #un cambio de puerta por acción del jugador
CASI_NUNCA = 500  #un cambio de puerta cada 500 acciones del jugador
NUCLEO = 30       #salas de la zona que el escalado deja idéntica

NORMAL = {"acciones": 3000, "salas": 100, "muchos": (1, 10, 30, 100), "rangos": (200, 5000),
          "salas_rango": (100, 1000), "cazadores_rango": 10, "cazadores_modos": 30,
          "escalado": (100, 1000), "repeticiones": 2000}
PEQUENO = {"acciones": 20, "salas": 30, "muchos": (1, 3), "rangos": (200, 5000),
           "salas_rango": (30, 60), "cazadores_rango": 3, "cazadores_modos": 4,
           "escalado": (40, 80), "repeticiones": 20}


def _direccion_libre(sala):
    usadas = [s.direccion for s in sala.salidas]
    for d in DIRECCIONES:
        if d not in usadas:
            return d
    return None


def _conectar(a, b, costo, cerrada=False):
    da, db = _direccion_libre(a), _direccion_libre(b)
    if da is None or db is None:
        return False
    ida = Salida(da, b, cerrada=cerrada, costo=costo)
    vuelta = Salida(db, a, cerrada=cerrada, costo=costo)
    a.agregar_salida(ida)
    b.agregar_salida(vuelta)
    ida.enlazar(vuelta)
    return True


def _salas_conexas(azar, num_salas):
    """Árbol abierto más puertas extra, algunas cerradas."""
    salas = [Sala(i + 1, f"Sala {i + 1}") for i in range(num_salas)]
    for i in range(1, num_salas):
        costo = azar.choice(COSTOS_SALIDA)
        for _ in range(20):
            if _conectar(salas[azar.randrange(i)], salas[i], costo):
                break
    for _ in range(num_salas // 2):
        a, b = azar.choice(salas), azar.choice(salas)
        costo = azar.choice(COSTOS_SALIDA)
        cerrada = azar.random() < 0.05
        if a is not b:
            _conectar(a, b, costo, cerrada)
    return salas


def _jugador(sala):
    return Jugador(vida_max=10**9, ataque=10, defensa=10**6, velocidad=100,
                   inventario_max=10, sala=sala)


def armar_cripta(semilla, num_salas, num_cazadores, rango=None):
    """Cripta sembrada: devuelve (partida, salas, cazadores). Con `rango`, todos lo usan."""
    azar = random.Random(semilla)
    salas = _salas_conexas(azar, num_salas)
    partida = Partida(_jugador(salas[0]), semilla=semilla)
    cazadores = []
    for k in range(num_cazadores):
        sorteado = azar.choice(RANGOS_CAZADOR)
        sala = azar.choice(salas[1:])
        h = Enemigo(f"c{k}", "x", f"Cazador {k}", 50, 50, 5, 0, 100, "cazador", sala,
                    rango=rango if rango is not None else sorteado)
        partida.activar_enemigo(h)
        cazadores.append(h)
    return partida, salas, cazadores


def _cambiar_puerta(partida, salas, azar):
    sala = azar.choice(salas)
    if sala.salidas:
        salida = azar.choice(sala.salidas)
        partida._poner_cerrada(salida, not salida.cerrada)


def _accion_jugador(partida, azar, k):
    if k % 4 == 3:
        abiertas = [s for s in partida.jugador.sala.salidas if not s.cerrada]
        if abiertas:
            partida.mover(azar.choice(abiertas).direccion)
            return
    partida.esperar_jugador()


def ejecucion(modo, semilla, num_salas, num_cazadores, rango, acciones, cambio_cada, registrar=False):
    """Una partida sembrada con la misma lista de acciones y de cambios de puerta.

    Devuelve us por acción, búsquedas hechas y (si `registrar`) las decisiones de los cazadores.
    """
    partida, salas, cazadores = armar_cripta(semilla, num_salas, num_cazadores, rango)
    decisor = DecisorCazador(modo)
    partida.decisor_cazador = decisor
    decisiones = []
    if registrar:
        original = decisor.decidir

        def registrando(p, cazador, limite_forzado=None):
            salida = original(p, cazador, limite_forzado)
            decisiones.append((cazador.id_enemigo,
                               None if salida is None else (salida.destino.id, salida.direccion)))
            return salida

        decisor.decidir = registrando
    azar = random.Random(semilla + 7)
    busquedas = Busqueda.busquedas
    inicio = time.perf_counter()
    for k in range(acciones):
        if k % cambio_cada == cambio_cada - 1:
            _cambiar_puerta(partida, salas, azar)
        _accion_jugador(partida, azar, k)
    segundos = time.perf_counter() - inicio
    return {"us": segundos / acciones * 1_000_000,
            "busquedas": Busqueda.busquedas - busquedas,
            "decisiones": decisiones}


def verificar_equivalencia(semilla, num_salas, num_cazadores, rango, acciones, cambio_cada, modos=MODOS):
    """Corre la misma lista de acciones en cada modo; falla si alguna decisión difiere."""
    base = None
    for modo in modos:
        decisiones = ejecucion(modo, semilla, num_salas, num_cazadores, rango, acciones,
                               cambio_cada, registrar=True)["decisiones"]
        if base is None:
            base, modo_base = decisiones, modo
        elif decisiones != base:
            raise RuntimeError(f"el modo {modo} decide distinto que el modo {modo_base}")
    return base


def _medir(modo, num_salas, num_cazadores, rango, acciones, cambio_cada):
    r = ejecucion(modo, SEMILLA, num_salas, num_cazadores, rango, acciones, cambio_cada)
    return r["us"], r["busquedas"]


def _celda(par):
    return f"{par[0]:>10.1f} us {par[1]:>8} busq."


# ---- escalado (FR-018) ------------------------------------------------------

def cripta_local(semilla, total, rango, nucleo=None):
    """Cripta de `total` salas cuya zona a `rango` del jugador es la misma sea cual sea el total.

    El núcleo sale de una semilla; el resto se cuelga con salidas más caras que `rango`.
    Devuelve (partida, salas, cazador).
    """
    nucleo = min(NUCLEO, total) if nucleo is None else nucleo
    azar = random.Random(semilla)
    salas = [Sala(i + 1, f"Sala {i + 1}") for i in range(total)]
    for i in range(1, nucleo):
        _conectar(salas[azar.randrange(i)], salas[i], azar.choice(COSTOS_SALIDA))
    for _ in range(nucleo // 2):
        a, b = azar.choice(salas[:nucleo]), azar.choice(salas[:nucleo])
        costo = azar.choice(COSTOS_SALIDA)
        if a is not b:
            _conectar(a, b, costo)
    resto = random.Random(semilla + 1)
    for i in range(nucleo, total):
        _conectar(salas[resto.randrange(i)], salas[i], rango + 1 + resto.randrange(500))
    partida = Partida(_jugador(salas[0]), semilla=semilla)
    estampa = Busqueda().calcular(salas[0], rango)
    alcanzadas = [s for s in salas[1:] if s.busq_marca == estampa]
    sala = max(alcanzadas, key=lambda s: (s.busq_dist, -s.id)) if alcanzadas else salas[0]
    cazador = Enemigo("c0", "x", "Cazador 0", 50, 50, 5, 0, 100, "cazador", sala, rango=rango)
    partida.activar_enemigo(cazador)
    partida.agenda.cancelar(cazador.evento)
    return partida, salas, cazador


def _region(salas, jugador_sala, rango):
    estampa = Busqueda().calcular(jugador_sala, rango)
    return [(s.id, s.busq_dist) for s in salas if s.busq_marca == estampa]


def escalado(salas_chicas, salas_grandes, rango, semilla, repeticiones=2000):
    """Microsegundos por decisión en dos criptas de distinto tamaño y misma región; y su razón."""
    tiempos = []
    regiones = []
    for total in (salas_chicas, salas_grandes):
        partida, salas, cazador = cripta_local(semilla, total, rango)
        regiones.append(_region(salas, partida.jugador.sala, rango))
        decisor = DecisorCazador("individual")
        inicio = time.perf_counter()
        for _ in range(repeticiones):
            decisor.decidir(partida, cazador)
        tiempos.append((time.perf_counter() - inicio) / repeticiones * 1_000_000)
    if regiones[0] != regiones[1]:
        raise RuntimeError("las dos criptas no tienen la misma región dentro del rango")
    return tiempos[0], tiempos[1], tiempos[1] / tiempos[0]


# ---- salida -----------------------------------------------------------------

def ejecutar(pequeno=False):
    cfg = PEQUENO if pequeno else NORMAL
    acciones = cfg["acciones"]
    salas = cfg["salas"]
    print(f"Benchmarks del cazador ({acciones} acciones del jugador por celda, semilla {SEMILLA})")

    print("\n1. un cazador contra muchos (modo compartido, puertas casi nunca cambian)")
    for n in cfg["muchos"]:
        print(f"   {n:>4} cazadores {_celda(_medir('compartido', salas, n, None, acciones, CASI_NUNCA))}")

    print("\n2. rango chico contra rango grande (modo compartido, puertas casi nunca cambian)")
    for total in cfg["salas_rango"]:
        for rango in cfg["rangos"]:
            par = _medir("compartido", total, cfg["cazadores_rango"], rango, acciones, CASI_NUNCA)
            print(f"   {total:>5} salas, rango {rango:>5} {_celda(par)}")

    n = cfg["cazadores_modos"]
    print(f"\n(antes de medir: los tres modos deciden igual con {n} cazadores)")
    comprobadas = min(acciones, 1000)
    for cambio in (SEGUIDO, CASI_NUNCA):
        verificar_equivalencia(SEMILLA, salas, n, None, comprobadas, cambio)
    medidas = {}
    for nombre, cambio in (("puertas cambian seguido", SEGUIDO), ("puertas casi nunca cambian", CASI_NUNCA)):
        for modo in MODOS:
            medidas[(nombre, modo)] = _medir(modo, salas, n, None, acciones, cambio)

    print(f"\n3. una búsqueda por cazador contra compartida ({n} cazadores, {salas} salas)")
    for nombre in ("puertas cambian seguido", "puertas casi nunca cambian"):
        for modo in MODOS:
            print(f"   {nombre:<28} {modo:<22} {_celda(medidas[(nombre, modo)])}")

    print("\n4. reusar contra recalcular (compartido contra compartido_sin_reuso)")
    for nombre in ("puertas cambian seguido", "puertas casi nunca cambian"):
        reusa = medidas[(nombre, "compartido")]
        recalcula = medidas[(nombre, "compartido_sin_reuso")]
        print(f"   {nombre:<28} reusar {reusa[0]:>10.1f} us {reusa[1]:>8} busq.   "
              f"recalcular {recalcula[0]:>10.1f} us {recalcula[1]:>8} busq.   "
              f"razón {recalcula[0] / reusa[0]:.2f}")

    chicas, grandes = cfg["escalado"]
    t_chica, t_grande, razon = escalado(chicas, grandes, 200, SEMILLA, cfg["repeticiones"])
    print(f"\n5. escalado con el tamaño de la cripta (rango 200, misma región)")
    print(f"   {chicas:>5} salas {t_chica:>10.1f} us por decisión")
    print(f"   {grandes:>5} salas {t_grande:>10.1f} us por decisión")
    print(f"   razón {razon:.2f}")


if __name__ == "__main__":
    ejecutar()
