from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Comment, History, Ticket


class TicketRepository:
    def __init__(self, db: Session):
        self.db = db

    def by_id(self, ticket_id: int) -> Ticket | None:
        return self.db.get(Ticket, ticket_id)

    def list(self, *, requester_id: int | None = None, status: str | None = None, category: str | None = None, priority: str | None = None) -> list[Ticket]:
        query = select(Ticket)
        if requester_id is not None:
            query = query.where(Ticket.requester_id == requester_id)
        if status:
            query = query.where(Ticket.status == status)
        if category:
            query = query.where(Ticket.category == category)
        if priority:
            query = query.where(Ticket.priority == priority)
        return list(self.db.scalars(query.order_by(Ticket.id.desc())).all())

    def add(self, ticket: Ticket) -> Ticket:
        self.db.add(ticket)
        self.db.commit()
        self.db.refresh(ticket)
        return ticket

    def comments_for(self, ticket_id: int) -> list[Comment]:
        return list(self.db.scalars(select(Comment).where(Comment.ticket_id == ticket_id)).all())

    def history_for(self, ticket_id: int) -> list[History]:
        return list(self.db.scalars(select(History).where(History.ticket_id == ticket_id)).all())

    def commit(self) -> None:
        self.db.commit()

    def count_by_status(self) -> dict[str, int]:
        """Conteo de tickets agrupado por estado.

        La agregacion se resuelve en la base de datos con GROUP BY, no
        trayendo todas las filas a memoria para contarlas en Python, el
        costo no crece con el numero de tickets.

        Solo aparecen los estados presentes, una base sin tickets devuelve
        un diccionario vacio porque GROUP BY no produce filas cuando no
        hay nada que agrupar.
        """
        consulta = select(Ticket.status, func.count()).group_by(Ticket.status)
        return {estado: total for estado, total in self.db.execute(consulta).all()}
