"""SIM_Slack: simulacion local del webhook de Slack para notificaciones internas."""

from __future__ import annotations

from typing import Any

from .. import db
from . import validate_enum, validate_params

_REQUIRED = ["canal", "resumen_ejecutivo", "acciones_realizadas", "nivel_urgencia"]
_NIVELES = ["Normal", "Alta", "Critica"]


def send_notification(args: dict[str, Any]) -> dict[str, Any]:
    """Envia una notificacion de resumen al canal interno (simulado)."""
    error = validate_params(args, _REQUIRED)
    if error:
        return error
    error = validate_enum(args, "nivel_urgencia", _NIVELES)
    if error:
        return error

    result = db.create_slack_message(
        canal=args["canal"],
        resumen_ejecutivo=args["resumen_ejecutivo"],
        acciones_realizadas=args.get("acciones_realizadas", []),
        nivel_urgencia=args["nivel_urgencia"],
        alertas=args.get("alertas", []),
    )
    return {
        "ok": True,
        "message": f"Notificacion enviada a Slack ({args['canal']})",
        **result,
    }