"""Capa de datos SQLite del prototipo UTP Assistant.

Estructura de almacenamiento equivalente al diseño de la propuesta:
- ``threads``  -> "Thread" de la Assistants API (un hilo por cliente/prospecto).
- ``messages`` -> historial de mensajes del thread (roles system/user/assistant/tool).
- ``emails``   -> correos simulados recibidos (bandeja + conector de ingesta).
- ``jira_tasks`` / ``calendar_events`` / ``crm_contacts`` / ``slack_messages``
  -> sistemas externos SIMULADOS (Jira, Calendar, CRM, Slack).
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import sqlite3
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .config import DB_PATH

_SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre     TEXT    NOT NULL,
    email      TEXT    NOT NULL UNIQUE,
    pass_hash  TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS threads (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente         TEXT    NOT NULL,
    correo_contacto TEXT    NOT NULL,
    empresa         TEXT    NOT NULL,
    created_at      TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS messages (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    thread_id  INTEGER NOT NULL REFERENCES threads(id),
    role       TEXT    NOT NULL,
    content    TEXT    NOT NULL,
    created_at TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS emails (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    thread_id    INTEGER NOT NULL REFERENCES threads(id),
    remitente    TEXT    NOT NULL,
    asunto       TEXT    NOT NULL,
    cuerpo       TEXT    NOT NULL,
    fecha        TEXT    NOT NULL,
    adjuntos     TEXT    NOT NULL DEFAULT '[]',
    procesado    INTEGER NOT NULL DEFAULT 0,
    run_id       TEXT
);

CREATE TABLE IF NOT EXISTS jira_tasks (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    key                TEXT    NOT NULL UNIQUE,
    proyecto_key       TEXT    NOT NULL,
    titulo             TEXT    NOT NULL,
    descripcion        TEXT    NOT NULL,
    prioridad          TEXT    NOT NULL,
    cliente_relacionado TEXT   NOT NULL,
    fecha_limite       TEXT,
    created_at         TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS calendar_events (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo           TEXT    NOT NULL,
    asistentes       TEXT    NOT NULL DEFAULT '[]',
    fecha_propuesta  TEXT,
    hora_propuesta   TEXT,
    duracion_minutos INTEGER,
    agenda           TEXT    NOT NULL,
    es_tentativa     INTEGER NOT NULL DEFAULT 1,
    created_at       TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS crm_contacts (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_contacto             TEXT    NOT NULL,
    empresa                     TEXT    NOT NULL,
    correo_electronico          TEXT    NOT NULL UNIQUE,
    etapa_pipeline              TEXT    NOT NULL,
    interes_principal           TEXT,
    ultima_interaccion_resumen  TEXT    NOT NULL,
    documentos_adjuntos         TEXT    NOT NULL DEFAULT '[]',
    updated_at                  TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS slack_messages (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    canal               TEXT    NOT NULL,
    resumen_ejecutivo   TEXT    NOT NULL,
    acciones_realizadas TEXT    NOT NULL DEFAULT '[]',
    alertas             TEXT    NOT NULL DEFAULT '[]',
    nivel_urgencia      TEXT    NOT NULL DEFAULT 'Normal',
    created_at          TEXT    NOT NULL
);
"""


def utcnow() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


# --------------------------------------------------------------------------- #
# Conexión e inicializacion
# --------------------------------------------------------------------------- #

def get_connection(db_path: Path | str | None = None) -> sqlite3.Connection:
    """Devuelve una conexion SQLite con row_factory activo. Crea el archivo si falta."""
    db_path = DB_PATH if db_path is None else db_path
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: Path | str | None = None) -> None:
    """Crea las tablas (idempotente)."""
    conn = get_connection(db_path)
    try:
        conn.executescript(_SCHEMA)
        conn.commit()
    finally:
        conn.close()


# --------------------------------------------------------------------------- #
# Password (prototipo: sha256 + salt, NO usar en produccion)
# --------------------------------------------------------------------------- #

def _hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or os.urandom(16).hex()
    digest = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    """Verifica una contrasena contra el hash almacenado ('salt$digest')."""
    if "$" not in stored:
        return False
    salt, expected = stored.split("$", 1)
    digest = hashlib.sha256((salt + password).encode()).hexdigest()
    return hmac.compare_digest(digest, expected)


def _verify_password(password: str, stored: str) -> bool:
    return verify_password(password, stored)


# --------------------------------------------------------------------------- #
# Usuarios internos
# --------------------------------------------------------------------------- #

def seed(db_path: Path | str | None = None, password: str = "demo123") -> None:
    """Inserta datos de ejemplo si la BD esta vacia (idempotente).

    - 2 usuarios internos (red interna de 2 usuarios).
    - Thread de TechCorp (Ana Torres) con correo que SI requiere acciones.
    - Thread de Grupo Innova con correo de agradecimiento (sin acciones).
    """
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        if conn.execute("SELECT COUNT(*) AS n FROM users").fetchone()["n"] > 0:
            return

        p1 = _hash_password(password)
        p2 = _hash_password(password)
        conn.execute(
            "INSERT INTO users (nombre, email, pass_hash) VALUES (?, ?, ?)",
            ("Bernardo Rivera", "bernie.rivera@utpconsult.com", p1),
        )
        conn.execute(
            "INSERT INTO users (nombre, email, pass_hash) VALUES (?, ?, ?)",
            ("Odalis Dominguez", "odalis.dominguez@utpconsult.com", p2),
        )

        now = utcnow()

        # Thread 1: TechCorp (requiere acciones)
        t1 = conn.execute(
            "INSERT INTO threads (cliente, correo_contacto, empresa, created_at) "
            "VALUES (?, ?, ?, ?)",
            ("Ana Torres", "ana.torres@techcorp.com", "TechCorp", now),
        ).lastrowid
        conn.execute(
            "INSERT INTO emails (thread_id, remitente, asunto, cuerpo, fecha, adjuntos) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                t1,
                "Ana Torres <ana.torres@techcorp.com>",
                "Re: Propuesta modulo de pagos",
                (
                    "Hola equipo de UTP Consult, gracias por la propuesta. "
                    "Nos interesa avanzar. "
                    "¿Podríamos tener una reunión la próxima semana para discutir "
                    "los detalles técnicos del módulo de pagos? "
                    "Adjunto un documento con algunos requisitos iniciales.\n\n"
                    "Saludos, Ana Torres de TechCorp."
                ),
                "2026-09-22",
                '["requisitos_iniciales.pdf"]',
            ),
        )

        # Thread 2: Grupo Innova (sin accion requerida)
        t2 = conn.execute(
            "INSERT INTO threads (cliente, correo_contacto, empresa, created_at) "
            "VALUES (?, ?, ?, ?)",
            ("Carlos Mendoza", "carlos.mendoza@grupoinnova.pe", "Grupo Innova", now),
        ).lastrowid
        conn.execute(
            "INSERT INTO emails (thread_id, remitente, asunto, cuerpo, fecha, adjuntos) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                t2,
                "Carlos Mendoza <carlos.mendoza@grupoinnova.pe>",
                "Gracias por la propuesta",
                (
                    "Gracias equipo, la revisaremos con nuestra directiva. "
                    "Por ahora no requerimos ninguna accion adicional."
                ),
                "2026-09-22",
                "[]",
            ),
        )

        conn.commit()
    finally:
        conn.close()


# --------------------------------------------------------------------------- #
# Helpers de serializacion
# --------------------------------------------------------------------------- #


def _resolve(db_path: Path | str | None) -> Path | str:
    """Resuelve el path efectivo: None -> modulo DB_PATH (permite override en tests)."""
    return DB_PATH if db_path is None else db_path


def _dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def _loads(value: str) -> Any:
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return []


# --------------------------------------------------------------------------- #
# Threads y mensajes (equivalente a Thread + Messages de la API)
# --------------------------------------------------------------------------- #

def get_or_create_thread(
    cliente: str, correo_contacto: str, empresa: str, db_path: Path | str | None = None
) -> int:
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT id FROM threads WHERE correo_contacto = ?",
            (correo_contacto,),
        ).fetchone()
        if row:
            return int(row["id"])
        return int(
            conn.execute(
                "INSERT INTO threads (cliente, correo_contacto, empresa, created_at) "
                "VALUES (?, ?, ?, ?)",
                (cliente, correo_contacto, empresa, utcnow()),
            ).lastrowid
        )
    finally:
        conn.commit()
        conn.close()


def add_message(
    thread_id: int, role: str, content: str, db_path: Path | str | None = None
) -> int:
    conn = get_connection(db_path)
    try:
        return int(
            conn.execute(
                "INSERT INTO messages (thread_id, role, content, created_at) "
                "VALUES (?, ?, ?, ?)",
                (thread_id, role, content, utcnow()),
            ).lastrowid
        )
    finally:
        conn.commit()
        conn.close()


def get_thread_messages(
    thread_id: int, db_path: Path | str | None = None
) -> list[dict[str, Any]]:
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT role, content FROM messages WHERE thread_id = ? ORDER BY id",
            (thread_id,),
        ).fetchall()
        return [{"role": r["role"], "content": r["content"]} for r in rows]
    finally:
        conn.close()


# --------------------------------------------------------------------------- #
# Bandeja de correos simulados
# --------------------------------------------------------------------------- #

def add_email(
    thread_id: int,
    remitente: str,
    asunto: str,
    cuerpo: str,
    fecha: str,
    adjuntos: Iterable[str] = (),
    db_path: Path | str | None = None,
) -> int:
    conn = get_connection(db_path)
    try:
        return int(
            conn.execute(
                "INSERT INTO emails (thread_id, remitente, asunto, cuerpo, fecha, adjuntos) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (thread_id, remitente, asunto, cuerpo, fecha, _dumps(list(adjuntos))),
            ).lastrowid
        )
    finally:
        conn.commit()
        conn.close()


def get_pending_emails(db_path: Path | str | None = None) -> list[dict[str, Any]]:
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT * FROM emails WHERE procesado = 0 ORDER BY id"
        ).fetchall()
        return [dict(r) | {"adjuntos": _loads(r["adjuntos"])} for r in rows]
    finally:
        conn.close()


def list_emails(db_path: Path | str | None = None) -> list[dict[str, Any]]:
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT e.*, t.cliente, t.empresa FROM emails e "
            "JOIN threads t ON t.id = e.thread_id ORDER BY e.id DESC"
        ).fetchall()
        return [dict(r) | {"adjuntos": _loads(r["adjuntos"])} for r in rows]
    finally:
        conn.close()


def mark_email_processed(
    email_id: int, run_id: str, db_path: Path | str | None = None
) -> None:
    conn = get_connection(db_path)
    try:
        conn.execute(
            "UPDATE emails SET procesado = 1, run_id = ? WHERE id = ?",
            (run_id, email_id),
        )
    finally:
        conn.commit()
        conn.close()


# --------------------------------------------------------------------------- #
# Sistemas externos simulados (Jira / Calendar / CRM / Slack)
# --------------------------------------------------------------------------- #

def next_jira_key(proyecto_key: str, db_path: Path | str | None = None) -> str:
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT COUNT(*) AS n FROM jira_tasks WHERE proyecto_key = ?",
            (proyecto_key,),
        ).fetchone()
        return f"{proyecto_key}-{int(row['n']) + 1}"
    finally:
        conn.close()


def create_jira_task(
    key: str,
    proyecto_key: str,
    titulo: str,
    descripcion: str,
    prioridad: str,
    cliente_relacionado: str,
    fecha_limite: str | None = None,
    db_path: Path | str | None = None,
) -> dict[str, Any]:
    conn = get_connection(db_path)
    try:
        task_id = int(
            conn.execute(
                "INSERT INTO jira_tasks (key, proyecto_key, titulo, descripcion, "
                "prioridad, cliente_relacionado, fecha_limite, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (key, proyecto_key, titulo, descripcion, prioridad,
                 cliente_relacionado, fecha_limite, utcnow()),
            ).lastrowid
        )
        return {"id": task_id, "key": key, "proyecto": proyecto_key}
    finally:
        conn.commit()
        conn.close()


def list_jira_tasks(db_path: Path | str | None = None) -> list[dict[str, Any]]:
    conn = get_connection(db_path)
    try:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM jira_tasks ORDER BY id DESC"
        ).fetchall()]
    finally:
        conn.close()


def create_calendar_event(
    titulo: str,
    asistentes: Iterable[str],
    agenda: str,
    es_tentativa: bool,
    fecha_propuesta: str | None = None,
    hora_propuesta: str | None = None,
    duracion_minutos: int | None = 30,
    db_path: Path | str | None = None,
) -> dict[str, Any]:
    conn = get_connection(db_path)
    try:
        event_id = int(
            conn.execute(
                "INSERT INTO calendar_events (titulo, asistentes, fecha_propuesta, "
                "hora_propuesta, duracion_minutos, agenda, es_tentativa, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (titulo, _dumps(list(asistentes)), fecha_propuesta, hora_propuesta,
                 duracion_minutos, agenda, 1 if es_tentativa else 0, utcnow()),
            ).lastrowid
        )
        return {"id": event_id, "titulo": titulo, "es_tentativa": es_tentativa}
    finally:
        conn.commit()
        conn.close()


def list_calendar_events(db_path: Path | str | None = None) -> list[dict[str, Any]]:
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT * FROM calendar_events ORDER BY id DESC"
        ).fetchall()
        return [dict(r) | {"asistentes": _loads(r["asistentes"])} for r in rows]
    finally:
        conn.close()


def upsert_crm_contact(
    nombre_contacto: str,
    empresa: str,
    correo_electronico: str,
    etapa_pipeline: str,
    ultima_interaccion_resumen: str,
    interes_principal: str | None = None,
    documentos_adjuntos: Iterable[str] = (),
    db_path: Path | str | None = None,
) -> dict[str, Any]:
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT id FROM crm_contacts WHERE correo_electronico = ?",
            (correo_electronico,),
        ).fetchone()
        now = utcnow()
        if row:
            conn.execute(
                "UPDATE crm_contacts SET nombre_contacto = ?, empresa = ?, "
                "etapa_pipeline = ?, interes_principal = ?, "
                "ultima_interaccion_resumen = ?, documentos_adjuntos = ?, updated_at = ? "
                "WHERE id = ?",
                (nombre_contacto, empresa, etapa_pipeline, interes_principal,
                 ultima_interaccion_resumen, _dumps(list(documentos_adjuntos)), now,
                 row["id"]),
            )
            return {"id": row["id"], "accion": "actualizado"}
        contact_id = int(
            conn.execute(
                "INSERT INTO crm_contacts (nombre_contacto, empresa, correo_electronico, "
                "etapa_pipeline, interes_principal, ultima_interaccion_resumen, "
                "documentos_adjuntos, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (nombre_contacto, empresa, correo_electronico, etapa_pipeline,
                 interes_principal, ultima_interaccion_resumen,
                 _dumps(list(documentos_adjuntos)), now),
            ).lastrowid
        )
        return {"id": contact_id, "accion": "creado"}
    finally:
        conn.commit()
        conn.close()


def list_crm_contacts(db_path: Path | str | None = None) -> list[dict[str, Any]]:
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT * FROM crm_contacts ORDER BY id DESC"
        ).fetchall()
        return [dict(r) | {"documentos_adjuntos": _loads(r["documentos_adjuntos"])} for r in rows]
    finally:
        conn.close()


def create_slack_message(
    canal: str,
    resumen_ejecutivo: str,
    acciones_realizadas: Iterable[str],
    nivel_urgencia: str,
    alertas: Iterable[str] = (),
    db_path: Path | str | None = None,
) -> dict[str, Any]:
    conn = get_connection(db_path)
    try:
        msg_id = int(
            conn.execute(
                "INSERT INTO slack_messages (canal, resumen_ejecutivo, "
                "acciones_realizadas, alertas, nivel_urgencia, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (canal, resumen_ejecutivo, _dumps(list(acciones_realizadas)),
                 _dumps(list(alertas)), nivel_urgencia, utcnow()),
            ).lastrowid
        )
        return {"id": msg_id, "canal": canal}
    finally:
        conn.commit()
        conn.close()


def list_slack_messages(db_path: Path | str | None = None) -> list[dict[str, Any]]:
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT * FROM slack_messages ORDER BY id DESC"
        ).fetchall()
        return [
            dict(r)
            | {"acciones_realizadas": _loads(r["acciones_realizadas"])}
            | {"alertas": _loads(r["alertas"])}
            for r in rows
        ]
    finally:
        conn.close()