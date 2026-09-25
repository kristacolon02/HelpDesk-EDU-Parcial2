-- ============================================================
-- Datos de prueba para el ejercicio 04 del parcial 2
-- HelpDesk EDU - PostgreSQL
--
-- Requiere que el esquema ya exista (lo crea la aplicacion con
-- Base.metadata.create_all al conectarse a PostgreSQL).
-- ============================================================

BEGIN;

-- Limpieza previa. El orden importa mientras no todas las tablas
-- tengan cascada, primero los hijos, despues los padres.
DELETE FROM history;
DELETE FROM comments;
DELETE FROM tickets;
DELETE FROM users WHERE id > 4;

-- ------------------------------------------------------------
-- Usuarios adicionales
-- seed_users ya inserto: 1 Admin, 2 Supervisor, 3 Technician,
-- 4 Requester. Se agregan un segundo tecnico y un segundo
-- solicitante para que las agregaciones tengan varios grupos.
-- ------------------------------------------------------------
INSERT INTO users (id, email, name, role, password_hash) VALUES
    (5, 'tecnico2@example.com',     'Tecnico Dos',     'technician', 'x'),
    (6, 'solicitante2@example.com', 'Solicitante Dos', 'requester',  'x');

-- ------------------------------------------------------------
-- Tickets
-- ------------------------------------------------------------
INSERT INTO tickets (id, title, description, category, priority, status, requester_id, assignee_id, created_at, due_at) VALUES
    (1, 'Impresora sin tinta',        'La impresora del aula 3 no imprime', 'Hardware', 'High',     'Open',        4, 3,    now(), now() + interval '24 hours'),
    (2, 'No puedo iniciar sesion',    'El portal rechaza mi contrasena',    'Software', 'Medium',   'Open',        4, 3,    now(), now() + interval '48 hours'),
    (3, 'Wifi intermitente',          'Se cae la senal en el laboratorio',  'Network',  'Low',      'In Progress', 6, 5,    now(), now() + interval '72 hours'),
    (4, 'Monitor quemado',            'El monitor no enciende',             'Hardware', 'Critical', 'Closed',      4, 3,    now(), now() + interval '4 hours'),
    (5, 'Solicitud de licencia',      'Necesito licencia de ofimatica',     'General',  'Medium',   'Open',        6, NULL, now(), now() + interval '48 hours');

-- ------------------------------------------------------------
-- Comentarios
-- Solo los tickets 1 y 3 tienen comentarios: los tickets 2, 4 y 5
-- quedan vacios, para que la consulta (c) tenga resultados.
-- ------------------------------------------------------------
INSERT INTO comments (id, ticket_id, author_id, body, created_at) VALUES
    (1, 1, 3, 'Se solicito el toner al proveedor.', now()),
    (2, 1, 4, 'Gracias, quedo pendiente.',          now()),
    (3, 3, 5, 'Se reviso el punto de acceso.',      now());

-- ------------------------------------------------------------
-- Historial
-- El ticket 1 acumula tres eventos: es el que se usa en la
-- demostracion de ON DELETE CASCADE.
-- ------------------------------------------------------------
INSERT INTO history (id, ticket_id, actor_id, event_type, detail, created_at) VALUES
    (1, 1, 4, 'created',        'Ticket created',        now()),
    (2, 1, 2, 'assigned',       'Assigned to Technician', now()),
    (3, 1, 3, 'commented',      'Comment added',          now()),
    (4, 2, 4, 'created',        'Ticket created',         now()),
    (5, 3, 6, 'created',        'Ticket created',         now()),
    (6, 4, 4, 'created',        'Ticket created',         now()),
    (7, 4, 3, 'closed',         'Ticket closed',          now()),
    (8, 5, 6, 'created',        'Ticket created',         now());

-- ------------------------------------------------------------
-- Las secuencias se reposicionan porque los ids se insertaron a
-- mano, sin esto el proximo INSERT automatico toparia con un id
-- ya usado.
-- ------------------------------------------------------------
SELECT setval('users_id_seq',    (SELECT MAX(id) FROM users));
SELECT setval('tickets_id_seq',  (SELECT MAX(id) FROM tickets));
SELECT setval('comments_id_seq', (SELECT MAX(id) FROM comments));
SELECT setval('history_id_seq',  (SELECT MAX(id) FROM history));

COMMIT;
