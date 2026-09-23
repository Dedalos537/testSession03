"""UI Streamlit de "UTP Assistant": red interna simulada de 2 usuarios.

Pestanas:
- Bandeja: correos simulados, procesar pendientes y simular correo entrante.
- Chat del thread: conversacion con el asistente por cliente/thread.
- Resultados: sistemas simulados (Jira, CRM, Calendar, Slack).
"""

from __future__ import annotations

import traceback
from typing import Any

import streamlit as st

from utp_assistant import db, runner
from utp_assistant.config import MODEL

st.set_page_config(page_title="UTP Assistant", page_icon="✉️", layout="wide")


def _init() -> None:
    db.init_db()
    db.seed()
    st.session_state.setdefault("user", None)
    st.session_state.setdefault("thread_seleccionado", None)


def _usuarios() -> list[dict[str, Any]]:
    conn = db.get_connection()
    try:
        return [dict(r) for r in conn.execute(
            "SELECT id, nombre, email, pass_hash FROM users ORDER BY id"
        ).fetchall()]
    finally:
        conn.close()


def _login() -> None:
    if st.session_state["user"]:
        return
    with st.container(border=True):
        st.subheader("Ingreso a la red interna (2 usuarios)")
        col1, col2 = st.columns(2)
        with col1:
            nombre = st.selectbox(
                "Usuario",
                [u["nombre"] for u in _usuarios()],
                index=0,
            )
        with col2:
            clave = st.text_input("Contrasena", type="password")
        if st.button("Ingresar", type="primary"):
            user = next(u for u in _usuarios() if u["nombre"] == nombre)
            if db.verify_password(clave, user["pass_hash"]):
                st.session_state["user"] = user
                st.rerun()
            else:
                st.error("Contrasena incorrecta. (Prototipo: use 'demo123')")
    st.stop()


@st.cache_data(show_spinner=False)
def _listado_emails() -> list[dict[str, Any]]:
    from utp_assistant.inbox import list_emails

    return list_emails()


def _resultados() -> dict[str, list[dict[str, Any]]]:
    return {
        "jira": db.list_jira_tasks(),
        "crm": db.list_crm_contacts(),
        "calendar": db.list_calendar_events(),
        "slack": db.list_slack_messages(),
    }


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


def pestana_bandeja() -> None:
    st.subheader("Bandeja de entrada simulada")
    c1, c2 = st.columns([2, 1])
    with c1:
        if st.button("Procesar correos pendientes", type="primary"):
            client = _get_client()
            pendientes = [e for e in _listado_emails() if not e["procesado"]]
            if not pendientes:
                st.info("No hay correos pendientes.")
            with st.status("Ejecutando Run(s)...", expanded=True) as status:
                for email in pendientes:
                    try:
                        res = runner.process_email(email, client=client)
                        st.write(f"**{email['asunto']}** (run {res['run_id']})")
                        st.code(res["resumen_final"] or "(sin resumen)", language="text")
                        if res["tool_calls"]:
                            for tc in res["tool_calls"]:
                                st.caption(f"- {tc['name']} -> {tc['output']}")
                    except Exception:  # noqa: BLE001 - UI maneja cualquier fallo del run
                        st.error(f"Fallo procesando {email['asunto']}:\n{traceback.format_exc()}")
                status.update(label="Runs completados.", state="complete")
    with c2:
        st.markdown(f"**Modelo Groq:** `{MODEL}`")

    for e in _listado_emails():
        estado = "✅ procesado" if e["procesado"] else "⏳ pendiente"
        with st.expander(f"{e['fecha']} — {e['empresa']} | {e['asunto']} ({estado})"):
            st.markdown(f"**De:** {e['remitente']}")
            st.markdown(f"**Adjuntos:** {', '.join(e['adjuntos']) or 'ninguno'}")
            st.markdown(e["cuerpo"])
            if e["run_id"]:
                st.caption(f"run_id: {e['run_id']}")

    st.divider()
    st.subheader("Simular correo entrante (webhook)")
    with st.form("nuevo_correo", clear_on_submit=True):
        rem = st.text_input("Remitente", value="Nombre <correo@empresa.com>")
        emp = st.text_input("Empresa", value="Cliente")
        asu = st.text_input("Asunto")
        cuer = st.text_area("Cuerpo")
        adj = st.text_input("Adjuntos (separador ,)", value="")
        if st.form_submit_button("Enviar correo"):
            from utp_assistant.inbox import send_email

            adjs = [a.strip() for a in adj.split(",") if a.strip()]
            send_email(rem, asu, cuer, empresa=emp, adjuntos=adjs)
            _listado_emails.clear()
            st.success("Correo simulado ingresado y pendiente de procesamiento.")


def pestana_chat() -> None:
    st.subheader("Chat del asistente por thread (cliente)")
    from utp_assistant.inbox import list_emails

    emails = list_emails()
    if not emails:
        st.info("Sin correos aun.")
        return

    opciones = {f"#{e['thread_id']} — {e['empresa']} ({e['cliente']})": e["thread_id"] for e in emails}
    seleccion = st.selectbox("Thread", list(opciones), index=0)
    thread_id = opciones[seleccion]
    st.session_state["thread_seleccionado"] = thread_id

    historial = db.get_thread_messages(thread_id)
    for m in historial:
        papel = "assistant" if m["role"] == "assistant" else "user"
        with st.chat_message(papel):
            st.markdown(m["content"])

    texto = st.chat_input("Escribe un mensaje al asistente (se añadira al thread y se ejecutara un Run)")
    if texto:
        with st.chat_message("user"):
            st.markdown(texto)
        db.add_message(thread_id, "user", texto)
        try:
            with st.spinner("Ejecutando Run..."):
                res = runner.run_assistant(thread_id, client=_get_client())
            with st.chat_message("assistant"):
                st.markdown(res["resumen_final"])
        except Exception as exc:  # noqa: BLE001
            st.error(f"Error en el Run: {exc}")


def pestana_resultados() -> None:
    st.subheader("Sistemas externos simulados")
    datos = _resultados()
    tab_jira, tab_crm, tab_cal, tab_slack = st.tabs(["Jira", "CRM", "Calendar", "Slack"])
    with tab_jira:
        st.dataframe(datos["jira"], use_container_width=True)
    with tab_crm:
        st.dataframe(datos["crm"], use_container_width=True)
    with tab_cal:
        st.dataframe(datos["calendar"], use_container_width=True)
    with tab_slack:
        st.dataframe(datos["slack"], use_container_width=True)
    st.caption("Los datos se leen de SQLite en cada render.")


def main() -> None:
    _init()
    _login()
    user = st.session_state["user"]
    st.sidebar.markdown(f"### Usuario\n{user['nombre']}\n{user['email']}")
    if st.sidebar.button("Cerrar sesion"):
        st.session_state["user"] = None
        st.rerun()

    st.title("UTP Assistant")
    st.caption("Asistente IA para correos de clientes — red interna simulada de 2 usuarios")

    tab1, tab2, tab3 = st.tabs(["📥 Bandeja", "💬 Chat del thread", "📊 Resultados"])
    with tab1:
        pestana_bandeja()
    with tab2:
        pestana_chat()
    with tab3:
        pestana_resultados()


if __name__ == "__main__":
    main()