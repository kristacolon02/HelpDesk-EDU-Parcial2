"""Pruebas del ejercicio 05 del parcial 2, agregacion y persistencia.

La prueba central no se conforma con leer el resultado dentro de la misma
sesion que escribio, confirma la transaccion, cierra esa sesion y consulta
desde una sesion nueva sobre el mismo engine. Solo asi se demuestra que el
dato quedo en la base y no en la cache de identidad de SQLAlchemy.
"""
from datetime import datetime, timedelta

from app.core.database import create_session_factory
from app.models.entities import Ticket
from app.repositories.tickets import TicketRepository
from app.services.auth import seed_users

SOLICITANTE_ID = 4


def nueva_factory():
    """Engine SQLite en memoria con StaticPool.

    ``create_session_factory("sqlite://")`` configura StaticPool, de modo
    que todas las sesiones que produzca comparten la misma conexion y
    la misma base en memoria, sin eso cada sesion abriria una base
    vacia distinta y la prueba no probaria nada.
    """
    return create_session_factory("sqlite://")


def ticket(status: str) -> Ticket:
    return Ticket(
        title=f"Caso {status}",
        description="Caso de prueba",
        category="Hardware",
        priority="Medium",
        status=status,
        requester_id=SOLICITANTE_ID,
        due_at=datetime.utcnow() + timedelta(hours=48),
    )


def test_count_by_status_desde_una_sesion_nueva_tras_commit():
    factory = nueva_factory()

    # Sesion de escritura: tres tickets en dos estados validos.
    escritura = factory()
    seed_users(escritura)
    escritura.add_all([ticket("Open"), ticket("Open"), ticket("Closed")])
    escritura.commit()
    escritura.close()

    # Sesion nueva sobre el mismo engine: no hereda nada en memoria.
    lectura = factory()
    reporte = TicketRepository(lectura).count_by_status()

    assert reporte == {"Open": 2, "Closed": 1}


def test_la_suma_del_reporte_coincide_con_los_tickets_creados():
    factory = nueva_factory()

    escritura = factory()
    seed_users(escritura)
    escritura.add_all([ticket("Open"), ticket("Open"), ticket("Closed")])
    escritura.commit()
    escritura.close()

    reporte = TicketRepository(factory()).count_by_status()

    assert sum(reporte.values()) == 3


def test_solo_aparecen_los_estados_presentes():
    factory = nueva_factory()

    escritura = factory()
    seed_users(escritura)
    escritura.add_all([ticket("Open"), ticket("Open"), ticket("Closed")])
    escritura.commit()
    escritura.close()

    reporte = TicketRepository(factory()).count_by_status()

    assert set(reporte) == {"Open", "Closed"}
    assert "Cancelled" not in reporte
    assert "In Progress" not in reporte


def test_base_sin_tickets_devuelve_diccionario_vacio():
    # Base de prueba independiente: ningun ticket insertado.
    factory = nueva_factory()
    sesion = factory()
    seed_users(sesion)
    sesion.commit()
    sesion.close()

    reporte = TicketRepository(factory()).count_by_status()

    assert reporte == {}


def test_el_reporte_devuelve_enteros():
    factory = nueva_factory()

    escritura = factory()
    seed_users(escritura)
    escritura.add_all([ticket("Open"), ticket("Closed")])
    escritura.commit()
    escritura.close()

    reporte = TicketRepository(factory()).count_by_status()

    assert all(isinstance(total, int) for total in reporte.values())
