# PRP: UTP Assistant — Prototipo de asistente IA para correos simulados (2 usuarios)

> **Proyecto:** UTP Assistant
> **Versión:** 1.0
> **Creado:** 2026-09-22
> **Estado:** Ready
> **Modelo base:** Groq (`llama-3.3-70b-versatile`) vía Chat Completions + Local Tool Calling
> **Basado en:** "Propuesta de diseño técnico de un asistente de IA" (Grupo X, Facultad de Ingeniería, 2026)

---

## Goal

Construir un prototipo funcional del asistente **"UTP Assistant"** que:

1. Se conecte a la **API de Groq** (key `gsk_…` provista por el equipo, cargada desde `.env`, NUNCA hardcodeada).
2. Analice **correos simulados** (no reales) dentro de una **red interna de 2 usuarios** de UTPConsult, cada uno con su propia bandeja de entrada.
3. Extraiga remitente, empresa, requisitos, solicitudes de reunión, plazos y compromisos.
4. Invoque las 4 funciones definidas en el diseño (`actualizar_contacto_en_crm`, `crear_tarea_en_jira`, `agendar_reunion_en_google_calendar`, `enviar_notificacion_interna`), implementadas contra **sistemas externos SIMULADOS** (locales, vía SQLite) para que el prototipo funcione sin credenciales reales de Jira/Calendar/CRM/Slack.
5. Entregue al usuario el resumen en 3 bloques (resumen ejecutivo / acciones ejecutadas / pendientes y alertas) según el system prompt del diseño.

## Why

- Validar y demostrar la propuesta de diseño técnica del grupo en un entorno controlado, sin tocar sistemas reales de la empresa.
- Probar la orquestación completa de *function calling* con la API de Groq (que **NO ofrece Assistants API**), replicando manualmente el ciclo Thread → Run → `requires_action` → `submit_tool_outputs` descrito en el diseño.
- Proveer una base educativa y extendible: luego basta reemplazar los "mocks" SQLite por integraciones reales (Jira, Google Calendar, HubSpot/CRM, Slack).

## What

### Alcance del prototipo
- **UI en Streamlit** (coherente con las referencias del diseño: chat elements, session_state, file_uploader).
- **2 cuentas de usuario interno** (ej. `bernie.rivera@utpconsult.com` y `odalis.dominguez@utpconsult.com`).
- Bandeja de entrada simulada: correos precargados de prospectos ficticios (ej. Ana Torres / TechCorp) + envío manual de correos nuevos.
- **Conector de ingesta simulado**: un botón "procesar correos" que toma cada correo sin procesar y ejecuta un *Run*.
- **Ciclo de Run propio** (runner) con estados: `queued → in_progress → requires_action → (tool_outputs) → completed`.
- **4 herramientas (tool schemas)** tal cual el diseño (sección 3 del doc) + **implementaciones que escriben en tablas locales** simulando Jira, Calendar, CRM y Slack.
- **System prompt** idéntico al diseño (sección 2 del doc), con las reglas de no-inventar-datos, orden de ejecución, y formato de salida en 3 bloques.
- Persistencia: **SQLite** (`utp_assistant.db`) para threads, mensajes, correos, usuarios, tareas Jira, eventos Calendar, contactos CRM y notificaciones "Slack".

### Fuera de alcance (a propósito)
- Integración real con Jira, Google Calendar, CRM y Slack (los mocks ya dejan el contrato listo para reemplazo).
- Envío/recepción real de correos (SMTP/IMAP o webhook).
- Manejo de documentos PDF con la herramienta `search` de Assistants (no existe en Groq; los adjuntos se manejan como metadatos de texto).

### Decisiones técnicas (FUNDAMENTAL para no fallar)
> El diseño original eligió **Assistants API**. **Groq NO tiene Assistants API.** Por lo tanto la implementación usa **Chat Completions + Local Tool Calling** y reconstruye manualmente lo que el diseño describe:
> - **Thread** → tabla `threads` + `messages` en SQLite; se localiza por `cliente` (remitente/empresa).
> - **Message (rol user)** → mensaje con el correo normalizado (remitente, asunto, fecha, cuerpo, adjuntos).
> - **Run** → función `run_assistant(thread_id)`: envía `messages` + `tools` a `chat.completions.create`.
>   - Si la respuesta trae `message.tool_calls` (`finish_reason == "tool_calls"`) → estado `requires_action` → la app (NO el modelo) ejecuta las funciones → appendea `role: "assistant"` (con `tool_calls`) y luego un mensaje `role: "tool"` por cada `tool_call_id` → reenvía (`this equivale a submit_tool_outputs`) → `completed` cuando el modelo responde texto final.
> - **Orden de ejecución**: el system prompt obliga a CRM → Jira → Calendar → Notificación. El runner respeta (si llegan) el orden en que el modelo devuelve los `tool_calls`; ante duda, ordena según este orden lógico.

### Success Criteria
- [ ] Al procesar el correo de ejemplo de Ana Torres (TechCorp) se ejecutan 3 acciones en orden: CRM upsert → tarea Jira creada (ej. `PAGOS-1`) → evento tentativo en Calendar; y al final notificación interna registrada.
- [ ] Los parámetros ausentes del correo (fecha exacta de reunión) NO son inventados: `es_tentativa: true`, nota de pendiente registrada.
- [ ] Ambos usuarios internos pueden entrar a la app (sesión con `st.session_state`), ver su bandeja, procesar correos y ver resultados (tareas, contactos, eventos, notificaciones).
- [ ] Correos sin acción (agradecimientos/spam) resultan en "sin acción requerida" y NO invocan herramientas.
- [ ] Suite de tests pasa con Groq **mockeado** (sin red), y la integración manual con la key real funciona en dev.
- [ ] La API key vive en `.env` (`.gitignore`) y nunca aparece hardcodeada en código.

---

## All Needed Context

### Documentación y referencias
```yaml
- url: https://console.groq.com/docs/tool-use/local-tool-calling
  why: Implementación de local tool calling (ciclo exacto a replicar). CRITICO.
- url: https://console.groq.com/docs/tool-use/overview
  why: Tabla de modelos con soporte de herramientas y paralelismo.
- url: https://github.com/groq/groq-api-cookbook/blob/HEAD/tutorials/parallel-tool-use/parallel-tool-use.ipynb
  why: Patrón de mensajes con tool_calls + role tool + tool_call_id.
- url: https://docs.streamlit.io/develop/api-reference/chat
  why: Componentes de chat usados en la UI.
- url: https://docs.streamlit.io/develop/api-reference/caching-and-state/st.session_state
  why: Gestión de sesión por usuario.
- url: https://docs.streamlit.io/develop/api-reference/widgets/st.file_uploader
  why: Subida de adjuntos simulados.
```

### Fuente de requisitos (leer antes de codear)
- Diseño técnico: `docs/Propuesta_UPT_Assistant.md` (si se copia el documento a `utp-assistant/docs/`). Si no existe, transcribir literalmente las secciones 2 (system prompt), 3 (schemas de las 4 herramientas) y 4 (ciclo del Run) en los archivos indicados abajo.

### Estructura actual del proyecto
```bash
# NO existe aún el proyecto. Crear desde cero esta estructura:
utp-assistant/
├── .env.example          # GROQ_API_KEY=... (placeholder)
├── .gitignore            # .env, *.db, __pycache__, .venv
├── pyproject.toml        # o requirements.txt
├── README.md
├── docs/
│   └── Propuesta_UPT_Assistant.md   # copia del documento del grupo (opcional, recomendado)
├── PRPs/
└── utp_assistant/
    ├── __init__.py
    ├── config.py             # carga de env: GROQ_API_KEY, MODEL, DB_PATH
    ├── db.py                 # conexión SQLite + schema + seed
    ├── system_prompt.py      # texto literal del system prompt (sección 2)
    ├── tools.py              # schemas de las 4 funciones (sección 3)
    ├── runner.py             # ciclo del Run (queued→in_progress→requires_action→completed)
    ├── services/
    │   ├── __init__.py
    │   ├── jira.py           # SIM_Jira: crea tarea (tabla jira_tasks)
    │   ├── calendar.py       # SIM_Calendar: crea evento (tabla calendar_events)
    │   ├── crm.py            # SIM_CRM: upsert contacto (tabla crm_contacts)
    │   └── slack.py          # SIM_Slack: notificación (tabla slack_messages)
    ├── inbox.py              # bandeja simulada: precargada + envío manual
    └── app.py                # UI Streamlit (login de 2 usuarios, chat, bandeja, tablas de resultados)
tests/
    ├── test_tools.py
    ├── test_runner.py
    └── test_system_prompt.py
```

### Gotchas críticos (Groq)
```python
# 1. Groq NO ofrece Assistants API: NO usar retroalimentación de threads. Orquestar manualmente.
# 2. Antes de reenviar tool outputs, appendea el message de asistente TAL CUAL:
#    messages.append(response.choices[0].message)  # incluye tool_calls
#    Luego, por cada tool_call, un mensaje:
#    messages.append({"role": "tool", "tool_call_id": id, "content": json.dumps(resultado)})
# 3. temperature recomendada 0.0–0.5 para tool calling estable (Groq docs).
# 4. tool_choice = "auto" (con tools presentes). Usar "none" solo en la llamada final
#    de resumen para forzar texto (evita contenido null).
# 5. parallel_tool_calls = True por defecto: el modelo puede emitir varias funciones
#    en un solo tool_calls array. El runner debe procesarlas todas y mapear cada
#    resultado a su tool_call_id.
# 6. tool_call.function.arguments viene como string JSON: json.loads() antes de invocar.
# 7. Rate limits de Groq: usar threading.Sleep/backoff simple o retry en 429/rate_limit.
# 8. El SDK oficial es `groq` (pip install groq), cliente: Groq(api_key=os.getenv("GROQ_API_KEY")).
# 9. max tokens por request: usar max_completion_tokens=4096 (suficiente).
# 10. Streamlit: la ejecución del runner bloquea (preferir progreso con st.status/spinner).
```

---

## Implementation Blueprint

### Tasks (en orden de ejecución)

```yaml
Task 1: Esqueleto del proyecto y config
  - CREATE: utp-assistant/.gitignore        # .env, *.db, __pycache__, .venv
  - CREATE: utp-assistant/.env.example      # GROQ_API_KEY=tu_api_key_groq
  - CREATE: utp-assistant/pyproject.toml    # python>=3.11; deps: groq, streamlit, python-dotenv, pydantic
  - CREATE: utp-assistant/README.md         # cómo instalar, .env, correr app, correr tests
  - CREATE: utp_assistant/config.py
    - pattern: "GROQ_API_KEY = os.getenv('GROQ_API_KEY')"  # NUNCA hardcodear
    - MODEL default: "llama-3.3-70b-versatile"
    - DB_PATH default: str(Path(__file__).parent / "utp_assistant.db")
  - COPY: documento del grupo a docs/Propuesta_UPT_Assistant.md (fuente de contexto)

Task 2: Capa de datos SQLite
  - CREATE: utp_assistant/db.py
  - Tablas:
    - users(id, nombre, email, pass_hash)      # 2 usuarios internos
    - threads(id, cliente, correo_contacto, empresa, created_at)  # "Thread" por cliente
    - messages(id, thread_id, role, content, created_at)          # historial del thread
    - emails(id, thread_id, remitente, asunto, cuerpo, fecha, adjuntos_json, procesado, run_id)
    - jira_tasks(id, key, proyecto_key, titulo, descripcion, prioridad, cliente_relacionado, fecha_limite, created_at)
    - calendar_events(id, titulo, asistentes_json, fecha_propuesta, hora_propuesta, duracion_minutos, agenda, es_tentativa, created_at)
    - crm_contacts(id, nombre_contacto, empresa, correo_electronico, etapa_pipeline, interes_principal, ultima_interaccion_resumen, documentos_adjuntos_json, updated_at)
    - slack_messages(id, canal, resumen_ejecutivo, acciones_realizadas_json, alertas_json, nivel_urgencia, created_at)
  - Nota técnica: crm_contacts con UNIQUE(correo_electronico) para upsert.
  - CREATE seed(): insertar 2 users (contraseñas simples hashadas con hashlib/sha256 + salt en prototipo)
    - Primera vez que inicies la app, crear 2 emails simulados en 2 threads distintos
      (uno que SÍ requiere acciones - Ana Torres/TechCorp; otro con "Gracias por la propuesta"; sin acciones).
  - GOTCHA: usar sqlite3 con row_factory=sqlite3.Row; definir path absoluto.

Task 3: System prompt literal
  - CREATE: utp_assistant/system_prompt.py
  - Contenido: transcribir íntegramente la sección 2 del diseño
    (IDENTIDAD Y ROL, OBJETIVOS, REGLAS DE COMPORTAMIENTO, TONO, FORMATO DE SALIDA).
  - MODO: constante SYSTEM_PROMPT = """...""".

Task 4: Schemas de herramientas + implementaciones simuladas
  - CREATE: utp_assistant/tools.py
    - Exportar TOOLS = [crear_tarea_en_jira, agendar_reunion_en_google_calendar,
                        actualizar_contacto_en_crm, enviar_notificacion_interna]
    - Copiar esquemas JSON exactos de la sección 3 del diseño.
  - CREATE services/jira.py, calendar.py, crm.py, slack.py
    - Cada función: recibe args del modelo, valida requireds, inserta en su tabla,
      retorna dict JSON {ok: true, id: "...", detalle: "..."} (esto es lo que el modelo recibe como tool_output).
    - CRM: upsert por correo_electronico (UPDATE si existe, INSERT si no).
    - Calendar: devuelve {ok, event_id, es_tentativa}.
    - Simulan "APIs externas"; no dependen de credenciales reales.

Task 5: Runner (ciclo del Run equivalente a requires_action → submit_tool_outputs)
  - CREATE: utp_assistant/runner.py
  - APIs:
    - get_or_create_thread(cliente, correo_contacto, empresa) -> thread_id
    - add_email_to_thread(email) -> registra en emails + appendea messages (rol user con el correo normalizado)
    - PROCESS_ORDER = ["actualizar_contacto_en_crm", "crear_tarea_en_jira",
                       "agendar_reunion_en_google_calendar", "enviar_notificacion_interna"]
    - run_assistant(thread_id) -> dict(estado, resumen_final, tool_calls_ejecutadas)
  - Flujo:
    1. Leer messages del thread + system prompt.
    2. Llamar client.chat.completions.create(model, messages, tools, tool_choice="auto", temperature=0.2).
    3. Si message.tool_calls:
       - mark estado = "requires_action"
       - appendea respuesta (con tool_calls)
       - para cada tool_call (ordenar respetando PROCESS_ORDER si aplica):
         ejecutar dispatch(tool_call) y appendea {"role":"tool","tool_call_id":...,"content":json.dumps(out)}
       - llamada final con tool_choice="none" → texto resumen del asistente
       - mark estado = "completed"
    4. Guardar mensaje final en messages y run_id en emails.
    5. Manejar errores: credencial inválida (401), rate limit (429 con retry exponencial) → tool_output con {ok:false, error}.
  - GOTCHA: resetear estados a in_progress durante la ejecución; deviceTransactional a nivel de un correo (un run por correo).

Task 6: Bandeja y conector de ingesta simulado
  - CREATE: utp_assistant/inbox.py
  - list_pending_emails(), list_all_emails(), mark_as_processed(email_id, run_id)
  - send_email(remitente_externo, asunto, cuerpo, adjuntos) → crea thread y email nuevo (simula webhook).

Task 7: UI Streamlit
  - CREATE: utp_assistant/app.py
  - Login con 2 usuarios hardcodeados en BD (radio/selectbox de usuario + input contraseña simple).
  - Sidebar: selector de usuario → estado en st.session_state["user"].
  - Pestañas:
    - "Bandeja": lista emails, botón "Procesar correos pendientes" (st.status con spinner del run),
      botón "Simular correo entrante" (formulario remitente/asunto/cuerpo).
    - "Chat del thread": al seleccionar un correo o cliente, mostrar historial de messages y
      opción de escribir un mensaje que se añade al thread y ejecuta run_assistant (st.chat_message / st.chat_input).
    - "Resultados": tablas jira_tasks, crm_contacts, calendar_events, slack_messages (st.dataframe).
  - MIRROR pattern: Streamlit oficial chat example (st.session_state.messages).

Task 8: Pruebas (pytest, Groq mockeado)
  - CREATE: tests/test_tools.py    # cada service inserta y devuelve {ok:true,...}
  - CREATE: tests/test_runner.py   # monkeypatch runner.client: simular 1) respuesta con tool_calls,
    # 2) respuesta final sin tool_calls; verificar mensajes intermedios y orden.
  - CREATE: tests/test_system_prompt.py  # SYSTEM_PROMPT contiene keywords críticas
    # ("PENDIENTE DE CONFIRMACIÓN", "sin accion requerida", orden CRM→Jira→Calendar→Notificar).
```

### Pseudocode (detalles CRÍTICOS)

```python
# Task 5: Runner
def run_assistant(thread_id: str) -> dict:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages += [{"role": m.role, "content": m.content} for m in load_thread_messages(thread_id)]

    # PATTERN: primera llamada permite herramientas
    response = client.chat.completions.create(
        model=MODEL, messages=messages, tools=TOOLS,
        tool_choice="auto", temperature=0.2, max_completion_tokens=4096,
    )
    msg = response.choices[0].message
    executed = []

    # CRITICAL: este es el equivalente local de requires_action
    if msg.tool_calls:
        messages.append(msg)  # appendea el mensaje del asistente CON tool_calls
        tool_calls = sorted(msg.tool_calls,
                            key=lambda tc: PROCESS_ORDER.index(tc.function.name)
                            if tc.function.name in PROCESS_ORDER else 99)
        for tool_call in tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)  # GOTCHA: viene como string
            out = dispatch(name, args) or {"ok": False, "error": "herramienta desconocida"}
            executed.append({"name": name, "args": args, "output": out})
            messages.append({"role": "tool", "tool_call_id": tool_call.id,
                             "content": json.dumps(out, ensure_ascii=False)})
        # CRITICAL: tool_choice="none" fuerza resumen en texto (evita content null)
        final = client.chat.completions.create(
            model=MODEL, messages=messages, tools=TOOLS,
            tool_choice="none", temperature=0.2, max_completion_tokens=4096,
        )
        final_text = final.choices[0].message.content
    else:
        final_text = msg.content  # "sin acción requerida" o aclaración

    persist_final_message(thread_id, "assistant", final_text)
    return {"estado": "completed" if executed or final_text else "nocontent",
            "resumen_final": final_text, "tool_calls": executed}

def dispatch(name, args):
    # CRITICAL: siempre devolver dict JSON serializable (el modelo recibe esto como tool_output)
    try:
        registry = {
            "actualizar_contacto_en_crm": crm.upsert_contact,
            "crear_tarea_en_jira": jira.create_task,
            "agendar_reunion_en_google_calendar": calendar.create_event,
            "enviar_notificacion_interna": slack.send_notification,
        }
        return registry[name](**args)
    except KeyError:
        return {"ok": False, "error": f"función {name} no registrada"}
    except TypeError as e:
        return {"ok": False, "error": f"parámetros inválidos para {name}: {e}"}
```

### Integration Points
```yaml
CONFIG:
  - crear en: utp_assistant/.env
  - contenido: "GROQ_API_KEY=gsk_…"   (el equipo pega aquí la key de Groq provista)
  - GOTCHA: correr el runner SIEMPRE desde un entorno con .env cargado (python-dotenv).

ROUTES/UI:
  - app.py incluye 3 pestañas; session_state["user"] define qué bandeja se muestra.
  - cada "procesar correo" es transaccional: un email → un run → un run_id.

EXTERNAL (simulados, reemplazables):
  - services/* escriben en SQLite. Para producción futura: cambiar dispatch()
    manteniendo el MIMO (mismo nombre/args/json de retorno) contra APIs reales.
```

---

## Validation Loop

### Level 1: Sintaxis y estilo
```bash
cd ~/utp-assistant
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"           # deps: groq, streamlit, python-dotenv, pydantic; dev: pytest, ruff
ruff check utp_assistant tests/
```

### Level 2: Tests unitarios (sin red)
```bash
pytest tests/ -v

# Casos mínimos que deben existir:
def test_upsert_crm_crea_y_actualiza(): ...          # mismo correo → UPDATE, nuevo → INSERT
def test_crear_tarea_invalida_retorna_error(): ...   # falta required → {ok:false}
def test_runner_procesa_tool_calls_en_orden(): ...   # monkeypatch de client → verificar secuencia
def test_runner_sin_accion_no_invoca_tools(): ...    # respuesta sin tool_calls → texto + estado completed
def test_system_prompt_rules(): ...                  # keywords del prompt presentes
```

### Level 3: Integración (key real de Groq en dev)
```bash
# 1. Copiar .env.example → .env y pegar la GROQ_API_KEY provista
# 2. Arrancar UI
streamlit run utp_assistant/app.py
# 3. Probar manualmente:
#    - Login como usuario 1 → pestaña Bandeja → "Procesar correos pendientes"
#    - Verificar en Resultados: contacto CRM creado, tarea PAGOS-… creada,
#      evento con es_tentativa=True, notificación Slack registrada.
#    - Enviar correo de agradecimiento → debe marcar "sin acción requerida" sin tool_calls.
```

---

## Final Checklist

- [ ] `pytest tests/ -v` pasa (Groq mockeado, sin red).
- [ ] `ruff check utp_assistant/ tests/` sin errores.
- [ ] Integración manual con key real: correo Ana Torres produce las 3 acciones + notificación.
- [ ] Parámetros faltantes marcados como `PENDIENTE DE CONFIRMACIÓN` / `es_tentativa: true` (no inventados).
- [ ] Orden de ejecución respetado: CRM → Jira → Calendar → Notificación.
- [ ] Ambos usuarios pueden usar la app con bandejas independientes.
- [ ] Correo sin acción → "sin acción requerida", sin tool_calls.
- [ ] La API key solo existe en `.env` (gitignored), nunca en el código.
- [ ] Errores de la API (401/429) manejados con mensaje claro.
- [ ] README con instrucciones de instalación/ejecución.
- [ ] Logs/registro de auditoría: cada acción queda en su tabla SQLite con timestamps.

---

## Anti-Patterns a evitar

- ❌ No intentar usar Assistants API de OpenAI o esperar Threads nativos en Groq: orquestar manualmente.
- ❌ No hardcodear `GROQ_API_KEY` en el código ni en el PRP.
- ❌ No hacer `json.loads(tool_call.function.arguments)` → sí (es string).
- ❌ No olvidar appendea el mensaje asistente con `tool_calls` antes de los `role: "tool"` (rompe el loop).
- ❌ No usar sync en contexto sync de Streamlit sin cuidado (ejecución bloqueante OK aquí, mostrar spinner).
- ❌ No inventar datos: aplicar reglas del system prompt en la extracción de parámetros.
- ❌ No capturar `except Exception` vacío en el runner: loguear y devolver `{ok:false, error}` al modelo.

---

## Notes

- **Adaptación de arquitectura clave**: el diseño propone Assistants API (Threads/Runs/`requires_action`); Groq lo sustituye por Chat Completions stateless + Local Tool Calling. La capa `runner.py` materializa el estado del Run y el punto de control humano (`es_tentativa`) sin necesidad del framework propietario.
- **Siguiente iteración posible**: reemplazar `services/*` por SDK reales (Jira REST, Google Calendar API, HubSpot CRM, Slack Webhook) manteniendo `dispatch()` y los schemas intactos.
- **Seguridad**: la key `gsk_…` fue compartida en texto plano en el chat. Se recomienda rotarla en la consola de Groq y usar la nueva dentro de `.env`. Nunca subir `.env` al repositorio.
- **Modelo en Groq**: `llama-3.3-70b-versatile` tiene soporte de herramientas y paralelismo; es la opción recomendada para QA del prototipo. Alternativas: `openai/gpt-oss-120b`, `qwen/qwen3.6-27b` (ambas con parallel tool use).