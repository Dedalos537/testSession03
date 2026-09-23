# UTP Assistant

Prototipo del asistente de IA "UTP Assistant" para la gestión de correos simulados
en una red interna de 2 usuarios, basado en la propuesta de diseño técnico del grupo.

## Stack

- Python 3.11+
- [Groq API](https://console.groq.com) (Chat Completions + Local Tool Calling) — modelo `llama-3.3-70b-versatile`
- Streamlit (UI)
- SQLite (persistencia: threads, mensajes, y sistemas externos simulados Jira/Calendar/CRM/Slack)

> **Nota de arquitectura:** el diseño original plantea la Assistants API de OpenAI.
> Groq no ofrece Assistants API, por lo que el ciclo del Run (`requires_action` →
> `submit_tool_outputs`) se replica manualmente en `utp_assistant/runner.py`.

## Instalación

```bash
cd utp-assistant
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Configurar la API key (nunca commitearla)
cp .env.example .env
# editar .env y pegar GROQ_API_KEY
```

## Ejecución

```bash
# UI Streamlit
streamlit run utp_assistant/app.py

# Tests (sin red, Groq mockeado)
pytest tests/ -v

# Lint
ruff check utp_assistant/ tests/
```

## Estructura

```bash
utp-assistant/
├── docs/Propuesta_UPT_Assistant.md   # documento fuente del diseño
├── PRPs/001--utp-assistant-correos-asistente.md  # plan de implementación
├── utp_assistant/
│   ├── config.py                     # env: GROQ_API_KEY, MODEL, DB_PATH
│   ├── db.py                         # capa de datos SQLite (schema + seed)
│   ├── system_prompt.py              # prompt del sistema (sección 2)
│   ├── tools.py                      # schemas de las 4 funciones (sección 3)
│   ├── runner.py                     # ciclo del Run (Chat Completions + tool calling)
│   ├── inbox.py                      # bandeja simulada + conector de ingesta
│   ├── app.py                        # UI Streamlit (2 usuarios, bandeja, chat, resultados)
│   └── services/                     # SIM Jira/Calendar/CRM/Slack
└── tests/                            # test_tools, test_runner, test_system_prompt
```

Estado: Tasks 1–8 del PRP implementadas. Login: seleccionar usuario y contraseña `demo123`.