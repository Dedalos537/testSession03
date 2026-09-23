"""Tests de los servicios que simulan las APIs externas (Jira/CRM/Calendar/Slack)."""

import pytest

from utp_assistant import db
from utp_assistant.services import calendar, crm, jira, slack


@pytest.fixture
def dbfile(tmp_path, monkeypatch):
    path = tmp_path / "test.db"
    monkeypatch.setattr(db, "DB_PATH", path)
    db.seed(db_path=path)
    return path


def test_jira_crea_tarea_con_key(dbfile):
    out = jira.create_task({
        "proyecto_key": "PAGOS",
        "titulo": "Revisar requisitos iniciales",
        "descripcion": "Contexto extraido del correo.",
        "prioridad": "Alta",
        "cliente_relacionado": "TechCorp",
    })
    assert out["ok"] is True
    assert out["key"] == "PAGOS-1"
    assert "creada en Jira" in out["message"]


def test_jira_falta_obligatorio(dbfile):
    out = jira.create_task({"proyecto_key": "PAGOS"})
    assert out["ok"] is False
    assert "titulo" in out["error"]


def test_jira_prioridad_invalida(dbfile):
    out = jira.create_task({
        "proyecto_key": "PAGOS",
        "titulo": "t",
        "descripcion": "d",
        "prioridad": "Extrema",
        "cliente_relacionado": "X",
    })
    assert out["ok"] is False
    assert "prioridad" in out["error"]


def test_crm_upsert_idempotente(dbfile):
    base = {
        "nombre_contacto": "Ana Torres",
        "empresa": "TechCorp",
        "correo_electronico": "ana.torres@techcorp.com",
        "etapa_pipeline": "Negociacion",
        "ultima_interaccion_resumen": "Primer correo",
    }
    first = crm.upsert_contact(base)
    base["etapa_pipeline"] = "Propuesta enviada"
    second = crm.upsert_contact(base)

    assert first["ok"] and first["accion"] == "creado"
    assert second["ok"] and second["accion"] == "actualizado"
    assert first["id"] == second["id"]
    assert len(db.list_crm_contacts()) == 1


def test_crm_etapa_invalida(dbfile):
    out = crm.upsert_contact({
        "nombre_contacto": "A",
        "empresa": "B",
        "correo_electronico": "a@b.com",
        "etapa_pipeline": "Inexistente",
        "ultima_interaccion_resumen": "r",
    })
    assert out["ok"] is False
    assert "etapa_pipeline" in out["error"]


def test_calendar_evento_tentativo_por_defecto(dbfile):
    out = calendar.create_event({
        "titulo": "Reunion - TechCorp",
        "asistentes": ["ana.torres@techcorp.com"],
        "agenda": "Detalles modulo de pagos",
        "es_tentativa": True,
    })
    assert out["ok"] is True
    assert out["es_tentativa"] is True
    event = db.list_calendar_events()[0]
    assert event["duracion_minutos"] == 30


def test_calendar_falta_obligatorio(dbfile):
    out = calendar.create_event({"titulo": "t", "asistentes": [], "es_tentativa": False})
    assert out["ok"] is False
    assert "agenda" in out["error"]


def test_slack_notificacion(dbfile):
    out = slack.send_notification({
        "canal": "#ventasseguimiento",
        "resumen_ejecutivo": "Resumen de 2 lineas",
        "acciones_realizadas": ["Tarea PAGOS-1 creada"],
        "nivel_urgencia": "Normal",
        "alertas": ["Fecha de reunion tentativa"],
    })
    assert out["ok"] is True
    msg = db.list_slack_messages()[0]
    assert msg["canal"] == "#ventasseguimiento"
    assert "Fecha de reunion tentativa" in msg["alertas"]


def test_slack_faltan_acciones(dbfile):
    out = slack.send_notification({
        "canal": "#v",
        "resumen_ejecutivo": "r",
        "acciones_realizadas": [],
        "nivel_urgencia": "Normal",
    })
    assert out["ok"] is False
    assert "acciones_realizadas" in out["error"]


def test_tools_schemas_completos():
    from utp_assistant.tools import ORDER, TOOLS

    nombres = [t["function"]["name"] for t in TOOLS]
    assert nombres == ORDER
    assert len(nombres) == 4
    for tool in TOOLS:
        fn = tool["function"]
        assert fn["name"]
        assert fn["description"]
        assert fn["parameters"]["type"] == "object"