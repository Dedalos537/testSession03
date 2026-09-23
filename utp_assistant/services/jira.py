"""SIM_Jira: simulacion local de la API de Jira para crear tareas (issues)."""

from __future__ import annotations

from typing import Any

from .. import db
from . import validate_enum, validate_params

_REQUIRED = ["proyecto_key", "titulo", "descripcion", "cliente_relacionado"]
_PRIORIDADES = ["Baja", "Media", "Alta", "Urgente"]


def create_task(
    args: dict[str, Any],
    *,
    run_id: str | None = None,
    origen: str | None = None,
) -> dict[str, Any]:
    """Crea una tarea en Jira (simulado). Devuelve {ok, key, ...} o {ok: False, error}."""
    error = validate_params(args, _REQUIRED)
    if error:
        return error
    error = validate_enum(args, "prioridad", _PRIORIDADES)
    if error:
        return error

    proyecto_key = args["proyecto_key"]
    key = db.next_jira_key(proyecto_key)
    result = db.create_jira_task(
        key=key,
        proyecto_key=proyecto_key,
        titulo=args["titulo"],
        descripcion=args["descripcion"],
        prioridad=args.get("prioridad", "Media"),
        cliente_relacionado=args["cliente_relacionado"],
        fecha_limite=args.get("fecha_limite"),
        run_id=run_id,
        origen=origen,
    )
    return {
        "ok": True,
        "message": f"Tarea {key} creada en Jira",
        **result,
    }