from structures.agenda import AgendaEventos

a = AgendaEventos()
a.programar(50, "x")
a.programar(10, "x")
a.programar(30, "x")
a.programar(10, "y")   # empate de tiempo con el primer 10

while len(a) > 0:
    event = a.extraer()
    print(event.tiempo, event.num_sec, event.tipo)

b = AgendaEventos()
e1 = b.programar(10, "a")
e2 = b.programar(20, "b")
e3 = b.programar(30, "c")
e4 = b.programar(40, "d")

print(b.cancelar(e2))    # True
print(b.cancelar(e2))    # False (ya estaba cancelado)

while len(b) > 0:
    ev = b.extraer()
    print(ev.tiempo, ev.tipo)

c = AgendaEventos()
x = c.programar(10, "x")
y = c.programar(20, "y")
z = c.programar(30, "z")

c.reprogramar(z, 5)      # z pasa a ser el más temprano
c.reprogramar(x, 20)     # x empata con y, pero ahora tiene secuencia mayor

while len(c) > 0:
    ev = c.extraer()
    print(ev.tiempo, ev.tipo)