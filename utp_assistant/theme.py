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
        f'<link rel="stylesheet" href="{_STATIC_PREFIX}/utp-app.css" />',
        unsafe_allow_html=True,
    )


def badge(texto: str, clase: str) -> str:
    return f'<span class="badge {clase}">{_esc(texto)}</span>'


def topbar(user: dict[str, Any], modelo: str) -> str:
    nombre = _esc(user["nombre"])
    email = _esc(user["email"])
    rol = _esc(user.get("rol") or "Equipo")
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
        + badge(rol, "badge-modelo")
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


def run_card(asunto: str, res: dict[str, Any]) -> str:
    """Tarjeta legible de un Run: lista las acciones ejecutadas con su resultado,
    sin volver a volcar JSON crudo (el resumen completo queda en un expander)."""
    run_id = _esc(res.get("run_id") or "")
    items: list[str] = []
    for tc in res.get("tool_calls") or []:
        out = tc.get("output") or {}
        nombre = _esc(tc.get("name") or "")
        ok = bool(out.get("ok"))
        detalle = out.get("message") or out.get("error") or out.get("info") or "OK"
        icono = "ti-check text-success" if ok else "ti-alert-triangle text-danger"
        sello = badge("OK", "badge-procesado") if ok else badge("NO ejecutada", "badge-pendiente")
        items.append(
            '<div class="list-group-item d-flex align-items-start gap-2">'
            f'<i class="ti {icono} mt-1"></i>'
            "<div>"
            f'<div class="fw-semibold">{nombre} {sello}</div>'
            f'<div class="text-muted small">{_esc(detalle)}</div>'
            "</div></div>"
        )
    cuerpo = "".join(items) if items else (
        '<div class="text-muted small">Sin acciones ejecutadas (sin accion requerida).</div>'
    )
    return (
        '<div class="card mt-2">'
        f'<div class="card-header d-flex align-items-center justify-content-between">'
        f'<h3 class="card-title my-0"><i class="ti ti-send me-2 text-primary"></i>{_esc(asunto)}</h3>'
        f'<span class="badge badge-modelo">run {run_id}</span>'
        "</div>"
        f'<div class="list-group list-group-flush">{cuerpo}</div>'
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