# HelpDesk EDU — Segundo Parcial

Repositorio de la Serie II del segundo parcial.
Sale de una copia del proyecto HelpDesk EDU visto en clase y agrega los 5
ejercicios solicitados, cada uno en su propia rama y sus pruebas.

- **Repositorio:** https://github.com/kristacolon02/HelpDesk-EDU-Parcial2
- **Proyecto base:** https://github.com/rortizs/HelpDesk-EDU_Estudents

## Requisitos previos

- Python 3.12
- [uv](https://docs.astral.sh/uv/)
- Docker Desktop (solo para el ejercicio 4)

## Reproducir pruebas

Instalacion y pruebas:

    uv venv .venv --python 3.12
    uv sync --all-groups
    uv run pytest -q

Para el ejercicio 4 que requiere PostgreSQL:

    docker compose up -d db

El esquema lo crea la aplicacion al conectarse por primera vez a la base
"helpdesk" en localhost:5433:

    uv run python -c "
    from app.core.database import create_session_factory
    from app.services.auth import seed_users
    url = 'postgresql+psycopg://helpdesk:helpdesk@localhost:5433/helpdesk'
    factory = create_session_factory(url)
    with factory() as db:
        seed_users(db)
    "

Con el esquema creado, se cargan los datos y se ejecutan las consultas:

    docker compose exec -T db psql -U helpdesk -d helpdesk < docs/database/seed_parcial2.sql
    docker compose exec -T db psql -U helpdesk -d helpdesk < docs/database/queries_parcial2.sql

## Estructura de ramas

    main
     +-- developer
          +-- Feacture_etiquetasEcapsuladas
          +-- Feacture_observadoresTicket
          +-- Feacture_excepcionesPolimorfismo
          +-- Feacture_consultasSQL
          +-- Feacture_agregacionSQLAlchemy

Cada rama contiene su respectivo commit y se integro a `developer`,
`developer` se integra a `main` al final de todo.

Nota: Los ejercicios 01 y 02 se integraron directamente a `main` por un error que cometi al leer las instrucciones. 
A partir del ejercicio 03 ya es en el orden correcto feature → developer → main. 
Las ramas de los dos primeros ejercicios conservan su historial completo.

## Estado previo

Antes de cualquier modificacion, las pruebas del proyecto base pasaban
completas: **9 passed**. No habia fallos anteriores que reportar.

Luego de los cinco incrementos: **42 passed**.

| Ejercicio | Pruebas agregadas |
|---|---|
| Base del proyecto | 9 |
| 1 — Etiquetas y encapsulamiento | 13 |
| 2 — Observadores | 5 |
| 3 — Excepciones y polimorfismo | 10 |
| 4 — SQL (evidencia en PostgreSQL) | — |
| 5 — Agregacion y persistencia | 5 |
| **Total** | **42** |

Las salidas completas estan en `docs/evidencias/`.

---

## Ejercicio 1 — Etiquetas y encapsulamiento

**Rama:** `Feacture_etiquetasEcapsuladas`

**Archivos:** `app/domain/errors.py`, `app/models/entities.py`,
`tests/test_parcial2_01_tags.py`

Se agrego a `Ticket` una coleccion privada de etiquetas expuesta mediante la
propiedad de solo lectura `tags`, que devuelve una tupla. `add_tag()` normaliza
con `strip().lower()`, rechaza valores vacios con `ValidationError` y evita
duplicados. Como la propiedad no define setter, `ticket.tags = [...]` lanza
`AttributeError`.

**Adaptacion:** el enunciado pide declarar la coleccion con
`field(default_factory=list, init=False, repr=False)`, sintaxis propia de
dataclass. En este proyecto `Ticket` es una entidad declarativa de SQLAlchemy
no un dataclass, asi que las tres garantias de esa declaracion se replican por
otra via `_tag_store()` crea la lista en el primer uso, una por instancia sin
lista mutable compartida a nivel de clase, el atributo no participa del
constructor generado por el ORM y al no estar mapeado queda fuera del repr.
Las etiquetas viven en memoria y no requieren migracion SQL, como indica el
enunciado.

![Pruebas del ejercicio 01](docs/evidencias/01_screenshot.png)



## Ejercicio 2 — Observadores y relaciones entre objetos

**Rama:** `Feacture_observadoresTicket`

**Archivos:** `app/services/tickets.py`, `tests/test_parcial2_02_watchers.py`

`TicketService.watchers(ticket_id)` devuelve el solicitante y cuando existe el
tecnico asignado. La deduplicacion se hace por id y no por identidad de objeto,
porque dos consultas distintas pueden devolver cosas diferentes del mismo
usuario. Si el ticket no existe, el error continua y no se queda dentro de esa funcion.

**Adaptacion:** el enunciado usa `self.require(ticket_id)` y
`self._users.require(id)`. En este proyecto el servicio exponia `_ticket()` y el
colaborador de usuarios se llama `self.users`, asi que se agregaron `require()`
y `_require_user()` como equivalentes dentro del mismo servicio. No se accede al
repositorio de ningun otro servicio.

![Pruebas del ejercicio 02](docs/evidencias/02_screenshot.png)



## Ejercicio 3 — Excepciones y polimorfismo

**Rama:** `Feacture_excepcionesPolimorfismo`

**Archivos:** `app/domain/errors.py`, `app/services/notifications.py`,
`app/services/tickets.py`, `tests/test_parcial2_03_excepciones.py`

`DuplicateAssignmentError` hereda de `DomainError`. En `assign()` la asignacion
al tecnico que el ticket ya tiene se rechaza **antes** de mutar el ticket,
registrar historial o emitir notificaciones, de modo que un intento invalido no
deja registro. Las validaciones previas (tecnico inexistente, rol no
autorizado) se conservan.

`Notifier` es una clase abstracta con `notify` declarado `@abstractmethod`;
`NullNotifier` es la implementacion segura usada por defecto y
`WebhookNotifier` simula el canal acumulando cada envio en `sent_payloads`, sin
HTTP ni impresion. El servicio llama siempre `self.notifier.notify(...)`, sin
ningun condicional por tipo.

**Adaptacion:** el enunciado habla de "el parametro notifier existente", pero
`TicketService` no lo tenia. Se agrego como parametro opcional con
`NullNotifier` por defecto, por lo que las llamadas actuales desde las rutas
siguen funcionando sin cambios.

**Limitacion conocida:** `DuplicateAssignmentError` se gwnera en la capa de
servicios y no se cambia a un codigo HTTP, porque el enunciado limita los
archivos a modificar y el manejador tendria que registrarse en `app/main.py`.
Invocada a traves del API, esa condicion devolveria un error 500.

![Pruebas del ejercicio 03](docs/evidencias/03_screenshot.png)



## Ejercicio 4 — SQL e integridad referencial

**Rama:** `Feacture_consultasSQL`

**Archivos:** `docker-compose.yml`, `app/models/entities.py`,
`docs/database/seed_parcial2.sql`, `docs/database/queries_parcial2.sql`

Cuatro consultas ejecutadas contra PostgreSQL 16 en contenedor. La salida
completa esta en `docs/evidencias/ej4_consultas.txt`.

- **(a)** Tickets abiertos con el nombre del solicitante, resolviendo la clave
  foranea con JOIN. Resultado: 3 filas.
- **(b)** Carga de trabajo por tecnico con LEFT JOIN desde users para que los
  tecnicos sin tickets entren al agrupamiento y el HAVING COUNT(...) > 0 los
  excluya despues; GROUP BY por id y nombre, orden descendente. Resultado: 2
  filas. Con un JOIN interno el HAVING seria decorativo, porque ningun grupo
  podria tener conteo cero.
- **(c)** Tickets sin comentarios mediante NOT EXISTS. Resultado: 3 filas.
- **(d)** Demostracion de ON DELETE CASCADE sobre el historial, dentro de una
  transaccion cerrada con ROLLBACK:

      d1. historial inicial del ticket 1    ->  3
      d2. historial tras DELETE del ticket  ->  0
      d3. historial tras ROLLBACK           ->  3

La verificacion final confirma que los datos quedaron intactos. 6 usuarios,
5 tickets, 3 comentarios y 8 eventos de historial.

**Adaptaciones:**

1. El servicio `db` del `docker-compose.yml` no publicaba ningun puerto, por lo
   que la base solo era posible desde la red interna de Docker. Se agrego
   `5433:5432` para ejecutar las consultas desde el host sin interferir con una
   instalacion local de PostgreSQL en el 5432.
2. Las llaves foraneas `comments.ticket_id` e `history.ticket_id` no declaraban
   ON DELETE CASCADE, lo que hacia imposible el inciso (d): el DELETE habria
   fallado por violacion de integridad referencial. Se agrego
   `ondelete="CASCADE"` en el modelo ORM, que es lo que genera esa clausula en
   el esquema.
3. El proyecto no incluye `docs/database/database.sql`, el esquema lo crea
   `Base.metadata.create_all` al conectarse. Se documento el procedimiento
   reproducible arriba y se agrego `seed_parcial2.sql` con los datos de prueba,
   escrito de forma idempotente para poder ejecutarlo varias veces.
   
![Pruebas del ejercicio 04](docs/evidencias/04_screenshot.png)



## Ejercicio 5 — Consulta agregada y persistencia con SQLAlchemy

**Rama:** `Feacture_agregacionSQLAlchemy`

**Archivos:** `app/repositories/tickets.py`,
`tests/test_parcial2_05_agregacion.py`

`count_by_status()` resuelve la combinacipn en la base con
`select(Ticket.status, func.count()).group_by(Ticket.status)` sin traer las
filas a memoria para contarlas en Python. Devuelve solo los estados presentes y
un diccionario vacio cuando no hay tickets, porque GROUP BY no produce filas si
no hay nada que agrupar.

La prueba principal no se conforma con leer dentro de la misma sesion que
escribio, crea tres tickets en dos estados, confirma la transaccion, cierra esa
sesion y consulta desde una sesion nueva sobre el mismo engine SQLite en
memoria con StaticPool. Es lo unico que demuestra que el dato quedo en la base
y no en la cache de identidad de SQLAlchemy.

**Adaptacion:** el enunciado nombra `app/repositories/sqlalchemy.py`, la clase
`SqlAlchemyTicketRepository` y el modelo `TicketORM`. En este proyecto el
repositorio vive en `app/repositories/tickets.py`, se llama `TicketRepository` y
el modelo es `Ticket`. La condicion "no cambie la interfaz abstracta
TicketRepository" se cumple automaticamente, el proyecto no define una clase
abstracta, el repositorio es concreto y el metodo se agrego sin alterar ninguna
firma existente.

**Nota:** los tickets se insertan directamente con su estado final, sin pasar 
por `change_status()` de manera que no se ejecuta ninguna transicion de estado 
para preparar el caso de prueba.
   
![Pruebas del ejercicio 05](docs/evidencias/05_screenshot.png)



---

## Limitacion general del enunciado

Los cinco enunciados fueron redactados para una arquitectura hexagonal
(dominio con dataclasses, repositorios abstractos con ABC, puerto de
notificacion) que este proyecto FastAPI no usa. Cada ejercicio se
resolvio conservando la estructura actual del proyecto, las diferencias 
de nombres o clases quedan documentadas en la seccion de cada ejercicio.

## Dependencia removida

Se quitó el extra `[cryptography]` de `python-jose` en `pyproject.toml` porque
no compila en mi macOS sin OpenSSL ni Rust. El proyecto usa HS256 y
`pbkdf2_sha256`, que no dependen de esa librería.

## Evidencias

| Archivo | Contenido |
|---|---|
| `docs/evidencias/ej1_pruebas.txt` | Pruebas del ejercicio 1, detalladas |
| `docs/evidencias/ej2_pruebas.txt` | Pruebas del ejercicio 2, detalladas |
| `docs/evidencias/ej3_pruebas.txt` | Pruebas del ejercicio 3, detalladas |
| `docs/evidencias/ej4_consultas.txt` | Salida de las cuatro consultas en PostgreSQL |
| `docs/evidencias/ej5_pruebas.txt` | Pruebas del ejercicio 5, detalladas |
| `docs/evidencias/resultado_pruebas.txt` | Corrida completa: 42 passed |
| `docs/evidencias/git_historial.txt` | Historial de ramas, commits y merges |


