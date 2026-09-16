# Semana 06 - Chatbot multimodal con Groq y Streamlit

Proyecto de laboratorio alineado con la Sesión 2 de la Unidad 2.
Usa la API de **Groq** (compatible con OpenAI) para el chatbot y la transcripción de audio.

## Objetivos

- Implementar un chatbot sobre comida peruana.
- Crear una interfaz con Streamlit.
- Mantener el historial de conversación durante la sesión.
- Transcribir un archivo de audio mediante la API de transcripción de Groq.

## 1. Requisitos

- Python 3.10 o superior.
- Internet.
- Cuenta de Groq con clave de API en https://console.groq.com.
- Visual Studio Code recomendado.

## 2. Crear entorno virtual (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 3. Configurar la clave de API

```powershell
Copy-Item .env.example .env
```

Abra `.env` y reemplace el marcador `GROQ_API_KEY` por su clave de Groq
(`gsk_...`). No comparta este archivo ni lo suba a GitHub.

## 4. Ejecutar

```powershell
streamlit run app.py
```

Streamlit mostrará una dirección local, normalmente `http://localhost:8501`.

## 5. Prueba del chatbot

1. Pregunte: `¿Qué es el ceviche peruano?`
2. Luego pregunte: `¿Y cuáles son sus ingredientes principales?`
3. Verifique que la segunda respuesta conserve el contexto de la conversación.

## 6. Prueba de audio

1. Abra la pestaña **Transcripción**.
2. Cargue un archivo corto MP3/WAV/M4A.
3. Pulse **Transcribir audio**.
4. Verifique el texto resultante.

## 7. GitHub

Antes de publicar, confirme que `.env` está ignorado:

```powershell
git status
```

Nunca publique una clave de API. El repositorio debe contener `.env.example`, no `.env`.

## Nota técnica de actualización

El laboratorio mantiene el recorrido didáctico de Chat Completions, ahora sobre el
endpoint compatible de Groq (`https://api.groq.com/openai/v1`). El chatbot usa
modelos como `openai/gpt-oss-120b` y la transcripción usa `whisper-large-v3`.
