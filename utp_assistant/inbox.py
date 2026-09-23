"""Bandeja de correos simulados y conector de ingesta (equivalente al Paso 1 del diseno).

Simula un webhook sobre la bandeja de UTPConsult: recibe un correo "entrante",
normaliza remitente/fecha/asunto/cuerpo/adjuntos, lo asocia a un Thread (nuevo
o existente) y queda pendiente de procesamiento por el runner.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any

from . import db

_REMITENTE_RE = re.compile(r"^(?P<nombre>.*?)\s*<(?P<correo>[^>]+)>\s*$")


def parse_remitente(remitente: str) -> tuple[str, str]:
    """Devuelve (nombre, correo) a partir de 'Nombre <correo>' o solo 'correo'."""
    match = _REMITENTE_RE.match(remitente.strip())
    if match:
        return match.group("nombre").strip() or match.group("correo"), match.group("correo")
    return remitente.strip(), remitente.strip()


def list_emails() -> list[dict[str, Any]]:
    return db.list_emails()


def list_pending_emails() -> list[dict[str, Any]]:
    return db.get_pending_emails()


def send_email(
    remitente: str,
    asunto: str,
    cuerpo: str,
    empresa: str = "Cliente",
    adjuntos: Iterable[str] = (),
    fecha: str | None = None,
) -> int:
    """Registra un correo simulado entrante asociado a su Thread (Paso 1 del diseno).

    Si el remitente ya tiene Thread, se reutiliza (cliente con comunicacion previa);
    si no, se crea uno nuevo.
    """
    nombre, correo = parse_remitente(remitente)
    thread_id = db.get_or_create_thread(cliente=nombre, correo_contacto=correo, empresa=empresa)
    return db.add_email(
        thread_id=thread_id,
        remitente=remitente,
        asunto=asunto,
        cuerpo=cuerpo,
        fecha=fecha or datetime.now(UTC).date().isoformat(),
        adjuntos=adjuntos,
    )


def process_pending(client: Any = None, db_path: Any = None) -> list[dict[str, Any]]:
    """Procesa todos los correos pendientes con el runner. Devuelve cada resultado."""
    from . import runner  # import tardio para evitar ciclo

    results = []
    for email in list_pending_emails():
        results.append(runner.process_email(email, client=client, db_path=db_path))
    return results