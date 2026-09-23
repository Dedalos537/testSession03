"""Tests de componentes de UI (renderizado legible, sin dumps JSON crudos)."""

from utp_assistant.theme import run_card, tabla_tabler


def test_run_card_no_vuelca_json_crudo():
    res = {
        "run_id": "run_abc123",
        "tool_calls": [
            {
                "name": "crear_tarea_en_jira",
                "output": {"ok": True, "message": "Tarea PAGOS-1 creada en Jira", "key": "PAGOS-1"},
            },
            {
                "name": "enviar_notificacion_interna",
                "output": {"ok": False, "error": "faltan parametros obligatorios"},
            },
        ],
    }
    html = run_card("Re: Propuesta modulo de pagos", res)
    assert "run_abc123" in html
    assert "Tarea PAGOS-1 creada en Jira" in html
    assert "NO ejecutada" in html
    assert "faltan parametros obligatorios" in html
    assert "{'ok'" not in html
    assert "-> {" not in html


def test_run_card_sin_acciones():
    html = run_card("Gracias", {"run_id": "run_x", "tool_calls": []})
    assert "Sin acciones ejecutadas" in html


def test_tabla_tabler_vacia_con_cabeceras():
    html = tabla_tabler("T", "ti-bug", ["A", "B"], [], "Aún no hay datos.")
    assert "<thead>" in html and "<th>A</th>" in html
    assert "colspan" in html
    assert "0 registros" in html