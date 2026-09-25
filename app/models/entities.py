"""SQLAlchemy entities: persistence representation of the HelpDesk domain."""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.domain.errors import ValidationError


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(120), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(20))
    password_hash: Mapped[str] = mapped_column(String(255))


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(50))
    priority: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(30), default="Open")
    requester_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    assignee_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    due_at: Mapped[datetime] = mapped_column(DateTime)
    requester: Mapped[User] = relationship(User, foreign_keys=[requester_id])
    assignee: Mapped[User | None] = relationship(User, foreign_keys=[assignee_id])

    # --- Etiquetas en memoria (parcial 2, EJERCICIO 1) --------------------
    # La coleccion es privada y NO esta mapeada a ninguna columna, vive solo
    # durante la vida del objeto y no requiere migracion SQL.
    #
    # En un dataclass esta coleccion se declararia como
    # ``field(default_factory=list, init=False, repr=False)``. Ticket es una
    # entidad declarativa de SQLAlchemy, no un dataclass, asi que se replican
    # las tres garantias de esa declaracion por otra via:
    #   * default_factory -> _tag_store() crea la lista en el primer uso, de
    #     modo que cada instancia tiene la suya y nunca se comparte una lista
    #     mutable a nivel de clase;
    #   * init=False      -> no aparece en el constructor generado por el ORM;
    #   * repr=False      -> al no estar mapeada, queda fuera del repr.

    def _tag_store(self) -> list[str]:
        """Devuelve la lista interna de etiquetas de ESTA instancia.

        La crea en el primer acceso. Es el equivalente a ``default_factory``:
        garantiza una coleccion distinta por objeto.
        """
        try:
            return self._tags
        except AttributeError:
            self._tags = []
            return self._tags

    @property
    def tags(self) -> tuple[str, ...]:
        """Etiquetas del ticket como tupla inmutable (solo lectura).

        Se devuelve una copia en forma de tupla para que quien consuma la
        propiedad no pueda mutar la coleccion interna. Al no definirse un
        setter, ``ticket.tags = [...]`` lanza ``AttributeError``.
        """
        return tuple(self._tag_store())

    def add_tag(self, tag: str) -> None:
        """Agrega una etiqueta normalizada, sin duplicados.

        Normaliza con ``strip().lower()`` para que "  Hardware " y "hardware"
        sean la misma etiqueta. Rechaza valores vacios o compuestos solo por
        espacios con ``ValidationError``. Si la etiqueta ya existe, la
        operacion no hace nada.
        """
        normalized = tag.strip().lower()
        if not normalized:
            raise ValidationError("La etiqueta no puede estar vacia.")

        store = self._tag_store()
        if normalized not in store:
            store.append(normalized)


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"))
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    author: Mapped[User] = relationship(User)


class History(Base):
    __tablename__ = "history"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"))
    actor_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    event_type: Mapped[str] = mapped_column(String(50))
    detail: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    actor: Mapped[User] = relationship(User)


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(160))
    body: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(50))
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
