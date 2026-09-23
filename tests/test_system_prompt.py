"""Tests del system prompt: verifican que las reglas clave del diseno siguen presentes."""

from utp_assistant.system_prompt import KEYWORDS_REQUIRED, SYSTEM_PROMPT

SECCIONES = [
    "IDENTIDAD Y ROL",
    "OBJETIVOS",
    "REGLAS DE COMPORTAMIENTO",
    "TONO",
    "FORMATO DE SALIDA",
]


def test_prompt_contiene_todas_las_secciones():
    for seccion in SECCIONES:
        assert seccion in SYSTEM_PROMPT


def test_prompt_contiene_keywords_criticas():
    for keyword in KEYWORDS_REQUIRED:
        assert keyword in SYSTEM_PROMPT


def test_prompt_declara_orden_logico_de_ejecucion():
    idx_crm = SYSTEM_PROMPT.index("actualizar_contacto_en_crm")
    idx_jira = SYSTEM_PROMPT.index("crear_tarea_en_jira")
    idx_cal = SYSTEM_PROMPT.index("agendar_reunion_en_google_calendar")
    idx_slack = SYSTEM_PROMPT.index("enviar_notificacion_interna")
    assert idx_crm < idx_jira < idx_cal < idx_slack