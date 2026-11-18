"""DTO del resultado de «ir a» (FR-016, FR-022). Valores simples y una lista de str; no importa model/."""


class ViajeResultadoDTO:
    def __init__(self, aceptado, motivo, pasos, direcciones=None):
        self.aceptado = aceptado        # False si la sala no está explorada
        self.motivo = motivo            # "no_explorada" o el motivo de parada del viaje
        self.pasos = pasos              # cuántos pasos se dieron
        self.direcciones = list(direcciones) if direcciones is not None else []
