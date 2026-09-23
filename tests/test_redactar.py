"""Tests del filtro de redaccion de datos sensibles (Riesgo 2 - DLP)."""

from utp_assistant.redactar import redactar


def test_enmascara_tarjeta_valid_luhn():
    assert redactar("mi tarjeta 4111 1111 1111 1111 vence 12/27") == (
        "mi tarjeta [NUMERO DE TARJETA] vence 12/27"
    )
    assert redactar("5555555555554444") == "[NUMERO DE TARJETA]"
    assert redactar("4111-1111-1111-1111") == "[NUMERO DE TARJETA]"


def test_no_enmascara_numero_invalido_luhn():
    assert redactar("1234567890123456") == "1234567890123456"


def test_enmascara_dni():
    assert redactar("DNI 98765432") == "DNI [DNI]"
    assert redactar("1234567") == "[DNI]"


def test_enmascara_cuit():
    assert redactar("CUIT 20304050607") == "CUIT [CUIT]"


def test_enmascara_telefono():
    assert redactar("+51 999 888 777") == "[TELEFONO]"
    assert redactar("llamar al 999888777") == "llamar al [TELEFONO]"
    assert redactar("51 999-888-777") == "[TELEFONO]"


def test_respeta_fechas_cortos_y_texto_normal():
    texto = "La fecha es 2026-09-22, monto 1500, id 12 y adjunto requisitos.pdf"
    assert redactar(texto) == texto


def test_vacio_y_none():
    assert redactar("") == ""
    assert redactar(None) == ""
    assert redactar("Solo texto sin datos sensibles.") == "Solo texto sin datos sensibles."