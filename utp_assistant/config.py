"""Configuracion central del proyecto.

La API key de Groq NUNCA debe hardcodearse: se lee desde variables de entorno
(.env), gestionada con python-dotenv.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
MODEL = os.getenv("MODEL", "openai/gpt-oss-120b")
DB_PATH = Path(os.getenv("DB_PATH", str(Path(__file__).resolve().parent / "utp_assistant.db")))

# Modelos con soporte de tool calling disponibles en esta cuenta de Groq
MODEL_OPTIONS = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "qwen/qwen3.8-27b",
]


def require_api_key() -> str:
    """Devuelve la API key o lanza un error claro si no esta configurada."""
    if not GROQ_API_KEY:
        raise RuntimeError(
            "GROQ_API_KEY no configurada. Copia .env.example a .env y agrega tu key de Groq."
        )
    return GROQ_API_KEY