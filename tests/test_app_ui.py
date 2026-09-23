from __future__ import annotations

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from utp_assistant import db

APP_PATH = str(Path(__file__).resolve().parent.parent / "utp_assistant" / "app.py")


@pytest.fixture
def at(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> AppTest:
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "ui.db")
    app = AppTest.from_file(APP_PATH, default_timeout=30)
    app.run()
    assert not app.exception
    return app


def _html(at: AppTest) -> str:
    return "\n".join(m.value for m in at.markdown)


def _login(at: AppTest) -> None:
    at.text_input[0].input("demo123")
    at.button[0].click()
    at.run()


def test_login_muestra_diseno_tabler(at: AppTest) -> None:
    html = _html(at)
    assert "app/static/tabler/tabler.min.css" in html
    assert "tabler-icons.min.css" in html
    assert "auth-card" in html
    assert "Ingreso a la red interna" in html


def test_login_invalido_muestra_error(at: AppTest) -> None:
    at.text_input[0].input("clave-incorrecta")
    at.button[0].click()
    at.run()
    assert not at.exception
    errores = [e.value for e in at.error]
    assert any("Contraseña incorrecta" in e for e in errores)


def test_login_ok_muestra_topbar_bandeja_y_metricas(at: AppTest) -> None:
    _login(at)
    assert not at.exception
    html = _html(at)
    assert "UTP Assistant" in html
    assert "Correos recibidos" in html
    assert "Correos pendientes" in html
    assert "Correos procesados" in html
    assert "modelo" in html.lower()
    assert "Procesar correos pendientes" in [b.label for b in at.button]


def test_resultados_renderizan_cabeceras_aunque_vacias(at: AppTest) -> None:
    _login(at)
    assert not at.exception
    etiquetas = {t.label for t in at.tabs}
    assert {"📥 Bandeja", "💬 Chat del thread", "📊 Resultados"} <= etiquetas
    resultados = next(t for t in at.tabs if t.label == "📊 Resultados")
    html = "\n".join(m.value for m in resultados.markdown)
    assert "<thead>" in html
    assert "<tbody>" in html
    assert "colspan" in html
    assert "0 registros" in html
    assert "Aún no hay tareas de Jira." in html
    assert "Aún no hay contactos en el CRM." in html
    assert "Aún no hay eventos en Calendar." in html
    assert "Aún no hay mensajes de Slack." in html


def test_seed_provee_correos_y_los_muestra_como_tarjetas(at: AppTest) -> None:
    _login(at)
    assert not at.exception
    html = _html(at)
    assert "asunto" in html.lower() or "techcorp" in html.lower()