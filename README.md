# UTP Assistant

Prototipo del asistente de IA "UTP Assistant" para la gestión de correos simulados
en una red interna de 2 usuarios, basado en la propuesta de diseño técnico del grupo.

## Stack

- Python 3.11+
- [Groq API](https://console.groq.com) (Chat Completions + Local Tool Calling) — modelo predeterminado `openai/gpt-oss-120b` (configurable en `.env` con `MODEL`)
- Streamlit (UI) con diseño [Tabler](https://tabler.io) v1.3.0 (assets oficiales vendored en `utp_assistant/static/tabler`)
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
│   ├── db.py                         # capa de datos SQLite (schema + seed + auditoria)
│   ├── redactar.py                   # DLP: redacta tarjeta/DNI/CUIT/teléfono antes del modelo
│   ├── system_prompt.py              # prompt del sistema (sección 2, reglas anti-alucinación)
│   ├── tools.py                      # schemas de las 4 funciones (sección 3)
│   ├── runner.py                     # ciclo del Run (+ trazabilidad, auditoría, resumen legible)
│   ├── inbox.py                      # bandeja simulada + conector de ingesta
│   ├── theme.py                      # componentes UI estilo Tabler (topbar, métricas, tablas, empty states)
│   ├── static/tabler/                # CSS + iconos Tabler vendored (servido en /app/static)
│   ├── app.py                        # UI Streamlit (2 usuarios, bandeja, chat, resultados, revisión humana)
│   └── services/                     # SIM Jira/Calendar/CRM/Slack
└── tests/                            # test_tools, test_runner, test_system_prompt, test_app_ui, test_theme, test_redactar
```

## Guardarrailes implementados (Riesgos 1 y 2 del documento)

**Riesgo 1 - alucinaciones o extracción incorrecta:**
- El system prompt exige usar `"PENDIENTE DE CONFIRMACION"` cuando el correo no tiene fecha/hora
  explícita y marcar `es_tentativa: true`; prohíbe inventar o asumir datos.
- Las propuestas tentativas quedan pendientes de validación humana: la pestaña
  "Revisión humana" (Resultados) permite confirmarlas, con RBAC (solo el rol `Gerencia`).
- Validación estructural en cada servicio: parámetros obligatorios y enums (una prioridad
  inventada como "PENDIENTE DE CONFIRMACION" se rechaza y no se persiste).
- Trazabilidad: cada registro guarda `run_id` y `origen` (email id · fecha · asunto); el asistente
  cita el origen de cada dato en sus resúmenes.

**Riesgo 2 - seguridad y privacidad del cliente:**
- Redacción DLP (`redactar.py`) con chequeo Luhn: enmascara `[NUMERO DE TARJETA]`, `[DNI]`,
  `[CUIT]` y `[TELEFONO]` antes de que el texto llegue al modelo; la bandeja original se conserva.
- Minimización: al modelo solo se envía el historial reciente (`MAX_HISTORY_MESSAGES=20`).
- Auditoría: toda acción del asistente se registra en la tabla `auditoria` (acción, estado,
  detalle, usuario), visible en "Revisión humana".
- RBAC y log de confirmaciones para el punto de control humano.

Estado: Tasks 1–8 del PRP implementadas + guardarrailes de riesgos. Login: seleccionar usuario y contraseña `demo123`.

> La tabla "Sistemas externos simulados" y las bandejas renderizan siempre sus cabeceras
> y un estado vacío explícito aunque todavía no haya datos (verificado por AppTest en
> `tests/test_app_ui.py`).