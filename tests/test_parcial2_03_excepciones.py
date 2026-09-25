"""Pruebas del ejercicio 3 del parcial 2: excepciones y polimorfismo.

Se verifica que la asignacion duplicada se rechaza sin dejar rastro en el
historial ni en las notificaciones, y que el canal de notificacion se
inyecta por el parametro ``notifier`` del servicio.
"""
from datetime import datetime, timedelta

import pytest

from app.core.database import create_session_factory
from app.domain.errors import DomainError, DuplicateAssignmentError
from app.models.entities import Ticket
from app.schemas.tickets import AssignIn
from app.services.auth import seed_users
from app.services.notifications import Notifier, NullNotifier, WebhookNotifier
from app.services.tickets import TicketService

SUPERVISOR_ID = 2
TECNICO_ID = 3
SOLICITANTE_ID = 4


def nueva_sesion():
    """Crea una base SQLite en memoria con los usuarios sembrados."""
    factory = create_session_factory("sqlite://")
    with factory() as db:
        seed_users(db)
    return factory()


def crear_ticket(db, assignee_id: int | None = None) -> Ticket:
    ticket = Ticket(
        title="Impresora sin tinta",
        description="Caso de prueba",
        category="Hardware",
        priority="Medium",
        requester_id=SOLICITANTE_ID,
        assignee_id=assignee_id,
        due_at=datetime.utcnow() + timedelta(hours=48),
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


# --------------------------------------------------------------------
# Contrato Notifier
# --------------------------------------------------------------------

def test_notifier_es_abstracto_y_no_se_puede_instanciar():
    with pytest.raises(TypeError):
        Notifier()


def test_webhook_notifier_nace_sin_envios():
    assert WebhookNotifier().sent_payloads == []


def test_webhook_notifier_guarda_los_argumentos_recibidos():
    notifier = WebhookNotifier()

    notifier.notify(event="assigned", ticket_id=7, detail="x", recipients=[1, 2])

    assert notifier.sent_payloads == [
        {"event": "assigned", "ticket_id": 7, "detail": "x", "recipients": [1, 2]}
    ]


# --------------------------------------------------------------------
# Inyeccion polimorfica
# --------------------------------------------------------------------

def test_el_servicio_usa_null_notifier_por_defecto():
    db = nueva_sesion()

    service = TicketService(db)

    assert isinstance(service.notifier, NullNotifier)


def test_asignacion_valida_emite_notificacion_con_su_payload():
    db = nueva_sesion()
    ticket = crear_ticket(db)
    notifier = WebhookNotifier()
    service = TicketService(db, notifier=notifier)
    actor = service.users.by_id(SUPERVISOR_ID)

    service.assign(ticket.id, AssignIn(assignee_id=TECNICO_ID), actor)

    assert len(notifier.sent_payloads) == 1
    payload = notifier.sent_payloads[0]
    assert payload["event"] == "assigned"
    assert payload["ticket_id"] == ticket.id
    assert payload["detail"] == "Assigned to Technician"
    assert sorted(payload["recipients"]) == sorted([SOLICITANTE_ID, TECNICO_ID])


# --------------------------------------------------------------------
# Asignacion duplicada
# --------------------------------------------------------------------

def test_reasignar_al_mismo_tecnico_lanza_duplicate_assignment_error():
    db = nueva_sesion()
    ticket = crear_ticket(db, assignee_id=TECNICO_ID)
    service = TicketService(db)
    actor = service.users.by_id(SUPERVISOR_ID)

    with pytest.raises(DuplicateAssignmentError):
        service.assign(ticket.id, AssignIn(assignee_id=TECNICO_ID), actor)


def test_duplicate_assignment_error_es_un_error_de_dominio():
    db = nueva_sesion()
    ticket = crear_ticket(db, assignee_id=TECNICO_ID)
    service = TicketService(db)
    actor = service.users.by_id(SUPERVISOR_ID)

    with pytest.raises(DomainError):
        service.assign(ticket.id, AssignIn(assignee_id=TECNICO_ID), actor)


def test_la_asignacion_duplicada_no_agrega_historial_ni_notificaciones():
    db = nueva_sesion()
    ticket = crear_ticket(db, assignee_id=TECNICO_ID)
    notifier = WebhookNotifier()
    service = TicketService(db, notifier=notifier)
    actor = service.users.by_id(SUPERVISOR_ID)
    historial_previo = len(service.tickets.history_for(ticket.id))

    with pytest.raises(DuplicateAssignmentError):
        service.assign(ticket.id, AssignIn(assignee_id=TECNICO_ID), actor)

    assert len(service.tickets.history_for(ticket.id)) == historial_previo
    assert notifier.sent_payloads == []


def test_las_validaciones_previas_se_mantienen():
    db = nueva_sesion()
    ticket = crear_ticket(db)
    notifier = WebhookNotifier()
    service = TicketService(db, notifier=notifier)
    actor = service.users.by_id(SUPERVISOR_ID)

    # Un solicitante no puede recibir la asignacion: sigue vigente la regla
    # anterior, que responde 422 y no se ve alterada por la nueva excepcion.
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as error:
        service.assign(ticket.id, AssignIn(assignee_id=SOLICITANTE_ID), actor)

    assert error.value.status_code == 422
    assert notifier.sent_payloads == []


def test_reasignar_a_otro_tecnico_si_es_valido():
    db = nueva_sesion()
    ticket = crear_ticket(db, assignee_id=TECNICO_ID)
    notifier = WebhookNotifier()
    service = TicketService(db, notifier=notifier)
    actor = service.users.by_id(SUPERVISOR_ID)

    resultado = service.assign(ticket.id, AssignIn(assignee_id=SUPERVISOR_ID), actor)

    assert resultado["assignee_id"] == SUPERVISOR_ID
    assert len(notifier.sent_payloads) == 1
