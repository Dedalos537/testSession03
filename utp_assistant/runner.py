"""Runner: ciclo de un Run de "UTP Assistant" sobre la API de Groq.

Replica manualmente el ciclo que el diseno describe para la Assistants API:
queued -> in_progress -> requires_action (la app ejecuta las funciones)
-> submit_tool_outputs (se reenvian los resultados) -> completed.

Groq NO ofrece Assistants API, por eso aqui se orquesta con Chat Completions
+ Local Tool Calling.
"""

from __future__ import annotations

import json
import time
import uuid
from collections.abc import Callable
from typing import Any

from groq import BadRequestError, Groq
from groq._exceptions import RateLimitError
from groq.types.chat import ChatCompletionMessage  # noqa: F401  (tipado)

from . import db
from .config import MODEL, require_api_key
from .services import calendar, crm, jira, slack
from .system_prompt import SYSTEM_PROMPT
from .tools import ORDER, TOOLS

TEMPERATURE = 0.2
MAX_TOKENS = 4096
MAX_ATTEMPTS = 4
MAX_ROUNDS = 4
MAX_CORRECTIVOS = 2

REGISTRY: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    "actualizar_contacto_en_crm": crm.upsert_contact,
    "crear_tarea_en_jira": jira.create_task,
    "agendar_reunion_en_google_calendar": calendar.create_event,
    "enviar_notificacion_interna": slack.send_notification,
}

_ORDER_INDEX = {name: i for i, name in enumerate(ORDER)}


def make_client() -> Groq:
    return Groq(api_key=require_api_key())


def _tool_use_failed(exc: BadRequestError) -> bool:
    mensaje = str(exc)
    return "tool_use_failed" in mensaje or "did not match schema" in mensaje


def _chat_tool_round(client: Groq, messages: list[dict[str, Any]]) -> Any:
    """Ronda de tool calling con correctivo: si el modelo emite funciones con
    parametros invalidos (Groq responde 400), se le pide corregir y se reintenta.

    Mismo numero de intentos en total (correctivos de adopcion del modelo).
    """
    intentos = MAX_CORRECTIVOS + 1
    ultimo: Exception | None = None
    for intento in range(intentos):
        try:
            return _chat(client, messages=messages, tools=TOOLS, tool_choice="auto")
        except BadRequestError as exc:
            if not _tool_use_failed(exc):
                raise
            ultimo = exc
            if intento < intentos - 1:
                messages.append({
                    "role": "user",
                    "content": (
                        "Corrige las llamadas a funciones: todos los parametros deben cumplir el "
                        "esquema definido. No uses null; si un dato falta usa el texto "
                        "'PENDIENTE DE CONFIRMACION' y en booleanos el valor explicito. "
                        "Respeta los enumerados indicados."
                    ),
                })
    raise ultimo  # type: ignore[misc]


def _is_rate_limit(exc: Exception) -> bool:
    try:
        if isinstance(exc, RateLimitError):
            return True
    except TypeError:  # pragma: no cover - version sin tipo
        pass
    return getattr(exc, "status_code", None) == 429


def _chat(
    client: Groq,
    *,
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]] | None = None,
    tool_choice: str | None = None,
) -> Any:
    """Wrapper con retry exponencial ante rate limits (429)."""
    kwargs: dict[str, Any] = {
        "model": MODEL,
        "messages": messages,
        "temperature": TEMPERATURE,
        "max_completion_tokens": MAX_TOKENS,
    }
    if tools is not None:
        kwargs["tools"] = tools
    if tool_choice is not None:
        kwargs["tool_choice"] = tool_choice

    attempt = 0
    while True:
        try:
            return client.chat.completions.create(**kwargs)
        except Exception as exc:
            attempt += 1
            if _is_rate_limit(exc) and attempt < MAX_ATTEMPTS:
                time.sleep(min(2**attempt, 30))
                continue
            raise


def _tool_calls_payload(tool_calls: list[Any]) -> list[dict[str, Any]]:
    return [
        {
            "id": tc.id,
            "type": "function",
            "function": {"name": tc.function.name, "arguments": tc.function.arguments},
        }
        for tc in tool_calls
    ]


def dispatch(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Ejecuta la funcion (implementacion local = "soa externa" simulada)."""
    fn = REGISTRY.get(name)
    if fn is None:
        return {"ok": False, "error": f"funcion '{name}' no registrada"}
    try:
        return fn(arguments)
    except TypeError as exc:
        return {"ok": False, "error": f"parametros invalidos para '{name}': {exc}"}


def _build_messages(thread_id: int, db_path: Any = None) -> list[dict[str, Any]]:
    history = db.get_thread_messages(thread_id, db_path)
    return [{"role": "system", "content": SYSTEM_PROMPT}] + [
        {"role": m["role"], "content": m["content"]} for m in history
    ]


def email_to_user_message(email: dict[str, Any]) -> str:
    """Normaliza un correo como Message rol 'user' (equivalente al Paso 2 del diseno)."""
    adjuntos = ", ".join(email.get("adjuntos", [])) or "ninguno"
    return (
        f"[EMAIL ID: {email['id']}]\n"
        f"De: {email['remitente']}\n"
        f"Fecha: {email['fecha']}\n"
        f"Asunto: {email['asunto']}\n"
        f"Adjuntos: {adjuntos}\n"
        f"Cuerpo:\n{email['cuerpo']}\n"
    )


def add_email_to_thread(email: dict[str, Any], db_path: Any = None) -> int:
    """Añade el correo como mensaje 'user' del thread (idempotente por EMAIL ID)."""
    thread_id = int(email["thread_id"])
    marker = f"[EMAIL ID: {email['id']}]"
    existente = any(marker in m["content"] for m in db.get_thread_messages(thread_id, db_path))
    if not existente:
        return db.add_message(thread_id, "user", email_to_user_message(email), db_path)
    return -1


def run_assistant(thread_id: int, client: Groq | None = None, db_path: Any = None) -> dict[str, Any]:
    """Ejecuta un Run completo sobre el thread indicado.

    Devuelve: {thread_id, run_id, estado, resumen_final, tool_calls}

    El asistente puede pedir funciones en varias rondas (los modelos pueden
    repartir las acciones del correo en distintos turnos). Se limita a
    ``MAX_ROUNDS``; si aun asi nunca produce texto, se entrega un resumen
    determinista con los resultados ya ejecutados.
    """
    if client is None:
        client = make_client()

    messages = _build_messages(thread_id, db_path)
    run_id = f"run_{uuid.uuid4().hex[:10]}"

    executed: list[dict[str, Any]] = []
    ejecutadas: set[str] = set()
    final_text: str | None = None
    modelo_invalido = False

    for _ in range(MAX_ROUNDS):
        try:
            first = _chat_tool_round(client, messages)
        except BadRequestError:
            # el modelo no logro emitir tool_calls validas ni aun con correctivos:
            # se cierra el Run con resumen determinista de lo ya ejecutado
            modelo_invalido = True
            break
        msg = first.choices[0].message

        if not msg.tool_calls:
            final_text = msg.content or "Procesamiento completado (sin resumen de texto del modelo)."
            break

        # requires_action: el arreglo tool_calls llega a la app (no al modelo)
        messages.append({
            "role": "assistant",
            "content": msg.content or "",
            "tool_calls": _tool_calls_payload(msg.tool_calls),
        })

        tool_calls = sorted(msg.tool_calls, key=lambda tc: _ORDER_INDEX.get(tc.function.name, 99))
        nuevas = 0
        for tc in tool_calls:
            name = tc.function.name
            try:
                arguments = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                arguments = {}

            # dedupe: una funcion por Run (algunas modelos repiten llamadas ya hechas)
            if name in ejecutadas:
                out = {"ok": True, "info": f"{name} ya fue ejecutada en este run; sin duplicar."}
            else:
                ejecutadas.add(name)
                nuevas += 1
                out = dispatch(name, arguments)
            executed.append({"name": name, "arguments": arguments, "output": out})
            # submit_tool_outputs equivalente: un mensaje 'tool' por tool_call_id
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(out, ensure_ascii=False),
            })

        # la ronda no aporto acciones nuevas: no pedir otra ronda al modelo
        if nuevas == 0:
            break

    if final_text is None:
        if modelo_invalido:
            final_text = (
                "El modelo no pudo completar el resumen en texto, pero las acciones "
                "solicitadas fueron ejecutadas.\n"
            ) + resumen_determinista(executed)
        else:
            final_text = resumen_determinista(executed)

    # completed: se persiste la respuesta final del asistente en el thread
    db.add_message(thread_id, "assistant", final_text, db_path)

    return {
        "thread_id": thread_id,
        "run_id": run_id,
        "estado": "completed",
        "resumen_final": final_text,
        "tool_calls": executed,
    }


def resumen_determinista(executed: list[dict[str, Any]]) -> str:
    """Resumen de respaldo (sin modelo) a partir de los resultados ejecutados."""
    if not executed:
        return "Sin accion requerida."
    lines = [f"Procesamiento completado. Acciones ejecutadas ({len(executed)}):"]
    for tc in executed:
        out = tc["output"]
        estado = "OK" if out.get("ok") else "ERROR"
        lines.append(f"- {tc['name']}: {estado} -> {json.dumps(out, ensure_ascii=False)}")
    return "\n".join(lines)


def process_email(email: dict[str, Any], client: Groq | None = None, db_path: Any = None) -> dict[str, Any]:
    """Procesa un correo pendiente: lo añade al thread, ejecuta el Run y lo marca procesado."""
    thread_id = int(email["thread_id"])
    add_email_to_thread(email, db_path)
    result = run_assistant(thread_id, client=client, db_path=db_path)
    db.mark_email_processed(email["id"], result["run_id"], db_path)
    return result