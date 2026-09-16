import os
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

st.set_page_config(
    page_title="SaborPerú AI - Semana 06",
    page_icon="🍲",
    layout="centered",
)

API_KEY = os.getenv("GROQ_API_KEY")
TEXT_MODEL = os.getenv("GROQ_TEXT_MODEL", "openai/gpt-oss-120b")
AUDIO_MODEL = os.getenv("GROQ_AUDIO_MODEL", "whisper-large-v3")

if not API_KEY:
    st.error(
        "No se encontró GROQ_API_KEY. Copia .env.example como .env y coloca allí tu clave de Groq."
    )
    st.stop()

client = OpenAI(
    api_key=API_KEY,
    base_url="https://api.groq.com/openai/v1",
)

SYSTEM_PROMPT = """
Eres SaborPerú, un chatbot educativo especializado exclusivamente en comida peruana.
Responde en español claro, amable y breve.
Puedes explicar platos, ingredientes, regiones, técnicas culinarias e historia gastronómica general.
Si la consulta no está relacionada con comida peruana, indícalo amablemente y redirige la conversación a tu especialidad.
Cuando describas una receta, separa ingredientes y preparación.
No inventes datos; si no tienes suficiente certeza, dilo de forma explícita.
""".strip()


def init_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []


def reset_chat():
    st.session_state.messages = []


def chat_with_model(user_text: str) -> str:
    # La PPT explica el envío del historial completo para mantener contexto.
    # En esta práctica se usa Chat Completions para conservar esa correspondencia didáctica.
    api_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    api_messages.extend(st.session_state.messages)
    api_messages.append({"role": "user", "content": user_text})

    response = client.chat.completions.create(
        model=TEXT_MODEL,
        messages=api_messages,
    )
    return response.choices[0].message.content or ""


def transcribe_audio(uploaded_file) -> str:
    uploaded_file.seek(0)
    transcription = client.audio.transcriptions.create(
        model=AUDIO_MODEL,
        file=(uploaded_file.name, uploaded_file),
    )
    return transcription.text


init_state()

st.title("🍲 SaborPerú AI")
st.caption("Semana 06 - Chatbot con OpenAI + Streamlit + transcripción de audio")

chat_tab, audio_tab = st.tabs(["💬 Chatbot", "🎙️ Transcripción"])

with chat_tab:
    st.subheader("Chatbot sobre comida peruana")
    st.write(
        "Pregunta por platos, ingredientes, regiones o preparaciones de la gastronomía peruana."
    )

    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("Limpiar chat", use_container_width=True):
            reset_chat()
            st.rerun()

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ejemplo: ¿Qué ingredientes lleva un ají de gallina?"):
        with st.chat_message("user"):
            st.markdown(prompt)

        try:
            with st.spinner("Generando respuesta..."):
                answer = chat_with_model(prompt)
        except Exception as exc:
            st.error(f"No se pudo obtener respuesta de la API: {exc}")
        else:
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.session_state.messages.append({"role": "assistant", "content": answer})
            with st.chat_message("assistant"):
                st.markdown(answer)

with audio_tab:
    st.subheader("Transcripción de audio")
    st.write(
        "Carga un archivo de audio corto y conviértelo a texto usando el endpoint de transcripciones."
    )

    audio_file = st.file_uploader(
        "Selecciona un audio",
        type=["mp3", "wav", "m4a", "mp4", "mpeg", "mpga", "webm"],
    )

    if audio_file is not None:
        st.audio(audio_file)
        st.caption(f"Archivo: {audio_file.name}")

        if st.button("Transcribir audio", type="primary"):
            try:
                with st.spinner("Transcribiendo..."):
                    text = transcribe_audio(audio_file)
            except Exception as exc:
                st.error(f"No se pudo transcribir el audio: {exc}")
            else:
                st.success("Transcripción completada")
                st.text_area("Texto transcrito", text, height=220)
                st.download_button(
                    "Descargar transcripción (.txt)",
                    data=text,
                    file_name="transcripcion.txt",
                    mime="text/plain",
                )

with st.sidebar:
    st.header("Configuración")
    st.write(f"Modelo de texto: `{TEXT_MODEL}`")
    st.write(f"Modelo de audio: `{AUDIO_MODEL}`")
    st.info(
        "La clave de API se lee desde la variable GROQ_API_KEY. Nunca la publiques en GitHub."
    )
