class VistaConsola:
    def mostrar_estado(self, estado):
        j = estado.jugador
        print("-" * 40)
        print(f"Sala {estado.id_sala}: {estado.nombre_sala}")
        print(f"Tiempo: {estado.reloj}")
        print(f"Jugador: {j.nombre} (Vida: {j.vida}/{j.vida_max})")
        print(f"  Ataque: {j.ataque}  Defensa: {j.defensa}  Velocidad: {j.velocidad}")
        print(f"  Arma: {j.arma if j.arma is not None else 'ninguna'}")
        print(f"  Armadura: {j.armadura if j.armadura is not None else 'ninguna'}")
        efectos = ", ".join(j.efectos)
        print(f"  Efectos: {efectos if efectos else 'ninguno'}")

        print("Salidas:")
        for s in estado.salidas:
            print(f"  {s.direccion} -> {s.nombre_destino} "
                  f"({'cerrada' if s.cerrada else 'abierta'}, costo {s.costo})")
        print("Enemigos en la sala:")
        for enemigo in estado.enemigos:
            marca = " (cazador)" if enemigo.cazador else ""
            linea = (f"  {enemigo.nombre}{marca} [{enemigo.id_enemigo}] "
                     f"(Vida: {enemigo.vida}/{enemigo.vida_max})")
            if enemigo.efectos:
                linea += f" [{', '.join(enemigo.efectos)}]"
            print(linea)
        print("Trampas en la sala:")
        for trampa in estado.trampas:
            print(f"  {trampa.nombre} (Daño: {trampa.dano}, "
                  f"{'armada' if trampa.armada else 'desarmada'})")
        print("Objetos en la sala:")
        for objeto in estado.objetos:
            print(f"  [{objeto.id_instancia}] {objeto.nombre}")
        print("Bitácora:")
        for mensaje in estado.bitacora:
            print(f"  {mensaje}")
        print("-" * 40)

    def mostrar_final(self, resumen):
        print("-" * 40)
        for mensaje in resumen.bitacora:
            print(f"  {mensaje}")
        print(f"Tiempo final: {resumen.reloj}")
        if resumen.victoria:
            print("¡Victoria! Escapaste de la cripta.")
        elif resumen.terminada:
            print("Has muerto.")
        else:
            print("Saliste de la partida.")


    def mostrar_mensaje(self, texto):
        print(texto)

    def pedir_comando(self):
        return input("> ")

    def mostrar_inventario(self, inv):
        print(f"Inventario ({inv.tamano}/{inv.capacidad_max}):")
        if inv.tamano == 0:
            print("  (vacío)")
            return
        for objeto in inv.objetos:
            marca = ">" if objeto.actual else " "
            equipo = " (equipado)" if objeto.equipado else ""
            print(f" {marca} [{objeto.id_instancia}] {objeto.nombre}{equipo} (peso {objeto.peso}, valor {objeto.valor})")

    def mostrar_inventario_ordenado(self, objetos, criterio):
        print(f"Inventario ordenado por {criterio}:")
        if not objetos:
            print("  (vacío)")
            return
        for objeto in objetos:
            print(f"  [{objeto.id_instancia}] {objeto.nombre} "
                  f"(peso {objeto.peso}, valor {objeto.valor})")

    def mostrar_reporte(self, solicitudes, presupuesto, aciertos, fallos):
        print("-" * 40)
        print(f"Solicitudes realizadas: {solicitudes} de {presupuesto}")
        if presupuesto is not None:
            print(f"Presupuesto restante: {presupuesto - solicitudes}")
        print(f"Aciertos: {aciertos}, Fallos: {fallos}")
        total = aciertos + fallos
        if total > 0:
            print(f"Porcentaje de aciertos: {aciertos / total * 100:.2f}%")
        else:
            print("Porcentaje de aciertos: N/A")
        print("-" * 40)

    def pedir_nombre(self):
        nombre = input("Nombre del jugador: ").strip()
        return nombre if nombre else "Jugador"

    def elegir_cripta(self, criptas):
        print("Criptas disponibles:")
        for i, c in enumerate(criptas, 1):
            print(f"  {i}. {c['nombre']} ({c['id']}) - "
                  f"{c['salas']} salas, dificultad {c['dificultad']}")
        while True:
            texto = input("Elige una cripta (número, o 'salir'): ").strip().lower()
            if texto == "salir":
                return None
            if texto.isdigit() and 1 <= int(texto) <= len(criptas):
                return criptas[int(texto) - 1]["id"]
            print("Opción no válida.")

    def mostrar_puntajes(self, puntajes):
        print("Tabla de puntajes:")
        print(f"  {'#':>2} {'Jugador':<14} {'Cripta':<10} {'Ver.':<6} "
              f"{'Acc.':>5} {'Derr.':>5} {'Tiempo':>7}  Resultado")
        for i, p in enumerate(puntajes[:10], 1):
            resultado = "victoria" if p.victoria else "derrota"
            print(f"  {i:>2} {p.nombre:<14} {p.id_cripta:<10} {p.version:<12} "
                  f"{p.acciones:>5} {p.derrotados:>5} {p.tiempo:>7}  {resultado}")