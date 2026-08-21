# tests/conftest.py
#
# Configura variáveis de ambiente ANTES de qualquer import de bot.*, já que
# bot/core/settings.py valida essas variáveis assim que é importado.

import os

os.environ.setdefault("TELEGRAM_TOKEN", "test-token")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("ADMIN_USER_IDS", "111")

import pytest

from bot.db.base import Base, engine, SessionLocal
from bot.services import user_service


@pytest.fixture()
def db():
    """Sessão de banco isolada por teste (SQLite em memória; tabelas limpas ao final)."""
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        with engine.begin() as conn:
            for table in reversed(Base.metadata.sorted_tables):
                conn.execute(table.delete())


@pytest.fixture()
def user(db):
    """Um usuário já cadastrado, pronto para ser dono de matérias/atividades/etc nos testes."""
    db_user, _ = user_service.get_or_create_user(db, 12345, "Ana", "ana_tg")
    return db_user
