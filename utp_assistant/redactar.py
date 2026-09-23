"""Filtro de redaccion de datos altamente sensibles (Riesgo 2 - DLP).

Se aplica ANTES de que la informacion llegue al modelo de Groq y a los
mensajes del historial: enmascara numeros de tarjeta (con chequeo Luhn para
no romper IDs o numeros legitimos), CUIT, DNI y telefonos.

Registros originales (tabla ``emails``) se conservan como fuente de verdad
del equipo; lo que viaja al modelo ya esta redactado.
"""

from __future__ import annotations

import re
from re import Match

_NUMERO_TARJETA = "[NUMERO DE TARJETA]"
_TELEFONO = "[TELEFONO]"
_DNI = "[DNI]"
_CUIT = "[CUIT]"

_CARD_RE = re.compile(r"(?<!\d)(?:\d(?:[ -](?=\d))?){13,19}(?!\d)")
_DNI_RE = re.compile(r"(?<!\d)\d{7,8}(?!\d)")
_CUIT_RE = re.compile(r"(?<!\d)\d{11}(?!\d)")
_PHONE_RE = re.compile(r"(?<!\d)(?:\+?51[\s-](?=\d))?(?:\d(?:[\s-](?=\d))?){9}(?!\d)")


def _luhn_valido(numero: str) -> bool:
    """Chequeo Luhn sobre la secuencia de digitos (evita enmascarar numeros no-tarjeta)."""
    digitos = [int(c) for c in numero if c.isdigit()]
    if not digitos:
        return False
    suma = 0
    for i, d in enumerate(reversed(digitos)):
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        suma += d
    return suma % 10 == 0


def _reemplazar_tarjeta(match: Match[str]) -> str:
    if _luhn_valido(match.group(0)):
        return _NUMERO_TARJETA
    return match.group(0)


def redactar(texto: str | None) -> str:
    """Enmascara datos sensibles de un texto. Devuelve None como string vacio."""
    if not texto:
        return ""
    texto = _CARD_RE.sub(_reemplazar_tarjeta, texto)
    texto = _CUIT_RE.sub(_CUIT, texto)
    texto = _DNI_RE.sub(_DNI, texto)
    texto = _PHONE_RE.sub(_TELEFONO, texto)
    return texto