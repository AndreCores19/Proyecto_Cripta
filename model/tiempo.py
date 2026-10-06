COSTO_MOVER = 100
COSTO_ATACAR = 100
COSTO_ESPERAR = 100
COSTO_USAR = 50
COSTO_EQUIPAR = 50
COSTO_RECOGER = 25
COSTO_SOLTAR = 25
COSTO_ABRIR = 50


def intervalo(costo, velocidad):
    #Tiempo que se tarda en realizar una acción con un costo y velocidad dados
    return max(1, costo * 100 // velocidad)


def nuevo_tiempo_por_velocidad(tiempo_siguiente, t, vel_anterior, vel_nueva):
    #Calcula el nuevo tiempo que se tardaría en llegar a tiempo_siguiente si la velocidad cambia 
    restante = max(1, (tiempo_siguiente - t) * vel_anterior // vel_nueva)
    return t + restante