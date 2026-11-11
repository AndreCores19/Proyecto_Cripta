import random
import time

from bench.bench_ciclo import COSTOS_SALIDA, armar_partida, armar_partida_costos
from model.tiempo_logica import intervalo
from structures.agenda import AgendaEventos, Evento

TAMANOS = (100, 300, 1000, 3000)
OPERACIONES = 5000

class AgendaListaSinOrdenar:

    def __init__(self):
        self.eventos = []
        self.num_sec = 0

    def programar(self, tiempo):
        ev = Evento(tiempo, self.num_sec, "accion")
        self.num_sec += 1
        self.eventos.append(ev)
        return ev

    def extraer(self):
        mejor = 0
        for i in range(1, len(self.eventos)):
            a, b = self.eventos[i], self.eventos[mejor]
            if a.tiempo < b.tiempo or (a.tiempo == b.tiempo and a.num_sec < b.num_sec):
                mejor = i
        self.eventos[mejor], self.eventos[-1] = self.eventos[-1], self.eventos[mejor]
        return self.eventos.pop()

    def cancelar(self, ev):
        for i in range(len(self.eventos)):
            if self.eventos[i] is ev:
                self.eventos[i] = self.eventos[-1]
                self.eventos.pop()
                return


class AgendaListaOrdenada:

    def __init__(self):
        self.eventos = []            # de mayor a menor (tiempo, num_sec)
        self.num_sec = 0

    def programar(self, tiempo):
        ev = Evento(tiempo, self.num_sec, "accion")
        self.num_sec += 1
        clave = (tiempo, ev.num_sec)
        i = len(self.eventos)
        self.eventos.append(ev)
        while i > 0 and (self.eventos[i - 1].tiempo, self.eventos[i - 1].num_sec) < clave:
            self.eventos[i] = self.eventos[i - 1]
            i -= 1
        self.eventos[i] = ev
        return ev

    def extraer(self):
        return self.eventos.pop()

    def cancelar(self, ev):
        for i in range(len(self.eventos)):
            if self.eventos[i] is ev:
                del self.eventos[i]
                return


class AgendaHeap:

    def __init__(self):
        self.agenda = AgendaEventos()

    def programar(self, tiempo):
        return self.agenda.programar(tiempo, "accion")

    def extraer(self):
        return self.agenda.extraer()

    def cancelar(self, ev):
        self.agenda.cancelar(ev)


def contar_operaciones(acciones=1000, num_enemigos=300, variable=False):
    if variable:
        partida = armar_partida_costos(100, num_enemigos, 1)
    else:
        partida = armar_partida(100, num_enemigos)
    agenda = partida.agenda
    cuentas = {"programar": 0, "extraer": 0, "cancelar": 0, "reprogramar": 0}
    nombres = ("programar", "extraer", "cancelar", "reprogramar")
    for nombre in nombres:
        original = getattr(agenda, nombre)

        def envuelta(*args, _n=nombre, _f=original, **kw):
            cuentas[_n] += 1
            return _f(*args, **kw)
        setattr(agenda, nombre, envuelta)
    maximo = 0
    for _ in range(acciones):
        partida.esperar_jugador()
        maximo = max(maximo, len(agenda))
    return {n: cuentas[n] / acciones for n in nombres}, maximo


def medir_ciclo(clase, n, operaciones, azar):
    agenda = clase()
    for _ in range(n):
        agenda.programar(azar.randint(0, 1000))
    inicio = time.perf_counter()
    for _ in range(operaciones):
        ev = agenda.extraer()
        agenda.programar(ev.tiempo + azar.randint(1, 200))
    return (time.perf_counter() - inicio) / operaciones * 1_000_000


def medir_ciclo_variable(clase, n, operaciones, azar):
    # incremento = intervalo(costo, velocidad), costo del conjunto de salidas, velocidad en [50, 200]
    agenda = clase()
    for _ in range(n):
        agenda.programar(azar.randint(0, 1000))
    inicio = time.perf_counter()
    for _ in range(operaciones):
        ev = agenda.extraer()
        agenda.programar(ev.tiempo + intervalo(azar.choice(COSTOS_SALIDA), azar.randint(50, 200)))
    return (time.perf_counter() - inicio) / operaciones * 1_000_000


def medir_cancelar(clase, n, operaciones, azar):
    agenda = clase()
    eventos = [agenda.programar(azar.randint(0, 1000)) for _ in range(n)]
    inicio = time.perf_counter()
    for _ in range(operaciones):
        i = azar.randrange(n)
        agenda.cancelar(eventos[i])
        eventos[i] = agenda.programar(azar.randint(0, 1000))
    return (time.perf_counter() - inicio) / operaciones * 1_000_000


def ejecutar():
    print(" Agenda de eventos ")
    por_ciclo, maximo = contar_operaciones()
    print("Operaciones reales por acción del jugador (100 salas, 300 enemigos):")
    for nombre in ("programar", "extraer", "cancelar", "reprogramar"):
        print(f"    {nombre:<12} {por_ciclo[nombre]:8.1f}")
    print(f"    eventos pendientes a la vez (máximo): {maximo}")

    candidatas = (("heap", AgendaHeap), ("lista sin ordenar", AgendaListaSinOrdenar),
                  ("lista ordenada", AgendaListaOrdenada))
    print("\n Extraer el próximo y programar otro (microsegundos por operación):")
    print(f"{'pendientes':>11}" + "".join(f"{nombre:>20}" for nombre, _ in candidatas))
    for n in TAMANOS:
        fila = f"{n:>11}"
        for _, clase in candidatas:
            fila += f"{medir_ciclo(clase, n, OPERACIONES, random.Random(1)):>20.1f}"
        print(fila)

    print("\n Extraer y programar: incremento fijo (randint 1..200) | variable (intervalo costo/velocidad):")
    print(f"{'pendientes':>11}" + "".join(f"{nombre + ' fijo':>24}{nombre + ' var.':>24}" for nombre, _ in candidatas))
    for n in TAMANOS:
        fila = f"{n:>11}"
        for _, clase in candidatas:
            fila += f"{medir_ciclo(clase, n, OPERACIONES, random.Random(1)):>24.1f}"
            fila += f"{medir_ciclo_variable(clase, n, OPERACIONES, random.Random(1)):>24.1f}"
        print(fila)

    print("\nOperaciones por acción con costos variables (100 salas, enemigos errantes):")
    print(f"{'enemigos':>9} {'modelo':>9} {'programar':>10} {'extraer':>9} {'cancelar':>9} {'reprogr.':>9} {'máx.pend.':>10}")
    for enemigos in (300, 1000, 3000):
        for modelo, variable in (("fijo", False), ("variable", True)):
            c, mx = contar_operaciones(1000, enemigos, variable)
            print(f"{enemigos:>9} {modelo:>9} {c['programar']:>10.1f} {c['extraer']:>9.1f} "
                  f"{c['cancelar']:>9.1f} {c['reprogramar']:>9.1f} {mx:>10}")

    print("\nCancelar un evento cualquiera y programar otro (microsegundos):")
    print(f"{'pendientes':>11}" + "".join(f"{nombre:>20}" for nombre, _ in candidatas))
    for n in TAMANOS:
        fila = f"{n:>11}"
        for _, clase in candidatas:
            fila += f"{medir_cancelar(clase, n, OPERACIONES // 2, random.Random(2)):>20.1f}"
        print(fila)


if __name__ == "__main__":
    ejecutar()