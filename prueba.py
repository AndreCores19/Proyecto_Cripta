"""from structures.agenda import AgendaEventos

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

from model.tiempo import intervalo, nuevo_tiempo_por_velocidad, COSTO_MOVER

print(intervalo(COSTO_MOVER, 100))               # esperado: 100
print(intervalo(COSTO_MOVER, 150))               # esperado: 66
print(nuevo_tiempo_por_velocidad(300, 200, 100, 200))   # esperado: 250
print(nuevo_tiempo_por_velocidad(300, 200, 100, 50))    # esperado: 400


from model.entidades import Jugador, Enemigo

j = Jugador(30, 6, 2, 100, sala=1)
r = Enemigo("e-201", "ent_rata_gigante", "Rata gigante", 12, 12, 5, 1, 150, "rastreador", sala=2)

j.recibir_dano(40)
print(j.vida, j.esta_vivo())      # esperado: 0 False

r.recibir_dano(5)
r.curar(100)
print(r.vida)                      # esperado: 12

from model.entidades import Jugador, Enemigo
from model.partida import Partida

j = Jugador(30, 6, 2, 100, sala=1)
rata = Enemigo("e-201", "ent_rata_gigante", "Rata gigante", 12, 12, 5, 1, 150, "rastreador", sala=1)

p = Partida(j, semilla=42)
p.activar_enemigo(rata)
p.avanzar_hasta_jugador()
print("Decide el jugador, reloj =", p.reloj)

while not p.terminada and rata.esta_vivo():
    p.atacar(rata)
    print("Decide el jugador, reloj =", p.reloj, "| vida jugador:", j.vida)

print("Derrotados:", p.enemigos_derrotados, "| agenda pendiente:", len(p.agenda))
"""

from model.entidades import Jugador, Enemigo
from model.sala import Sala, Salida
from model.partida import Partida

a = Sala(1, "Entrada")
b = Sala(2, "Pasillo")
a.agregar_salida(Salida("N", b))
b.agregar_salida(Salida("S", a))
b.agregar_salida(Salida("E", a, cerrada=True, llave="itm_llave"))

rata = Enemigo("e-201", "ent_rata_gigante", "Rata gigante", 12, 12, 5, 1, 150, "rastreador", sala=b)
b.inactivos.append(rata)

j = Jugador(30, 6, 2, 100, sala=a)
p = Partida(j, semilla=42)
p.avanzar_hasta_jugador()
print("Inicio: sala", j.sala.id, "reloj", p.reloj, "rastro A:", a.rastro)

print("Mover hacia O:", p.mover("O"))      # no existe
print("Mover N:", p.mover("N"))
print("Sala:", j.sala.id, "reloj:", p.reloj, "| vida:", j.vida)
print("Rastro A:", a.rastro, "| Rastro B:", b.rastro)
