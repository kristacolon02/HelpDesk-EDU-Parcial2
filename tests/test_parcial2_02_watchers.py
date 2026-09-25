"""Pruebas del ejercicio 2 del parcial 2: observadores del ticket.

Se trabaja directamente contra TicketService sobre una base SQLite en
memoria, sin pasar por la capa HTTP, para probar la regla de negocio y no
el enrutamiento.
"""
import pytest
from fastapi import HTTPException

from app.core.database import create_session_factory
from app.models.entities import Ticket
from app.services.auth import seed_users
from app.services.tickets import TicketService

# Ids que asigna seed_users, en su orden de insercion.
ADMIN_ID = 1
SUPERVISOR_ID = 2
TECNICO_ID = 3
SOLICITANTE_ID = 4


def nueva_sesion():
    """Crea una base SQLite en memoria con los usuarios sembrados."""
    factory = create_session_factory("sqlite://")
    with factory() as db:
        seed_users(db)
    return factory()


def crear_ticket(db, requester_id: int, assignee_id: int | None = None) -> Ticket:
    """Inserta un ticket directamente, sin pasar por el servicio."""
    from datetime import datetime, timedelta

    ticket = Ticket(
        title="Impresora sin tinta",
        description="Caso de prueba",
        category="Hardware",
        priority="Medium",
        requester_id=requester_id,
        assignee_id=assignee_id,
        due_at=datetime.utcnow() + timedelta(hours=48),
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


def test_watchers_devuelve_solo_al_solicitante_cuando_no_hay_tecnico():
    db = nueva_sesion()
    ticket = crear_ticket(db, requester_id=SOLICITANTE_ID)
    service = TicketService(db)

    observadores = service.watchers(ticket.id)

    assert [user.id for user in observadores] == [SOLICITANTE_ID]


def test_watchers_devuelve_solicitante_y_tecnico_cuando_son_distintos():
    db = nueva_sesion()
    ticket = crear_ticket(db, requester_id=SOLICITANTE_ID, assignee_id=TECNICO_ID)
    service = TicketService(db)

    observadores = service.watchers(ticket.id)

    assert [user.id for user in observadores] == [SOLICITANTE_ID, TECNICO_ID]


def test_watchers_no_duplica_cuando_solicitante_y_tecnico_son_el_mismo():
    db = nueva_sesion()
    ticket = crear_ticket(db, requester_id=TECNICO_ID, assignee_id=TECNICO_ID)
    service = TicketService(db)

    observadores = service.watchers(ticket.id)

    assert [user.id for user in observadores] == [TECNICO_ID]
    assert len(observadores) == 1


def test_watchers_devuelve_objetos_user_completos():
    db = nueva_sesion()
    ticket = crear_ticket(db, requester_id=SOLICITANTE_ID, assignee_id=TECNICO_ID)
    service = TicketService(db)

    observadores = service.watchers(ticket.id)

    assert [user.name for user in observadores] == ["Requester", "Technician"]
    assert all(user.email for user in observadores)


def test_watchers_propaga_el_error_si_el_ticket_no_existe():
    db = nueva_sesion()
    service = TicketService(db)

    with pytest.raises(HTTPException) as error:
        service.watchers(9999)

    assert error.value.status_code == 404
    