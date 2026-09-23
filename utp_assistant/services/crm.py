"""SIM_CRM: simulacion local del CRM (hubspot-like) para contactos/prospectos."""

from __future__ import annotations

from typing import Any

from .. import db
from . import validate_enum, validate_params

_REQUIRED = [
    "nombre_contacto",
    "empresa",
    "correo_electronico",
    "etapa_pipeline",
    "ultima_interaccion_resumen",
]
_ETAPAS = [
    "Prospecto",
    "Interesado",
    "Propuesta enviada",
    "Negociacion",
    "Cerrado-ganado",
    "Cerrado-perdido",
]


def upsert_contact(args: dict[str, Any]) -> dict[str, Any]:
    """Crea o actualiza un contacto en el CRM (simulado). Upsert por correo."""
    error = validate_params(args, _REQUIRED)
    if error:
        return error
    error = validate_enum(args, "etapa_pipeline", _ETAPAS)
    if error:
        return error

    result = db.upsert_crm_contact(
        nombre_contacto=args["nombre_contacto"],
        empresa=args["empresa"],
        correo_electronico=args["correo_electronico"],
        etapa_pipeline=args["etapa_pipeline"],
        ultima_interaccion_resumen=args["ultima_interaccion_resumen"],
        interes_principal=args.get("interes_principal"),
        documentos_adjuntos=args.get("documentos_adjuntos", []),
    )
    return {
        "ok": True,
        "message": (
            f"Contacto {args['correo_electronico']} actualizado en CRM"
            if result["accion"] == "actualizado"
            else f"Contacto {args['correo_electronico']} creado en CRM"
        ),
        **result,
    }