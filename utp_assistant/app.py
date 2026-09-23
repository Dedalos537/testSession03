"""UI Streamlit de "UTP Assistant": red interna simulada de 2 usuarios.

Pestañas:
- Bandeja: correos simulados, procesar pendientes y simular correo entrante.
- Chat del thread: conversacion con el asistente por cliente/thread.
- Resultados: sistemas simulados (Jira, CRM, Calendar, Slack).
"""

from __future__ import annotations

import traceback
from typing import Any

import streamlit as st

from utp_assistant import db, runner, theme
from utp_assistant.config import MODEL

st.set_page_config(page_title="UTP Assistant", layout="wide")


def _init() -> None:
    db.init_db()
    db.seed()
    st.session_state.setdefault("user", None)


def _usuarios() -> list[dict[str, Any]]:
    conn = db.get_connection()
    try:
        return [dict(r) for r in conn.execute(
            "SELECT id, nombre, email, pass_hash, rol FROM users ORDER BY id"
        ).fetchall()]
    finally:
        conn.close()


def _login() -> None:
    if st.session_state["user"]:
        return
    st.markdown(theme.login_apertura(), unsafe_allow_html=True)
    opciones = {u["nombre"]: u for u in _usuarios()}
    nombre = st.selectbox("Usuario", list(opciones))
    clave = st.text_input("Contraseña", type="password")
    if st.button("Ingresar", type="primary", use_container_width=True):
        user = opciones.get(nombre)
        if user and db.verify_password(clave, user["pass_hash"]):
            st.session_state["user"] = user
            st.rerun()
        else:
            st.error("Contraseña incorrecta (prototipo: use 'demo123').")
    st.markdown(theme.login_cierre(), unsafe_allow_html=True)
    st.stop()


def _listado_emails() -> list[dict[str, Any]]:
    from utp_assistant.inbox import list_emails

    return list_emails()


def _get_client() -> Any:
    try:
        return runner.make_client()
    except RuntimeError as exc:
        st.error(str(exc))
        st.info("Crea el archivo .env y agrega GROQ_API_KEY. Ver README.md.")
        st.stop()


def _logout() -> None:
    if st.button("Cerrar sesión", type="secondary", use_container_width=True):
        st.session_state["user"] = None
        st.rerun()


def pestana_bandeja() -> None:
    emails = _listado_emails()
    pendientes = [e for e in emails if not e["procesado"]]
    procesados = len(emails) - len(pendientes)
    _aviso_correo_enviado()
    st.markdown(
        theme.metrics_row(
            [
                ("Correos pendientes", len(pendientes), "ti-inbox"),
                ("Correos procesados", procesados, "ti-checks"),
                ("Tareas Jira", len(db.list_jira_tasks()), "ti-bug"),
                ("Contactos CRM", len(db.list_crm_contacts()), "ti-address-book"),
            ]
        ),
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns([2, 1])
    with c1:
        if st.button("Procesar correos pendientes", type="primary"):
            client = _get_client()
            if not pendientes:
                st.info("No hay correos pendientes.")
            with st.status("Ejecutando Run(s)...", expanded=True) as status:
                for email in pendientes:
                    try:
                        res = runner.process_email(
                            email,
                            client=client,
                            usuario=st.session_state["user"]["email"],
                        )
                        if res.get("estado") == "error":
                            st.error(res.get("error", "Error al procesar el correo."))
                            continue
                        st.markdown(
                            theme.run_card(email["asunto"], res),
                            unsafe_allow_html=True,
                        )
                        with st.expander("Resumen completo en texto"):
                            st.code(res["resumen_final"] or "(sin resumen)", language="text")
                    except Exception:  # noqa: BLE001 - la UI debe absorber cualquier fallo del run
                        st.error(
                            f"Fallo procesando {email['asunto']}:\n{traceback.format_exc()}"
                        )
                status.update(label="Runs completados.", state="complete")
    with c2:
        st.markdown(
            f'<p class="text-muted mb-0" style="text-align:right">'
            f'<i class="ti ti-cpu me-1"></i>Modelo: <code>{MODEL}</code></p>',
            unsafe_allow_html=True,
        )

    st.markdown('<h3 class="h4 mb-3">Correos recibidos</h3>', unsafe_allow_html=True)
    if emails:
        for e in emails:
            st.markdown(theme.email_card(e), unsafe_allow_html=True)
    else:
        st.markdown(
            theme.empty_state(
                "ti-inbox",
                "Bandeja vacía",
                "Los correos simulados aparecerán aquí, incluida su cabecera, aunque no haya datos.",
            ),
            unsafe_allow_html=True,
        )

    st.divider()
    st.markdown(
        '<h3 class="h4 mb-3">Simular correo entrante (webhook)</h3>',
        unsafe_allow_html=True,
    )
    with st.form("nuevo_correo", clear_on_submit=True):
        rem = st.text_input("Remitente", value="Nombre <correo@empresa.com>")
        emp = st.text_input("Empresa", value="Cliente")
        asu = st.text_input("Asunto")
        cuer = st.text_area("Cuerpo")
        adj = st.text_input("Adjuntos (separador ,)", value="")
        if st.form_submit_button("Enviar correo", type="primary"):
            from utp_assistant.inbox import send_email

            adjs = [a.strip() for a in adj.split(",") if a.strip()]
            send_email(rem, asu, cuer, empresa=emp, adjuntos=adjs)
            st.session_state["ultimo_correo"] = asu or "(sin asunto)"
            st.rerun()


def _aviso_correo_enviado() -> None:
    ultimo = st.session_state.pop("ultimo_correo", None)
    if ultimo:
        st.success(f"Correo simulado ingresado y pendiente de procesamiento: {ultimo}.")


def pestana_chat() -> None:
    st.markdown(
        '<h3 class="h5 mb-3"><i class="ti ti-message-circle me-2 text-primary"></i>'
        "Chat del asistente por thread (cliente)</h3>",
        unsafe_allow_html=True,
    )
    from utp_assistant.inbox import list_emails

    emails = list_emails()
    if not emails:
        st.markdown(
            theme.empty_state(
                "ti-mail-off",
                "Sin correos aún",
                "Crea o procesa un correo para habilitar el chat de su thread.",
            ),
            unsafe_allow_html=True,
        )
        return

    opciones = {
        f"#{e['thread_id']} · {e['empresa']} ({e['cliente']})": e["thread_id"]
        for e in emails
    }
    seleccion = st.selectbox("Thread", list(opciones), index=0)
    thread_id = opciones[seleccion]

    historial = db.get_thread_messages(thread_id)
    for m in historial:
        papel = "assistant" if m["role"] == "assistant" else "user"
        with st.chat_message(papel):
            st.markdown(m["content"])

    texto = st.chat_input(
        "Escribe un mensaje al asistente (se añadirá al thread y se ejecutará un Run)"
    )
    if texto:
        with st.chat_message("user"):
            st.markdown(texto)
        db.add_message(thread_id, "user", texto)
        try:
            with st.spinner("Ejecutando Run..."):
                res = runner.run_assistant(
                    thread_id,
                    client=_get_client(),
                    usuario=st.session_state["user"]["email"],
                )
            if res.get("estado") == "error":
                st.error(res.get("error", "Error al ejecutar el Run."))
            else:
                with st.chat_message("assistant"):
                    st.markdown(res["resumen_final"])
        except Exception as exc:  # noqa: BLE001
            st.error(f"Error en el Run: {exc}")


def _detalle_auditoria(detalle: dict[str, Any]) -> str:
    for clave in ("message", "error", "info"):
        if detalle.get(clave):
            return str(detalle.get(clave))
    return "ok" if detalle.get("ok") else "rechazada"


def pestana_revision() -> None:
    st.markdown(
        '<h3 class="h5 mb-1"><i class="ti ti-shield-check me-2 text-primary"></i>'
        "Punto de control humano (Riesgo 1)</h3>",
        unsafe_allow_html=True,
    )
    st.caption(
        "Las propuestas tentativas (reuniones sin fecha/hora exacta confirmada) quedan "
        "pendientes de validacion: solo Gerencia puede confirmarlas (Riesgo 2 - RBAC)."
    )

    pendientes = [ev for ev in db.list_calendar_events() if ev.get("es_tentativa")]
    if pendientes:
        for ev in pendientes:
            c1, c2, c3, c4 = st.columns([3, 1, 2, 2])
            c1.markdown(
                f'<div class="fw-semibold">{theme._esc(ev["titulo"])}</div>'
                f'<div class="text-muted small">origen: {theme._esc(ev.get("origen") or "chat")}</div>',
                unsafe_allow_html=True,
            )
            c2.markdown(
                '<span class="badge badge-pendiente">tentativa</span>',
                unsafe_allow_html=True,
            )
            c3.markdown(
                f'<div class="text-muted small">'
                f'{ev.get("fecha_propuesta") or "sin fecha"} · {ev.get("hora_propuesta") or "sin hora"}'
                f"</div>",
                unsafe_allow_html=True,
            )
            usuario = st.session_state["user"]
            if usuario.get("rol") == "Gerencia":
                if c4.button("Confirmar", key=f"confirmar_{ev['id']}", use_container_width=True):
                    db.confirmar_evento(ev["id"], usuario=usuario["email"])
                    st.rerun()
            else:
                c4.markdown(
                    '<span class="text-muted small">Solo Gerencia (RBAC)</span>',
                    unsafe_allow_html=True,
                )
        st.divider()
    else:
        st.markdown(
            theme.empty_state(
                "ti-calendar-check",
                "Sin propuestas pendientes de validacion",
                "Los eventos tentativos creados por el asistente aparecerán aquí para su "
                "confirmación humana antes de comunicarlos al cliente.",
            ),
            unsafe_allow_html=True,
        )

    st.markdown(
        '<h3 class="h5 mt-4 mb-2"><i class="ti ti-shield-lock me-2 text-primary"></i>'
        "Log de auditoría (Riesgo 2)</h3>",
        unsafe_allow_html=True,
    )
    aud = db.list_auditoria(limit=50)
    st.markdown(
        theme.tabla_tabler(
            "Acciones registradas",
            "ti-shield-lock",
            ["Fecha", "Run", "Acción", "Estado", "Usuario", "Detalle"],
            [
                (
                    a["created_at"],
                    a.get("run_id") or "—",
                    a["accion"],
                    "ejecutada" if a["estado"] == "ejecutada" else a["estado"],
                    a.get("usuario") or "—",
                    _detalle_auditoria(a.get("detalle") or {}),
                )
                for a in aud
            ],
            "Aún no hay acciones registradas en el log de auditoría.",
        ),
        unsafe_allow_html=True,
    )


def pestana_resultados() -> None:
    jira = db.list_jira_tasks()
    crm = db.list_crm_contacts()
    cal = db.list_calendar_events()
    slack = db.list_slack_messages()
    st.markdown(
        theme.metrics_row(
            [
                ("Tareas Jira", len(jira), "ti-bug"),
                ("Contactos CRM", len(crm), "ti-address-book"),
                ("Eventos Calendar", len(cal), "ti-calendar"),
                ("Mensajes Slack", len(slack), "ti-message-circle"),
            ]
        ),
        unsafe_allow_html=True,
    )

    tab_jira, tab_crm, tab_cal, tab_slack, tab_rev = st.tabs(
        ["Jira", "CRM", "Calendar", "Slack", "Revisión humana"]
    )
    with tab_jira:
        st.markdown(
            theme.tabla_tabler(
                "Tareas de proyecto",
                "ti-bug",
                ["Clave", "Título", "Prioridad", "Cliente", "Fecha límite", "Origen"],
                [
                    (
                        j["key"],
                        j["titulo"],
                        j["prioridad"],
                        j["cliente_relacionado"],
                        j.get("fecha_limite") or "—",
                        j.get("origen") or "—",
                    )
                    for j in jira
                ],
                "Aún no hay tareas de Jira.",
            ),
            unsafe_allow_html=True,
        )
    with tab_crm:
        st.markdown(
            theme.tabla_tabler(
                "Contactos del CRM",
                "ti-address-book",
                ["Contacto", "Empresa", "Email", "Etapa del pipeline", "Interés", "Última interacción", "Origen"],
                [
                    (
                        c["nombre_contacto"],
                        c["empresa"],
                        c["correo_electronico"],
                        c["etapa_pipeline"],
                        c.get("interes_principal") or "—",
                        c["ultima_interaccion_resumen"],
                        c.get("origen") or "—",
                    )
                    for c in crm
                ],
                "Aún no hay contactos en el CRM.",
            ),
            unsafe_allow_html=True,
        )
    with tab_cal:
        st.markdown(
            theme.tabla_tabler(
                "Eventos de Calendar",
                "ti-calendar",
                ["Título", "Fecha propuesta", "Hora", "Duración", "Estado", "Asistentes"],
                [
                    (
                        ev["titulo"],
                        ev.get("fecha_propuesta") or "—",
                        ev.get("hora_propuesta") or "—",
                        f"{ev['duracion_minutos']} min" if ev.get("duracion_minutos") else "—",
                        "Tentativa" if ev.get("es_tentativa") else "Confirmado",
                        ", ".join(ev.get("asistentes") or []) or "—",
                    )
                    for ev in cal
                ],
                "Aún no hay eventos en Calendar.",
            ),
            unsafe_allow_html=True,
        )
    with tab_slack:
        st.markdown(
            theme.tabla_tabler(
                "Mensajes de Slack",
                "ti-message-circle",
                ["Canal", "Resumen ejecutivo", "Urgencia", "Acciones", "Alertas", "Origen"],
                [
                    (
                        m["canal"],
                        m["resumen_ejecutivo"],
                        m["nivel_urgencia"],
                        ", ".join(m.get("acciones_realizadas") or []) or "—",
                        ", ".join(m.get("alertas") or []) or "—",
                        m.get("origen") or "—",
                    )
                    for m in slack
                ],
                "Aún no hay mensajes de Slack.",
            ),
            unsafe_allow_html=True,
        )
    with tab_rev:
        pestana_revision()
    st.markdown(
        '<p class="text-muted small"><i class="ti ti-database me-1"></i>'
        "Los datos se leen de SQLite en cada render; las tablas muestran su cabecera "
        "aunque estén vacías.</p>",
        unsafe_allow_html=True,
    )


def main() -> None:
    _init()
    theme.assets()
    _login()
    user = st.session_state["user"]

    c_nav, c_out = st.columns([5, 1])
    with c_nav:
        st.markdown(theme.topbar(user, MODEL), unsafe_allow_html=True)
    with c_out:
        _logout()

    tab1, tab2, tab3 = st.tabs(["Bandeja", "Chat del thread", "Resultados"])
    with tab1:
        pestana_bandeja()
    with tab2:
        pestana_chat()
    with tab3:
        pestana_resultados()


if __name__ == "__main__":
    main()