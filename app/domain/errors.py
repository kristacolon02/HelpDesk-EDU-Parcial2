"""Errores de dominio del HelpDesk.

Estas excepciones representan violaciones de reglas de negocio y son
independientes del framework web, no heredan de ``HTTPException``. La capa
de servicios las da y la capa de controladores decide como traducirlas
a una respuesta HTTP, manteniendo la separacion de capas.
"""


class DomainError(Exception):
    """Clase base de todos los errores de dominio.

    Permite que un unico bloque ``except DomainError`` capture cualquier
    violacion de regla de negocio, sin enumerar cada subclase.
    """


class ValidationError(DomainError):
    """Se da cuando un valor recibido no cumple una regla del dominio."""

class DuplicateAssignmentError(DomainError):
    """Se lanza al intentar asignar un ticket al tecnico que ya lo atiende.

    Es una operacion sin efecto: repetir la asignacion no cambia el estado
    del ticket, pero si se dejara pasar generaria un evento de historial y
    una notificacion enganosos.
    """
