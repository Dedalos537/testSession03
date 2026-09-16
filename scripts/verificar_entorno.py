import importlib.util
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

mods = ["openai", "streamlit", "dotenv"]
print("VERIFICACION DEL ENTORNO - SEMANA 06")
print("=" * 45)
for name in mods:
    ok = importlib.util.find_spec(name) is not None
    print(f"{name:12} : {'OK' if ok else 'FALTA'}")
print(f"GROQ_API_KEY : {'CONFIGURADA' if os.getenv('GROQ_API_KEY') else 'NO CONFIGURADA'}")
