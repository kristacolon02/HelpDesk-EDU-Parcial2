-- ============================================================
-- Ejercicio 04 del parcial 2: SQL e integridad referencial
-- HelpDesk EDU - PostgreSQL 16
--
-- Ejecucion:
--   psql -h localhost -p 5433 -U helpdesk -d helpdesk \
--        -f docs/database/queries_parcial2.sql
--
-- Requiere haber cargado antes docs/database/seed_parcial2.sql.
-- ============================================================


-- ------------------------------------------------------------
-- (a) Tickets abiertos con el nombre de su solicitante
--
-- El JOIN resuelve la clave foranea tickets.requester_id contra
-- users.id sin el, el listado solo mostraria un numero sin
-- significado para quien atiende la mesa de servicio.
-- ------------------------------------------------------------
SELECT
    t.id            AS ticket_id,
    t.title         AS titulo,
    t.priority      AS prioridad,
    t.status        AS estado,
    u.name          AS solicitante,
    u.email         AS correo_solicitante
FROM tickets AS t
JOIN users AS u ON u.id = t.requester_id
WHERE t.status = 'Open'
ORDER BY t.id;


-- ------------------------------------------------------------
-- (b) Carga de trabajo por tecnico asignado
--
-- Se parte de users y se usa LEFT JOIN para que tambien entren
-- los tecnicos sin tickets el HAVING los excluye despues. Con un
-- JOIN interno el HAVING seria decorativo porque ningun grupo
-- podria tener conteo cero.
--
-- El GROUP BY incluye id y nombre, el id garantiza que dos
-- personas homonimas no se mezclen en un mismo grupo.
-- ------------------------------------------------------------
SELECT
    u.id            AS tecnico_id,
    u.name          AS tecnico,
    COUNT(t.id)     AS tickets_asignados
FROM users AS u
LEFT JOIN tickets AS t ON t.assignee_id = u.id
WHERE u.role IN ('technician', 'supervisor')
GROUP BY u.id, u.name
HAVING COUNT(t.id) > 0
ORDER BY tickets_asignados DESC, u.id;


-- ------------------------------------------------------------
-- (c) Tickets sin ningun comentario
--
-- NOT EXISTS se detiene en cuanto encuentra la primera fila
-- coincidente a diferencia de un LEFT JOIN que materializa todas
-- las combinaciones antes de filtrar por NULL. Con indice sobre
-- comments.ticket_id es la forma mas directa de expresar la
-- ausencia de filas relacionadas.
-- ------------------------------------------------------------
SELECT
    t.id            AS ticket_id,
    t.title         AS titulo,
    t.status        AS estado
FROM tickets AS t
WHERE NOT EXISTS (
    SELECT 1
    FROM comments AS c
    WHERE c.ticket_id = t.id
)
ORDER BY t.id;


-- ------------------------------------------------------------
-- (d) Demostracion de ON DELETE CASCADE sobre el historial
--
-- La llave foranea history.ticket_id declara ON DELETE CASCADE
-- al borrar el ticket la base elimina sus eventos sin que la
-- aplicacion tenga que hacerlo. Toda la demostracion ocurre
-- dentro de una transaccion que termina en ROLLBACK, de modo que
-- los datos quedan intactos al finalizar.
-- ------------------------------------------------------------
BEGIN;

-- 1. Conteo inicial, debe ser mayor que cero.
SELECT 'd1. historial inicial del ticket 1' AS paso,
       COUNT(*) AS eventos
FROM history
WHERE ticket_id = 1;

-- 2. Se borra el ticket padre. No se toca la tabla history.
DELETE FROM tickets WHERE id = 1;

-- 3. Conteo tras el DELETE, la cascada ya vacio el historial.
SELECT 'd2. historial tras DELETE del ticket' AS paso,
       COUNT(*) AS eventos
FROM history
WHERE ticket_id = 1;

-- 4. Se deshace todo.
ROLLBACK;

-- 5. Conteo tras el ROLLBACK, el historial vuelve a su estado
--    original, lo que prueba que la demostracion no dejo danos.
SELECT 'd3. historial tras ROLLBACK' AS paso,
       COUNT(*) AS eventos
FROM history
WHERE ticket_id = 1;


-- ------------------------------------------------------------
-- Verificacion final - los datos quedaron intactos.
-- ------------------------------------------------------------
SELECT
    (SELECT COUNT(*) FROM users)    AS usuarios,
    (SELECT COUNT(*) FROM tickets)  AS tickets,
    (SELECT COUNT(*) FROM comments) AS comentarios,
    (SELECT COUNT(*) FROM history)  AS eventos_historial;
