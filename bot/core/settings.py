# bot/core/settings.py

import os
from dotenv import load_dotenv

load_dotenv()

# --- Configurações do Telegram ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise ValueError("Variável de ambiente TELEGRAM_TOKEN não encontrada.")

# --- Configurações do Banco de Dados (PostgreSQL) ---
# Lógica flexível: Se a DATABASE_URL existe (como na Render/Railway), use-a.
# Senão, monte-a a partir das variáveis individuais (para desenvolvimento local).
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # Este bloco só é executado em ambiente local (sem DATABASE_URL)
    
    # Define as variáveis necessárias para o ambiente local
    required_vars = {
        "DB_USER": os.getenv("DB_USER"),
        "DB_PASSWORD": os.getenv("DB_PASSWORD"),
        "DB_HOST": os.getenv("DB_HOST"),
        "DB_PORT": os.getenv("DB_PORT"),
        "DB_NAME": os.getenv("DB_NAME"),
    }

    # Verifica quais variáveis estão faltando
    missing_vars = [key for key, value in required_vars.items() if not value]

    # Se a lista de variáveis faltando não estiver vazia, lança um erro específico
    if missing_vars:
        raise ValueError(
            "Variáveis de ambiente locais não encontradas: "
            f"{', '.join(missing_vars)}"
        )
    
    # Se todas as variáveis locais existem, monta a URL de conexão
    DATABASE_URL = (
        f"postgresql://{required_vars['DB_USER']}:{required_vars['DB_PASSWORD']}@"
        f"{required_vars['DB_HOST']}:{required_vars['DB_PORT']}/{required_vars['DB_NAME']}"
    )