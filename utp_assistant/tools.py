"""Definicion de herramientas (function calling) de "UTP Assistant".

Esquemas en formato JSON Schema (seccion 3 de la propuesta de diseno), tal como
se pasan al parametro ``tools`` de la API de Groq. Aqui solo se define el
contrato; la implementacion de cada sistema externo esta en ``services/``.
"""

CREAR_TAREA_EN_JIRA = {
    "type": "function",
    "function": {
        "name": "crear_tarea_en_jira",
        "description": (
            "Crea una nueva tarea (issue) en el proyecto correspondiente de Jira a partir de "
            "un requerimiento identificado en el correo de un cliente. Se usa cuando el mensaje "
            "describe una accion de trabajo pendiente para el equipo (preparar una propuesta, "
            "resolver una duda tecnica, dar seguimiento a un modulo, etc.)."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "proyecto_key": {
                    "type": "string",
                    "description": (
                        "Codigo del proyecto en Jira al que pertenece la tarea (ej. 'CRM', "
                        "'PAGOS'). Usar 'GENERAL' si no se puede determinar con certeza."
                    ),
                },
                "titulo": {
                    "type": "string",
                    "description": (
                        "Titulo breve y accionable de la tarea, en modo imperativo (ej. "
                        "'Preparar propuesta tecnica del modulo de pagos')."
                    ),
                },
                "descripcion": {
                    "type": "string",
                    "description": (
                        "Descripcion detallada de la tarea, incluyendo el contexto extraido del "
                        "correo del cliente."
                    ),
                },
                "prioridad": {
                    "type": "string",
                    "enum": ["Baja", "Media", "Alta", "Urgente"],
                    "description": "Prioridad estimada segun la urgencia expresada por el cliente en el correo.",
                },
                "cliente_relacionado": {
                    "type": "string",
                    "description": "Nombre de la empresa o del contacto del cliente asociado a la tarea.",
                },
                "fecha_limite": {
                    "type": "string",
                    "description": (
                        "Fecha limite sugerida en formato YYYY-MM-DD, solo si se menciona o se "
                        "puede inferir explicitamente del correo."
                    ),
                },
            },
            "required": ["proyecto_key", "titulo", "descripcion", "cliente_relacionado"],
        },
    },
}

AGENDAR_REUNION_EN_GOOGLE_CALENDAR = {
    "type": "function",
    "function": {
        "name": "agendar_reunion_en_google_calendar",
        "description": (
            "Crea una propuesta de evento en Google Calendar para dar seguimiento a una solicitud "
            "de reunion de un cliente. Se usa cuando el correo solicita explicitamente coordinar "
            "una llamada o reunion."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "titulo": {
                    "type": "string",
                    "description": (
                        "Titulo del evento (ej. 'Reunion de seguimiento - TechCorp - Modulo de pagos')."
                    ),
                },
                "asistentes": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Lista de correos electronicos de los asistentes internos y externos a invitar.",
                },
                "fecha_propuesta": {
                    "type": "string",
                    "description": (
                        "Fecha propuesta en formato YYYY-MM-DD. Si el cliente solo indica un rango "
                        "(ej. 'la proxima semana'), proponer la fecha habil mas proxima dentro de ese rango."
                    ),
                },
                "hora_propuesta": {
                    "type": "string",
                    "description": (
                        "Hora propuesta en formato HH:MM (24h), zona horaria de UTPConsult. Vacio si "
                        "el correo no especifica horario."
                    ),
                },
                "duracion_minutos": {
                    "type": "integer",
                    "description": "Duracion estimada de la reunion en minutos. Usar 30 por defecto si no se especifica.",
                },
                "agenda": {
                    "type": "string",
                    "description": "Temas a tratar en la reunion, extraidos del correo del cliente.",
                },
                "es_tentativa": {
                    "type": "boolean",
                    "description": (
                        "Indica si la fecha/hora es una propuesta a confirmar (true) o fue solicitada "
                        "de forma explicita y exacta por el cliente (false)."
                    ),
                },
            },
            "required": ["titulo", "asistentes", "agenda", "es_tentativa"],
        },
    },
}

ACTUALIZAR_CONTACTO_EN_CRM = {
    "type": "function",
    "function": {
        "name": "actualizar_contacto_en_crm",
        "description": (
            "Crea o actualiza el registro de un contacto/prospecto en el CRM con la informacion mas "
            "reciente obtenida de la comunicacion con el cliente."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "nombre_contacto": {
                    "type": "string",
                    "description": "Nombre completo de la persona de contacto.",
                },
                "empresa": {
                    "type": "string",
                    "description": "Nombre de la empresa del cliente.",
                },
                "correo_electronico": {
                    "type": "string",
                    "description": "Direccion de correo electronico del contacto.",
                },
                "etapa_pipeline": {
                    "type": "string",
                    "enum": [
                        "Prospecto",
                        "Interesado",
                        "Propuesta enviada",
                        "Negociacion",
                        "Cerrado-ganado",
                        "Cerrado-perdido",
                    ],
                    "description": "Etapa del embudo de ventas en la que se encuentra el contacto, segun el contenido del correo.",
                },
                "interes_principal": {
                    "type": "string",
                    "description": "Producto, modulo o servicio de interes principal mencionado por el cliente.",
                },
                "ultima_interaccion_resumen": {
                    "type": "string",
                    "description": "Resumen breve (1-2 lineas) del contenido del ultimo correo recibido, para contexto del equipo de ventas.",
                },
                "documentos_adjuntos": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Nombres de los archivos adjuntos recibidos en el correo, si los hay.",
                },
            },
            "required": [
                "nombre_contacto",
                "empresa",
                "correo_electronico",
                "etapa_pipeline",
                "ultima_interaccion_resumen",
            ],
        },
    },
}

ENVIAR_NOTIFICACION_INTERNA = {
    "type": "function",
    "function": {
        "name": "enviar_notificacion_interna",
        "description": (
            "Envia un mensaje de resumen al canal interno de Slack del equipo de gestion de proyectos "
            "y ventas, notificando las acciones ejecutadas por el asistente y cualquier pendiente que "
            "requiera atencion humana."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "canal": {
                    "type": "string",
                    "description": "Nombre del canal de Slack destino (ej. '#ventasseguimiento').",
                },
                "resumen_ejecutivo": {
                    "type": "string",
                    "description": "Resumen de 2 a 3 lineas del correo procesado.",
                },
                "acciones_realizadas": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Lista de acciones ejecutadas automaticamente (ej. 'Tarea PAGOS-124 creada en Jira').",
                },
                "alertas": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Lista de alertas o datos pendientes de confirmacion que requieren revision humana.",
                },
                "nivel_urgencia": {
                    "type": "string",
                    "enum": ["Normal", "Alta", "Critica"],
                    "description": "Nivel de urgencia de la notificacion.",
                },
            },
            "required": ["canal", "resumen_ejecutivo", "acciones_realizadas", "nivel_urgencia"],
        },
    },
}

TOOLS = [
    ACTUALIZAR_CONTACTO_EN_CRM,
    CREAR_TAREA_EN_JIRA,
    AGENDAR_REUNION_EN_GOOGLE_CALENDAR,
    ENVIAR_NOTIFICACION_INTERNA,
]

ORDER = [
    "actualizar_contacto_en_crm",
    "crear_tarea_en_jira",
    "agendar_reunion_en_google_calendar",
    "enviar_notificacion_interna",
]