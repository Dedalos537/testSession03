# Propuesta de diseño técnico de un asistente de IA

**Grupo X — Facultad de Ingeniería**

**Integrantes:**
- Prieto Prieto Óscar Eduardo
- Palacios Chero Josué Gabriel
- Dominguez Yarleque Odalis
- Centeno Barrutia Diego Alejandro
- Suárez Infante Jorge Manuel Gregorio

**Ing. Rivera Abad Bernardo**

**Piura, 2026**

---

## Contenido

1. Arquitectura General del Asistente
   - 1.1 Comparación técnica
   - 1.2 Elección y justificación
2. Diseño del Prompt de Sistema (System Prompt)
3. Definición de Herramientas (Function Calling)
   - crear_tarea_en_jira
   - agendar_reunion_en_google_calendar
   - actualizar_contacto_en_crm
   - enviar_notificacion_interna
4. Diseño del Flujo de Interacción (Ciclo de un Run)
5. Consideraciones de Riesgo y Ética
6. Referencias

---

## Introducción

UTPConsult es una consultora de desarrollo de software cuyo equipo de gestión de proyectos y ventas se encuentra sobrepasado por el volumen de correos electrónicos de clientes potenciales y existentes. Tareas manuales como extraer requisitos de hilos largos, crear tareas en el sistema de gestión de proyectos, agendar reuniones de seguimiento y actualizar el CRM consumen tiempo valioso que podría dedicarse a actividades de mayor valor agregado.

El presente documento constituye la propuesta de diseño técnico del asistente de inteligencia artificial "UTP Assistant", cuyo objetivo es automatizar ese flujo de trabajo. El alcance de este informe es de diseño y arquitectura: se define y justifica la API a utilizar, se redacta el prompt de sistema, se especifican los esquemas de las funciones (herramientas) que el asistente podrá invocar, se describe el ciclo de vida de una ejecución (Run) sobre un caso de uso concreto, y se identifican los principales riesgos del sistema junto con sus estrategias de mitigación.

## 1. Arquitectura General del Asistente

Para construir "UTP Assistant" existen, dentro del ecosistema de OpenAI, dos alternativas principales como núcleo del sistema: la Chat Completions API y la Assistants API. Ambas permiten enviar mensajes a un modelo de lenguaje y definir herramientas (function calling), pero difieren sustancialmente en la gestión de estado, en la orquestación de herramientas y en el manejo de archivos, tres aspectos críticos para el caso de uso de UTPConsult.

### 1.1 Comparación técnica

| Dimensión | Chat Completions API | Assistants API |
|---|---|---|
| Gestión de estado / memoria | Sin estado (stateless): la aplicación debe reenviar manualmente todo el historial relevante de mensajes en cada llamada. | Con estado (stateful) mediante Threads: cada cliente o prospecto se puede mapear a un hilo persistente que conserva automáticamente el historial de la conversación de correos. |
| Uso de herramientas (function calling) | Disponible, pero el ciclo de detección, ejecución y reinyección de resultados de las funciones debe orquestarse manualmente en cada turno de la aplicación. | Orquestación nativa del ciclo mediante el estado requires_action del Run: el propio framework gestiona la pausa, la validación y la reincorporación de los resultados. |
| Manejo de archivos adjuntos | Sin manejo nativo; el documento adjunto debe procesarse aparte (extracción de texto) antes de incluirlo como texto plano en el prompt. | Soporta adjuntar archivos y consultarlos mediante la herramienta de búsqueda de archivos, permitiendo que el propio asistente lea el documento de requisitos enviado por el cliente. |
| Complejidad de implementación | Menor complejidad para una sola llamada aislada, pero crece rápidamente en flujos multi-turno con varias herramientas encadenadas. | Mayor complejidad de configuración inicial, compensada por la gestión automática del ciclo de vida en flujos largos y con múltiples pasos. |
| Escalabilidad a muchos clientes en paralelo | La aplicación debe diseñar y mantener su propio almacén de conversaciones por cliente. | El servicio almacena los Threads de forma nativa, simplificando la escalabilidad a decenas o cientos de prospectos gestionados en simultáneo. |

### 1.2 Elección y justificación

Se selecciona la Assistants API como núcleo de "UTP Assistant". El problema de negocio de UTPConsult no es un intercambio aislado de pregunta y respuesta, sino la gestión continua de conversaciones por correo con decenas de clientes y prospectos en paralelo, cada uno con su propio hilo, sus propios documentos adjuntos y su propio historial de decisiones comerciales.

- **Gestión de estado por cliente:** la abstracción de Thread permite asociar un identificador persistente a cada prospecto (por ejemplo, TechCorp) y despreocuparse de reconstruir manualmente el contexto en cada nuevo correo del hilo.
- **Orquestación nativa de herramientas:** el estado requires_action del Run ofrece un punto de control natural para el patrón "human-in-the-loop" que requiere este flujo — antes de que una función modifique un sistema externo (Jira, Calendar, CRM), la aplicación puede inspeccionar los tool_calls propuestos por el modelo.
- **Manejo integrado de archivos:** permite que "UTP Assistant" consulte directamente documentos de requisitos, como el que adjunta Ana Torres en el caso de ejemplo, sin un pipeline adicional de extracción de texto previo a la llamada al modelo.
- **Menor código de orquestación propio:** al delegar la gestión del historial y del ciclo de ejecución al framework, el equipo de UTPConsult reduce la superficie de código que debe mantener y depurar en producción.

En síntesis, si bien la Chat Completions API resultaría suficiente para una integración simple de una sola interacción, la naturaleza multi-cliente, multi-turno y con documentos adjuntos del flujo de correos de UTPConsult hace que la gestión de hilos y la orquestación de herramientas de la Assistants API sean claramente superiores para este caso de uso específico.

## 2. Diseño del Prompt de Sistema (System Prompt)

A continuación, se presenta el prompt de sistema completo de "UTP Assistant", redactado en formato de texto plano, tal como se cargaría en el campo de instrucciones del asistente.

**IDENTIDAD Y ROL**

Eres "UTP Assistant", el asistente virtual de gestion de proyectos y ventas de UTPConsult, una consultora de desarrollo de software. Actuas como un gestor de proyectos eficiente y proactivo: tu funcion es leer los correos electronicos de clientes potenciales y existentes, extraer la informacion relevante y ejecutar las acciones administrativas necesarias para que el equipo humano no tenga que hacerlo manualmente.

**OBJETIVOS**

1. Leer y comprender el contenido de correos entrantes, incluyendo hilos largos y documentos adjuntos.
2. Extraer con precision los datos del remitente, la empresa, los requerimientos tecnicos, las solicitudes de reunion, los plazos y los compromisos mencionados.
3. Determinar que acciones administrativas se derivan del correo (crear tarea, agendar reunion, actualizar CRM, notificar al equipo) e invocar las funciones correspondientes.
4. Entregar al equipo interno un resumen claro, ordenado y accionable de cada correo procesado.
5. Reducir el trabajo manual repetitivo del equipo sin sacrificar la exactitud de la informacion registrada.

**REGLAS DE COMPORTAMIENTO**

- Nunca inventes ni asumas datos que no esten explicitamente en el correo o en sus adjuntos. Si un dato es indispensable para ejecutar una funcion y no esta presente, no completes ese campo con una suposicion: marcalo como "PENDIENTE DE CONFIRMACION" y sugiere la pregunta de seguimiento que el equipo deberia enviar al cliente.
- Si el correo es ambiguo o contiene informacion contradictoria, no interrumpas el flujo de trabajo: registra la accion con la informacion disponible y describe la ambiguedad de forma explicita en el campo de notas o alertas correspondiente, para que un miembro del equipo la revise antes de confirmar la accion con el cliente.
- Antes de invocar una funcion, verifica que cuentas con todos los parametros obligatorios definidos en su esquema. Si falta un parametro obligatorio y no puede inferirse de forma confiable, no invoques la funcion: reportalo como pendiente.
- Cuando un correo requiera varias acciones, ejecutalas en este orden logico: primero actualizar_contacto_en_crm, luego crear_tarea_en_jira, despues agendar_reunion_en_google_calendar y, al final, enviar_notificacion_interna con el resumen consolidado.
- Nunca tomes decisiones comerciales (precios, descuentos, condiciones contractuales) ni te comuniques directamente con el cliente: toda tu salida esta dirigida exclusivamente al equipo interno de UTPConsult.
- Si el correo no requiere ninguna accion (agradecimientos, mensajes automaticos, spam), no invoques ninguna funcion y reportalo como "sin accion requerida", indicando brevemente el motivo.
- Cita siempre el origen de cada dato relevante que extraigas (por ejemplo, "segun el correo del [fecha], remitente [nombre]") para mantener trazabilidad ante cualquier revision posterior.

**TONO**

Profesional, claro y orientado a la accion, como el de un gestor de proyectos experimentado dirigiendose a sus colegas. Evita la informalidad excesiva y tambien evita la rigidez innecesaria: prioriza que cada mensaje sea facil de leer y de accionar en pocos segundos.

**FORMATO DE SALIDA**

Cuando comuniques resultados al equipo interno, organiza siempre tu respuesta en tres bloques:

1. Resumen ejecutivo del correo (2 a 3 lineas).
2. Acciones ejecutadas (lista de funciones invocadas, con sus parametros clave y el resultado obtenido).
3. Pendientes y alertas (ambiguedades, datos faltantes o riesgos detectados que requieren revision humana).

## 3. Definición de Herramientas (Function Calling)

Se definen cuatro funciones que "UTP Assistant" puede invocar durante un Run. Cada esquema sigue el formato de definición de herramientas (tools) de la API de OpenAI. Aquí solo se define el contrato de la función para la API; su implementación en cada sistema externo queda fuera del alcance de este documento.

### 3.1 crear_tarea_en_jira

```json
{
  "type": "function",
  "function": {
    "name": "crear_tarea_en_jira",
    "description": "Crea una nueva tarea (issue) en el proyecto correspondiente de Jira a partir de un requerimiento identificado en el correo de un cliente. Se usa cuando el mensaje describe una accion de trabajo pendiente para el equipo (preparar una propuesta, resolver una duda tecnica, dar seguimiento a un modulo, etc.).",
    "parameters": {
      "type": "object",
      "properties": {
        "proyecto_key": {
          "type": "string",
          "description": "Codigo del proyecto en Jira al que pertenece la tarea (ej. 'CRM', 'PAGOS'). Usar 'GENERAL' si no se puede determinar con certeza."
        },
        "titulo": {
          "type": "string",
          "description": "Titulo breve y accionable de la tarea, en modo imperativo (ej. 'Preparar propuesta tecnica del modulo de pagos')."
        },
        "descripcion": {
          "type": "string",
          "description": "Descripcion detallada de la tarea, incluyendo el contexto extraido del correo del cliente."
        },
        "prioridad": {
          "type": "string",
          "enum": ["Baja", "Media", "Alta", "Urgente"],
          "description": "Prioridad estimada segun la urgencia expresada por el cliente en el correo."
        },
        "cliente_relacionado": {
          "type": "string",
          "description": "Nombre de la empresa o del contacto del cliente asociado a la tarea."
        },
        "fecha_limite": {
          "type": "string",
          "description": "Fecha limite sugerida en formato YYYY-MM-DD, solo si se menciona o se puede inferir explicitamente del correo."
        }
      },
      "required": ["proyecto_key", "titulo", "descripcion", "cliente_relacionado"]
    }
  }
}
```

### 3.2 agendar_reunion_en_google_calendar

```json
{
  "type": "function",
  "function": {
    "name": "agendar_reunion_en_google_calendar",
    "description": "Crea una propuesta de evento en Google Calendar para dar seguimiento a una solicitud de reunion de un cliente. Se usa cuando el correo solicita explicitamente coordinar una llamada o reunion.",
    "parameters": {
      "type": "object",
      "properties": {
        "titulo": {
          "type": "string",
          "description": "Titulo del evento (ej. 'Reunion de seguimiento - TechCorp - Modulo de pagos')."
        },
        "asistentes": {
          "type": "array",
          "items": { "type": "string" },
          "description": "Lista de correos electronicos de los asistentes internos y externos a invitar."
        },
        "fecha_propuesta": {
          "type": "string",
          "description": "Fecha propuesta en formato YYYY-MM-DD. Si el cliente solo indica un rango (ej. 'la proxima semana'), proponer la fecha habil mas proxima dentro de ese rango."
        },
        "hora_propuesta": {
          "type": "string",
          "description": "Hora propuesta en formato HH:MM (24h), zona horaria de UTPConsult. Vacio si el correo no especifica horario."
        },
        "duracion_minutos": {
          "type": "integer",
          "description": "Duracion estimada de la reunion en minutos. Usar 30 por defecto si no se especifica."
        },
        "agenda": {
          "type": "string",
          "description": "Temas a tratar en la reunion, extraidos del correo del cliente."
        },
        "es_tentativa": {
          "type": "boolean",
          "description": "Indica si la fecha/hora es una propuesta a confirmar (true) o fue solicitada de forma explicita y exacta por el cliente (false)."
        }
      },
      "required": ["titulo", "asistentes", "agenda", "es_tentativa"]
    }
  }
}
```

### 3.3 actualizar_contacto_en_crm

```json
{
  "type": "function",
  "function": {
    "name": "actualizar_contacto_en_crm",
    "description": "Crea o actualiza el registro de un contacto/prospecto en el CRM con la informacion mas reciente obtenida de la comunicacion con el cliente.",
    "parameters": {
      "type": "object",
      "properties": {
        "nombre_contacto": {
          "type": "string",
          "description": "Nombre completo de la persona de contacto."
        },
        "empresa": {
          "type": "string",
          "description": "Nombre de la empresa del cliente."
        },
        "correo_electronico": {
          "type": "string",
          "description": "Direccion de correo electronico del contacto."
        },
        "etapa_pipeline": {
          "type": "string",
          "enum": ["Prospecto", "Interesado", "Propuesta enviada", "Negociacion", "Cerrado-ganado", "Cerrado-perdido"],
          "description": "Etapa del embudo de ventas en la que se encuentra el contacto, segun el contenido del correo."
        },
        "interes_principal": {
          "type": "string",
          "description": "Producto, modulo o servicio de interes principal mencionado por el cliente."
        },
        "ultima_interaccion_resumen": {
          "type": "string",
          "description": "Resumen breve (1-2 lineas) del contenido del ultimo correo recibido, para contexto del equipo de ventas."
        },
        "documentos_adjuntos": {
          "type": "array",
          "items": { "type": "string" },
          "description": "Nombres de los archivos adjuntos recibidos en el correo, si los hay."
        }
      },
      "required": ["nombre_contacto", "empresa", "correo_electronico", "etapa_pipeline", "ultima_interaccion_resumen"]
    }
  }
}
```

### 3.4 enviar_notificacion_interna

```json
{
  "type": "function",
  "function": {
    "name": "enviar_notificacion_interna",
    "description": "Envia un mensaje de resumen al canal interno de Slack del equipo de gestion de proyectos y ventas, notificando las acciones ejecutadas por el asistente y cualquier pendiente que requiera atencion humana.",
    "parameters": {
      "type": "object",
      "properties": {
        "canal": {
          "type": "string",
          "description": "Nombre del canal de Slack destino (ej. '#ventasseguimiento')."
        },
        "resumen_ejecutivo": {
          "type": "string",
          "description": "Resumen de 2 a 3 lineas del correo procesado."
        },
        "acciones_realizadas": {
          "type": "array",
          "items": { "type": "string" },
          "description": "Lista de acciones ejecutadas automaticamente (ej. 'Tarea PAGOS-124 creada en Jira')."
        },
        "alertas": {
          "type": "array",
          "items": { "type": "string" },
          "description": "Lista de alertas o datos pendientes de confirmacion que requieren revision humana."
        },
        "nivel_urgencia": {
          "type": "string",
          "enum": ["Normal", "Alta", "Critica"],
          "description": "Nivel de urgencia de la notificacion."
        }
      },
      "required": ["canal", "resumen_ejecutivo", "acciones_realizadas", "nivel_urgencia"]
    }
  }
}
```

## 4. Diseño del Flujo de Interacción (Ciclo de un Run)

Correo de ejemplo, enviado por una clienta de la empresa TechCorp:

> De: Ana Torres <ana.torres@techcorp.com>
> Para: equipo@utpconsult.com
> Asunto: Re: Propuesta modulo de pagos
>
> Hola equipo de UTP Consult, gracias por la propuesta. Nos interesa avanzar. ¿Podríamos tener una reunión la próxima semana para discutir los detalles técnicos del módulo de pagos? Adjunto un documento con algunos requisitos iniciales.
>
> Saludos, Ana Torres de TechCorp.
> [Adjunto: requisitos_iniciales.pdf]

**Paso 1 — Recepción y normalización del mensaje.** Un conector de ingesta (webhook conectado a la bandeja de correo de UTPConsult) detecta el nuevo mensaje y lo normaliza: remitente, asunto, cuerpo, fecha y archivo adjunto. El backend consulta su base de datos interna para determinar si el correo ya está asociado a un thread_id existente o si debe crearse un nuevo Thread.

**Paso 2 — Adición del mensaje al Thread.** El backend agrega el contenido normalizado como un nuevo Message (rol "user"), incluyendo metadatos relevantes. El documento adjunto se sube como File y se vincula al Thread.

**Paso 3 — Creación del Run.** La aplicación crea un nuevo Run sobre el Thread, indicando el asistente "UTP Assistant" (system prompt + funciones registradas). El Run inicia en estado queued y pasa a in_progress.

**Paso 4 — Razonamiento y extracción de información.** El modelo analiza el correo y extrae: remitente (Ana Torres), empresa (TechCorp), intención positiva de avanzar, solicitud de reunión "la próxima semana", y adjunto con requisitos. Como la fecha exacta no está especificada, el modelo la marca como dato tentativo.

**Paso 5 — Transición a requires_action.** El estado cambia a requires_action, con tool_calls:

1. `actualizar_contacto_en_crm` — nombre_contacto: "Ana Torres"; empresa: "TechCorp"; etapa_pipeline: "Negociación"; interes_principal: "Módulo de pagos"; ultima_interaccion_resumen: "..."; documentos_adjuntos: ["requisitos_iniciales.pdf"].
2. `crear_tarea_en_jira` — proyecto_key: "PAGOS"; titulo: "Revisar requisitos iniciales de TechCorp para el módulo de pagos"; prioridad: "Alta"; cliente_relacionado: "TechCorp".
3. `agendar_reunion_en_google_calendar` — titulo: "Reunión técnica – TechCorp – Módulo de pagos"; fecha_propuesta: fecha hábil más próxima dentro de la semana siguiente; es_tentativa: true.

**Paso 6 — Ejecución teórica de las funciones.** La aplicación (no el modelo) valida los parámetros y ejecuta las llamadas reales a las APIs externas. Cada sistema devuelve un identificador de confirmación (ej. ticket "PAGOS-124").

**Paso 7 — Envío de resultados al Run (submit_tool_outputs).** El backend invoca submit_tool_outputs devolviendo para cada tool_call_id el resultado. El Run vuelve a in_progress.

**Paso 8 — Finalización del Run.** Con todos los tool_outputs resueltos el Run pasa a completed y el modelo redacta el mensaje final (resumen ejecutivo, acciones ejecutadas, pendientes/alertas). Opcionalmente se envía como notificación al canal de Slack.

## 5. Consideraciones de Riesgo y Ética

### Riesgo 1 — Alucinaciones o extracción incorrecta de datos

El modelo podría inferir fechas, nombres o compromisos no mencionados explícitamente, o interpretar erróneamente la intención del cliente.

**Estrategias de mitigación**
- Diseño del prompt: reglas explícitas que prohíben inventar datos y obligan a marcar los campos faltantes como "PENDIENTE DE CONFIRMACIÓN".
- Validación estructural: JSON Schema con campos required y restricciones enum.
- Punto de control humano: toda acción con es_tentativa = true se ejecuta como propuesta, no como confirmación.
- Trazabilidad: cada dato extraído cita su origen (correo y fecha).
- Monitoreo continuo: revisión periódica, por muestreo, de un porcentaje de los Runs completados.

### Riesgo 2 — Seguridad y privacidad de la información del cliente

Los correos y documentos adjuntos pueden contener datos personales, información comercial sensible o confidencial.

**Estrategias de mitigación**
- Minimización de datos: enviar al modelo solo lo estrictamente necesario.
- Cifrado y control de acceso: cifrado en tránsito y en reposo; credenciales en variables de entorno o gestor de secretos, nunca expuestas al modelo.
- Cuenta empresarial con política de retención configurada.
- Filtrado previo de datos altamente sensibles (anonimización/redacción).
- Control de acceso basado en roles y auditoría.

## 6. Referencias

- OpenAI — API Reference (Chat Completions): https://platform.openai.com/docs/api-reference/chat
- OpenAI — API Reference (Audio Transcriptions): https://platform.openai.com/docs/api-reference/audio/createTranscription
- Streamlit — Chat Elements: https://docs.streamlit.io/develop/api-reference/chat
- Streamlit — Session State: https://docs.streamlit.io/develop/api-reference/caching-and-state/st.session_state
- Streamlit — File Uploader: https://docs.streamlit.io/develop/api-reference/widgets/st.file_uploader