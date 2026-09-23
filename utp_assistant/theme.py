from __future__ import annotations

import html
from collections.abc import Sequence
from typing import Any

import streamlit as st

_STATIC_PREFIX = "/app/static/tabler"


def _esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def assets() -> None:
    st.markdown(
        f'<link rel="stylesheet" href="{_STATIC_PREFIX}/tabler.min.css" />\n'
        f'<link rel="stylesheet" href="{_STATIC_PREFIX}/tabler-icons.min.css" />\n'
        f"<style>{_OVERRIDES}</style>",
        unsafe_allow_html=True,
    )


def badge(texto: str, clase: str) -> str:
    return f'<span class="badge {clase}">{_esc(texto)}</span>'


def topbar(user: dict[str, Any], modelo: str) -> str:
    nombre = _esc(user["nombre"])
    email = _esc(user["email"])
    return (
        '<div class="topbar">'
        '<div class="topbar-brand">'
        '<span class="avatar avatar-brand"><i class="ti ti-mail"></i></span>'
        '<span>UTP Assistant</span>'
        '<span class="d-none d-md-inline text-muted fw-normal small">'
        "Asistente IA para correos de clientes"
        "</span>"
        "</div>"
        '<div class="topbar-meta">'
        + badge(f"Modelo: {modelo}", "badge-modelo")
        + '<span class="avatar avatar-user"><i class="ti ti-user"></i></span>'
        + f"{nombre}"
        + f'<span class="d-none d-sm-inline text-muted small">{email}</span>'
        + "</div></div>"
    )


def metric_card(etiqueta: str, valor: Any, icono: str) -> str:
    return (
        '<div class="metric-card">'
        f'<span class="metric-icon"><i class="ti {icono}"></i></span>'
        "<div>"
        f'<div class="metric-value">{_esc(valor)}</div>'
        f'<div class="metric-label">{_esc(etiqueta)}</div>'
        "</div></div>"
    )


def metrics_row(items: Sequence[tuple[str, Any, str]]) -> str:
    cards = "".join(metric_card(etiqueta, valor, icono) for etiqueta, valor, icono in items)
    return f'<div class="metrics-row">{cards}</div>'


def tabla_tabler(
    titulo: str,
    icono: str,
    columnas: Sequence[str],
    filas: Sequence[Sequence[Any]],
    vacio: str = "Sin registros. Los datos aparecerán aquí cuando el asistente ingrese información.",
) -> str:
    th = "".join(f"<th>{_esc(c)}</th>" for c in columnas)
    if filas:
        cuerpo = "".join(
            "<tr>" + "".join(f"<td>{_esc(c)}</td>" for c in fila) + "</tr>"
            for fila in filas
        )
    else:
        cuerpo = (
            f'<tr><td colspan="{len(columnas)}">'
            f'<div class="empty"><i class="ti ti-database-off d-block mb-2"></i>'
            f"{_esc(vacio)}</div></td></tr>"
        )
    return (
        '<div class="card">'
        '<div class="card-header d-flex align-items-center justify-content-between">'
        f'<h3 class="card-title my-0"><i class="ti {icono} me-2 text-primary"></i>{_esc(titulo)}</h3>'
        f'<span class="badge badge-outline text-primary">{len(filas)} registros</span>'
        "</div>"
        '<div class="table-responsive">'
        f"<table class=\"table table-vcenter card-table\"><thead>{th}</thead><tbody>{cuerpo}</tbody></table>"
        "</div></div>"
    )


def email_card(e: dict[str, Any]) -> str:
    adjuntos = ", ".join(e.get("adjuntos") or []) or "sin adjuntos"
    estado = (
        badge("Procesado", "badge-procesado")
        if e.get("procesado")
        else badge("Pendiente", "badge-pendiente")
    )
    run = (
        f'<span class="text-muted"> · run {_esc(e["run_id"])}</span>'
        if e.get("run_id")
        else ""
    )
    return (
        '<div class="card">'
        '<div class="card-body">'
        '<div class="d-flex justify-content-between align-items-start gap-3">'
        "<div>"
        f'<div class="fw-semibold">{_esc(e["asunto"])}</div>'
        f'<div class="text-muted small">'
        f'{_esc(e["fecha"])} · {_esc(e.get("empresa") or "")} · de {_esc(e["remitente"])}'
        "</div></div>"
        f"{estado}"
        "</div>"
        f'<p class="mb-0 mt-2">{_esc(e["cuerpo"])}</p>'
        f'<div class="text-muted small mt-2"><i class="ti ti-paperclip me-1"></i>{_esc(adjuntos)}{run}</div>'
        "</div></div>"
    )


def empty_state(icono: str, titulo: str, detalle: str) -> str:
    return (
        '<div class="empty card">'
        f'<i class="ti {icono} d-block mb-2"></i>'
        f'<p class="fw-semibold mb-1">{_esc(titulo)}</p>'
        f'<p class="text-muted mb-0">{_esc(detalle)}</p>'
        "</div>"
    )


def login_apertura() -> str:
    return (
        '<div class="auth-card card">'
        '<div class="card-body p-4">'
        '<div class="auth-head">'
        '<span class="avatar avatar-brand mb-3"><i class="ti ti-mail"></i></span>'
        '<h2 class="h3 mb-1">UTP Assistant</h2>'
        '<p class="text-muted mb-0">Ingreso a la red interna (2 usuarios)</p>'
        "</div>"
    )


def login_cierre() -> str:
    return "</div></div>"


_OVERRIDES = """
header[data-testid="stHeader"] { display: none; }

[data-testid="stAppViewContainer"] {
  font-family: var(--tblr-font-sans-serif);
  background: #f6f8fb;
  color: #1f2937;
}

.block-container { padding-top: 1rem; }

.metrics-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.metric-card {
  display: flex;
  align-items: center;
  gap: 1rem;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 1rem 1.25rem;
}

.metric-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2.75rem;
  height: 2.75rem;
  border-radius: 6px;
  background: rgba(6, 111, 209, 0.08);
  color: var(--tblr-primary, #066fd1);
  font-size: 1.25rem;
}

.metric-value { font-size: 1.5rem; font-weight: 700; line-height: 1.1; }
.metric-label { color: #667382; font-size: 0.85rem; }

.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
  padding: 0.75rem 1rem;
  margin-bottom: 1.25rem;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
}

.topbar-brand { display: flex; align-items: center; gap: 0.65rem; font-weight: 600; }
.topbar-meta { display: flex; align-items: center; gap: 0.75rem; color: #667382; font-size: 0.9rem; }

.avatar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: #fff;
  border: 1px solid #e5e7eb;
  color: #667382;
}
.avatar-brand { width: 2rem; height: 2rem; color: #fff; background: var(--tblr-primary, #066fd1); }
.avatar-user { width: 1.75rem; height: 1.75rem; }

.badge { font-weight: 600; }
.badge-pendiente { background: rgba(245, 158, 11, 0.12); color: #b45309; }
.badge-procesado { background: rgba(16, 185, 129, 0.12); color: #047857; }
.badge-modelo { background: rgba(6, 111, 209, 0.08); color: #066fd1; }

.card {
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  box-shadow: 0 1px 2px rgba(17, 23, 39, 0.05);
  margin-bottom: 1.25rem;
}

.table th {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  color: #667382;
  font-weight: 600;
}
.table td { padding: 0.65rem 0.75rem; }

.empty { text-align: center; padding: 2.5rem 1rem; color: #667382; }
.empty i { font-size: 2rem; }

.stButton > button,
.stFormSubmitButton > button {
  border-radius: 6px;
  font-weight: 600;
}
.stButton > button[kind="secondary"],
.stFormSubmitButton > button[kind="secondary"] { border: 1px solid #e5e7eb; }

div[data-baseweb="input"] input,
div[data-baseweb="textarea"] textarea,
div[data-baseweb="select"] > div {
  border-radius: 6px;
  border-color: #e5e7eb;
}

[data-testid="stChatMessage"] {
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  background: #ffffff;
}
[data-testid="stChatInput"] textarea { border-radius: 6px; }

[data-testid="stTabs"] button[aria-selected="true"] {
  color: var(--tblr-primary, #066fd1);
  border-bottom-color: var(--tblr-primary, #066fd1);
}

.auth-card { max-width: 460px; margin: 3rem auto 0; }
.auth-card .card-body { display: block; }
.auth-head { text-align: center; margin-bottom: 1.25rem; }
.auth-head .avatar-brand { width: 3rem; height: 3rem; font-size: 1.5rem; }
"""