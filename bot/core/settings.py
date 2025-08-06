import os
from dotenv import load_dotenv

load_dotenv()

# --- Configurações do Telegram ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# --- Configurações do Banco de Dados (PostgreSQL) ---
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

# URL de conexão para o SQLAlchemy
# Formato: postgresql://usuario:senha@host:porta/nomedobanco
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Validação simples para garantir que o token foi carregado
if not TELEGRAM_TOKEN:
    raise ValueError("O TELEGRAM_TOKEN não foi encontrado. Verifique seu arquivo .env")