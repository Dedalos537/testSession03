"""Tests del runner: ciclo del Run con un cliente Groq falso (sin red)."""

import json

import pytest

from utp_assistant import db, inbox, runner


class ToolCall:
    def __init__(self, tid: str, name: str, arguments: dict):
        self.id = tid
        self.type = "function"
        self.function = type("F", (), {"name": name, "arguments": json.dumps(arguments)})()


class Choice:
    def __init__(self, msg):
        self.message = msg


class FakeCompletions:
    """Devuelve tool_calls en la 1.ª llamada y texto en las siguientes.

    Con ``tool_calls_first=False`` devuelve texto siempre (caso "sin accion").
    Con ``rate_limit_once=True`` falla la 1.ª llamada con HTTP 429 y reintenta.
    """

    def __init__(self, tool_calls_first=True, rate_limit_once=False, text_content=None):
        self.tool_calls_first = tool_calls_first
        self.rate_limit_once = rate_limit_once
        self.text_content = text_content or (
            "Resumen ejecutivo: TechCorp avanza.\n"
            "Acciones ejecutadas: ...\nPendientes: ninguno."
        )
        self._gave_tool_calls = False
        self.calls: list[dict] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.rate_limit_once and len(self.calls) == 1:
            exc = RuntimeError("rate limited")
            exc.status_code = 429
            raise exc
        if self.tool_calls_first and not self._gave_tool_calls:
            self._gave_tool_calls = True
            msg = type("M", (), {"content": None, "tool_calls": [
                ToolCall("call_3", "crear_tarea_en_jira", {
                    "proyecto_key": "PAGOS",
                    "titulo": "Revisar requisitos de TechCorp",
                    "descripcion": "Segun correo 2026-09-22",
                    "prioridad": "Alta",
                    "cliente_relacionado": "TechCorp",
                }),
                ToolCall("call_1", "actualizar_contacto_en_crm", {
                    "nombre_contacto": "Ana Torres",
                    "empresa": "TechCorp",
                    "correo_electronico": "ana.torres@techcorp.com",
                    "etapa_pipeline": "Negociacion",
                    "ultima_interaccion_resumen": "Avanzan con el modulo de pagos",
                }),
            ]})()
            return type("R", (), {"choices": [Choice(msg)]})()
        msg = type("M", (), {
            "content": self.text_content,
            "tool_calls": None,
        })()
        return type("R", (), {"choices": [Choice(msg)]})()


class FakeClient:
    def __init__(self, **kwargs):
        self.chat = type("C", (), {"completions": FakeCompletions(**kwargs)})()


@pytest.fixture
def dbfile(tmp_path, monkeypatch):
    path = tmp_path / "test.db"
    monkeypatch.setattr(db, "DB_PATH", path)
    db.seed(db_path=path)
    return path


def _primer_pendiente():
    return next(e for e in db.get_pending_emails() if "Ana Torres" in e["remitente"])


def test_runner_ejecuta_tool_calls_en_orden(dbfile):
    client = FakeClient()
    email = _primer_pendiente()
    res = runner.process_email(email, client=client)

    assert res["estado"] == "completed"
    ejecutados = [tc["name"] for tc in res["tool_calls"]]
    # pese a que el modelo respondio Jira antes que CRM, se reordena segun ORDER
    assert ejecutados == [
        "actualizar_contacto_en_crm",
        "crear_tarea_en_jira",
    ]
    assert "PAGOS-1" in json.dumps(res["tool_calls"])


def test_runner_guarda_resultados_y_marca_procesado(dbfile):
    client = FakeClient()
    email = _primer_pendiente()
    res = runner.process_email(email, client=client)

    assert len(db.list_jira_tasks()) == 1
    assert len(db.list_crm_contacts()) == 1
    email_db = next(e for e in db.list_emails() if e["id"] == email["id"])
    assert email_db["procesado"] == 1
    assert email_db["run_id"] == res["run_id"]
    # mensaje de historial: user (email) + assistant (resumen)
    assert len(db.get_thread_messages(email["thread_id"])) == 2


def test_runner_idempotente_por_email(dbfile):
    client = FakeClient()
    email = _primer_pendiente()
    runner.process_email(email, client=client)
    # al reprocesar el mismo correo ya procesado (simular re-run manual), no debe duplicar
    # el mensaje del correo en el thread
    runner.run_assistant(email["thread_id"], client=client)
    mensajes = [m["content"] for m in db.get_thread_messages(email["thread_id"])]
    correos = [c for c in mensajes if f"[EMAIL ID: {email['id']}]" in c]
    assert len(correos) == 1


def test_runner_sin_accion_no_invoca_tools(dbfile):
    client = FakeClient(
        tool_calls_first=False,
        text_content="Sin accion requerida: correo de agradecimiento, ni reunion ni tarea.",
    )
    eid = inbox.send_email(
        "Pedro Diaz <pedro@ejemplo.com>",
        "Gracias por la visita",
        "Fue un gusto, por ahora sin acciones nuevas.",
        empresa="Ejemplo SAC",
    )
    mail = next(e for e in db.list_emails() if e["id"] == eid)
    res = runner.process_email(mail, client=client)
    assert res["tool_calls"] == []
    assert "sin accion" in res["resumen_final"].lower()


def test_runner_reintenta_error_429(dbfile):
    client = FakeClient(rate_limit_once=True)
    email = _primer_pendiente()
    res = runner.process_email(email, client=client)
    assert res["estado"] == "completed"
    # primera llamada (429) + segunda (tool_calls) + tercera (resumen)
    assert len(client.chat.completions.calls) == 3


# --------------------------------------------------------------------------- #
# Guardarrailes: Riesgo 1 (alucinaciones) y Riesgo 2 (seguridad/privacidad)
# --------------------------------------------------------------------------- #

def test_runner_redacta_datos_sensibles_antes_del_modelo(dbfile):
    """Riesgo 2: el numero de tarjeta no viaja al modelo; la bandeja lo conserva."""
    eid = inbox.send_email(
        "Luis Perez <luis@corp.com>",
        "Adjunto datos de pago",
        "Hola, mi tarjeta es 4111 1111 1111 1111, DNI 98765432, tel 999888777.",
        empresa="Corp SAC",
    )
    mail = next(e for e in db.list_emails() if e["id"] == eid)
    client = FakeClient(tool_calls_first=False, text_content="Sin accion requerida.")
    runner.process_email(mail, client=client)

    payload = "".join(
        m.get("content") or ""
        for msgs in (c.get("messages", []) for c in client.chat.completions.calls)
        for m in msgs
        if m["role"] == "user"
    )
    assert "4111 1111 1111 1111" not in payload
    assert "98765432" not in payload
    assert "999888777" not in payload
    assert "[NUMERO DE TARJETA]" in payload

    original = next(e for e in db.list_emails() if e["id"] == eid)
    assert "4111 1111 1111 1111" in original["cuerpo"]


def test_historial_limitado_al_modelo(dbfile):
    """Riesgo 2 (minimizacion): solo las ultimas N=20 mensajes + el system prompt."""
    email = _primer_pendiente()
    t = email["thread_id"]
    for i in range(25):
        db.add_message(t, "user", f"mensaje historico #{i}")
    messages = runner._build_messages(t)
    assert len(messages) == runner.MAX_HISTORY_MESSAGES + 1  # + system
    contenido = " ".join(m["content"] for m in messages)
    assert "mensaje historico #24" in contenido
    assert "mensaje historico #0" not in contenido


def test_registros_traen_origen_y_auditoria(dbfile):
    """Riesgo 1 (trazabilidad): cada registro cita su origen; cada accion queda auditada."""
    client = FakeClient()
    email = _primer_pendiente()
    res = runner.process_email(email, client=client)

    tarea = db.list_jira_tasks()[0]
    assert tarea["run_id"] == res["run_id"]
    assert tarea["origen"].startswith(f"EMAIL {email['id']}")
    contacto = db.list_crm_contacts()[0]
    assert contacto["origen"].startswith("EMAIL ")

    auditoria = db.list_auditoria()
    acciones = [a for a in auditoria if a["accion"] in ("actualizar_contacto_en_crm", "crear_tarea_en_jira")]
    assert len(acciones) == 2
    assert {a["estado"] for a in acciones} == {"ejecutada"}
    assert all(a["run_id"] == res["run_id"] for a in acciones)


def test_resumen_determinista_legible_sin_json(dbfile):
    """El resumen de respaldo no vuelca JSON crudo ni duplica series de dicts."""
    resumen = runner.resumen_determinista([
        {
            "name": "crear_tarea_en_jira",
            "output": {"ok": True, "message": "Tarea PAGOS-1 creada en Jira", "key": "PAGOS-1"},
        },
        {
            "name": "agendar_reunion_en_google_calendar",
            "output": {
                "ok": True,
                "es_tentativa": True,
                "message": "Evento tentativo creado (pendiente de confirmacion)",
            },
        },
        {"name": "enviar_notificacion_interna", "output": {"ok": False, "error": "faltan parametros"}},
    ])
    assert "-> {" not in resumen
    assert "{'ok'" not in resumen
    assert "Pendientes y alertas" in resumen
    assert "NO ejecutada" in resumen
    assert "pendiente de confirmacion humana" in resumen