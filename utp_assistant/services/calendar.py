"""SIM_Calendar: simulacion local de Google Calendar para crear eventos."""

from __future__ import annotations

from typing import Any

from .. import db
from . import validate_params

_REQUIRED = ["titulo", "asistentes", "agenda", "es_tentativa"]


def create_event(args: dict[str, Any]) -> dict[str, Any]:
    """Crea un evento (propuesta tentativa) en Calendar. Devuelve {ok, id, ...}."""
    error = validate_params(args, _REQUIRED)
    if error:
        return error

    result = db.create_calendar_event(
        titulo=args["titulo"],
        asistentes=args.get("asistentes", []),
        agenda=args["agenda"],
        es_tentativa=bool(args.get("es_tentativa", True)),
        fecha_propuesta=args.get("fecha_propuesta"),
        hora_propuesta=args.get("hora_propuesta"),
        duracion_minutos=args.get("duracion_minutos", 30),
    )
    return {
        "ok": True,
        "message": (
            "Evento tentativo creado en Google Calendar (pendiente de confirmacion)"
            if result["es_tentativa"]
            else "Evento creado en Google Calendar"
        ),
        **result,
    }