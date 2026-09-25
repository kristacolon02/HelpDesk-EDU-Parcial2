"""Contrato de notificacion y sus implementaciones.

El servicio de tickets no sabe por que canal se avisa de los cambios: solo
conoce el contrato ``Notifier`` y llama a ``notify``. Cambiar de canal es
cambiar el objeto que se inyecta, sin tocar una linea del servicio ni
agregar condicionales por tipo.
"""
from abc import ABC, abstractmethod
from typing import Any


class Notifier(ABC):
    """Puerto de salida: como el sistema comunica lo que ocurre.

    Al heredar de ``ABC`` y declarar ``notify`` con ``@abstractmethod``, la
    clase no se puede instanciar directamente y toda implementacion queda
    obligada a definir el metodo.
    """

    @abstractmethod
    def notify(
        self,
        event: str,
        ticket_id: int,
        detail: str,
        recipients: list[int],
    ) -> None:
        """Comunica un hecho ocurrido sobre un ticket a sus destinatarios."""


class NullNotifier(Notifier):
    """Implementacion inofensiva que no envia nada (patron Null Object).

    Es el valor por defecto del servicio: evita tener que preguntar
    ``if self.notifier is not None`` antes de cada aviso.
    """

    def notify(
        self,
        event: str,
        ticket_id: int,
        detail: str,
        recipients: list[int],
    ) -> None:
        return None


class WebhookNotifier(Notifier):
    """Simula un canal de webhook guardando los envios en memoria.

    No realiza llamadas HTTP ni imprime nada: cada aviso se acumula en
    ``sent_payloads``, de modo que una prueba puede inspeccionar exactamente
    que se envio y con que datos.
    """

    def __init__(self) -> None:
        self.sent_payloads: list[dict[str, Any]] = []

    def notify(
        self,
        event: str,
        ticket_id: int,
        detail: str,
        recipients: list[int],
    ) -> None:
        self.sent_payloads.append(
            {
                "event": event,
                "ticket_id": ticket_id,
                "detail": detail,
                "recipients": list(recipients),
            }
        )
