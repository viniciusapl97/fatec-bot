# bot/core/settings.py

import os
from dotenv import load_dotenv

load_dotenv()

# --- Configurações do Telegram ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise ValueError("O TELEGRAM_TOKEN não foi encontrado. Verifique suas variáveis de ambiente.")

# --- Configurações do Banco de Dados (PostgreSQL) ---
# Lógica flexível: Se a DATABASE_URL existe (como na Render), use-a.
# Senão, monte-a a partir das variáveis individuais (para desenvolvimento local).
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT")
    DB_NAME = os.getenv("DB_NAME")

    # Valida se todas as variáveis do banco existem para o ambiente local
    if not all([DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME]):
        raise ValueError("Uma ou mais variáveis de banco de dados (DB_*) não foram encontradas para o ambiente local.")

    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"