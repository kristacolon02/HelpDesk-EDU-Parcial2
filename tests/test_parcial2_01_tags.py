"""Pruebas del ejercicio 01 del parcial 2: etiquetas y encapsulamiento.

Se construyen instancias de Ticket sin sesion de base de datos: las
etiquetas viven en memoria y no dependen de la persistencia.
"""
import pytest

from app.domain.errors import DomainError, ValidationError
from app.models.entities import Ticket


def nuevo_ticket(titulo: str = "Impresora sin tinta") -> Ticket:
    """Crea un ticket suelto, sin sesion ni base de datos."""
    return Ticket(
        title=titulo,
        description="Caso de prueba",
        category="Hardware",
        priority="Medium",
        requester_id=1,
    )


def test_ticket_nuevo_no_tiene_etiquetas():
    ticket = nuevo_ticket()

    assert ticket.tags == ()


def test_tags_devuelve_una_tupla():
    ticket = nuevo_ticket()
    ticket.add_tag("hardware")

    assert isinstance(ticket.tags, tuple)


def test_add_tag_normaliza_espacios_y_mayusculas():
    ticket = nuevo_ticket()

    ticket.add_tag("   Hardware   ")

    assert ticket.tags == ("hardware",)


def test_add_tag_no_duplica_etiquetas_equivalentes():
    ticket = nuevo_ticket()

    ticket.add_tag("Hardware")
    ticket.add_tag("hardware")
    ticket.add_tag("  HARDWARE ")

    assert ticket.tags == ("hardware",)


def test_add_tag_conserva_el_orden_de_insercion():
    ticket = nuevo_ticket()

    ticket.add_tag("red")
    ticket.add_tag("urgente")

    assert ticket.tags == ("red", "urgente")


@pytest.mark.parametrize("valor", ["", "   ", "\t", "\n"])
def test_add_tag_rechaza_valores_vacios(valor):
    ticket = nuevo_ticket()

    with pytest.raises(ValidationError):
        ticket.add_tag(valor)

    assert ticket.tags == ()


def test_validation_error_es_un_error_de_dominio():
    ticket = nuevo_ticket()

    with pytest.raises(DomainError):
        ticket.add_tag("  ")


def test_las_etiquetas_son_independientes_entre_tickets():
    primero = nuevo_ticket("No imprime")
    segundo = nuevo_ticket("No enciende")

    primero.add_tag("hardware")

    assert primero.tags == ("hardware",)
    assert segundo.tags == ()


def test_no_se_puede_reasignar_la_propiedad_publica():
    ticket = nuevo_ticket()
    ticket.add_tag("hardware")

    with pytest.raises(AttributeError):
        ticket.tags = ["software"]

    assert ticket.tags == ("hardware",)


def test_mutar_la_tupla_devuelta_no_afecta_al_ticket():
    ticket = nuevo_ticket()
    ticket.add_tag("hardware")

    copia = list(ticket.tags)
    copia.append("software")

    assert ticket.tags == ("hardware",)