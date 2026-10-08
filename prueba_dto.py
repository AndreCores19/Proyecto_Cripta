from dto.contenido_sala_dto import ContenidoSalaDTO
from dto.sala_dto import SalaDTO
from dto.salida_dto import SalidaDTO
from dto.datos_cripta_dto import DatosCriptaDTO, EstadisticasJugadorDTO

salidas = {
    "S": {"sala": 1},
    "N": {"sala": 3},
    "E": {"sala": 5, "cerrada": True, "llave": "itm_llave_bronce", "cierre_automatico": 500},
}

for direccion, datos in salidas.items():
    s = SalidaDTO.desde_json(direccion, datos)
    print(s.direccion, s.id_destino, s.cerrada, s.llave, s.cierre_automatico)


sala_json = {
    "id": 2, "nombre": "Pasillo de las urnas",
    "salidas": {
        "S": {"sala": 1},
        "N": {"sala": 3},
        "E": {"sala": 5, "cerrada": True, "llave": "itm_llave_bronce", "cierre_automatico": 500},
    },
}

sala = SalaDTO.desde_json(sala_json)
print(sala.id_sala, sala.nombre, len(sala.salidas))
for s in sala.salidas:
    print(s.direccion, s.id_destino, s.cerrada)

respuesta_real = {
    "id": "cripta-01",
    "version": "fd58f7743b9e",
    "salas_total": 6,
    "paginas": 1,
    "salas_por_pagina": 50,
    "sala_inicial": 1,
    "sala_salida": 6,
    "llave_salida": "itm_llave_negra",
    "presupuesto_solicitudes": 9,
    "inventario_max": 10,
    "jugador": {"vida_max": 30, "ataque": 6, "defensa": 2, "velocidad": 100},
}

cripta = DatosCriptaDTO.desde_json(respuesta_real)
print(cripta.id_cripta, cripta.presupuesto_solicitudes, cripta.sala_inicial, cripta.jugador.vida_max)

sala2 = {'sala': 2,
         'enemigos': [{'instancia': 'e-201', 'tipo': 'ent_rata_gigante', 'vida': 12},
                      {'instancia': 'e-202', 'tipo': 'ent_rata_gigante', 'vida': 12}],
         'objetos': ['itm_daga_oxidada'],
         'trampas': [{'instancia': 't-17', 'tipo': 'trp_dardos'}]}

sala4 = {'sala': 4,
         'enemigos': [{'instancia': 'e-401', 'tipo': 'ent_guardian_oseo'}],
         'objetos': ['itm_llave_negra', 'itm_pocion_menor'],
         'trampas': []}

c2 = ContenidoSalaDTO.desde_json(sala2)
print(c2.id_sala, len(c2.enemigos), c2.objetos, c2.enemigos[0].vida)
# 2 2 ['itm_daga_oxidada'] 12

c4 = ContenidoSalaDTO.desde_json(sala4)
print(c4.id_sala, len(c4.enemigos), c4.objetos, c4.enemigos[0].vida)
# 4 1 ['itm_llave_negra', 'itm_pocion_menor'] None