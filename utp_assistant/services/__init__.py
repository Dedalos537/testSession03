"""Servicios que simulan las APIs externas de UTP Consultant.

Cada modulo implementa el "contrato" definido en ``tools.py``: recibe los
argumentos que produce el modelo, valida parametros obligatorios y valores
enum, escribe en SQLite y devuelve un dict JSON serializable.
"""

from __future__ import annotations

from typing import Any


def validate_params(args: dict[str, Any], required: list[str]) -> dict[str, Any] | None:
    """Devuelve dict de error si falta algun parametro obligatorio, sino None."""
    missing = [k for k in required if args.get(k) in (None, "", [], {})]
    if missing:
        return {
            "ok": False,
            "error": f"faltan parametros obligatorios: {', '.join(missing)}",
        }
    return None


def validate_enum(args: dict[str, Any], field: str, values: list[str]) -> dict[str, Any] | None:
    value = args.get(field)
    if value is not None and value not in values:
        return {
            "ok": False,
            "error": f"valor invalido para '{field}': {value!r}. Permitidos: {values}",
        }
    return None