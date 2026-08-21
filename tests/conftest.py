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


@pytest.fixture(scope="session", autouse=True)
def _create_tables():
    """
    Cria as tabelas uma vez por sessão de testes, antes de qualquer teste
    rodar — inclusive os que não usam a fixture `db` (ex.: testes de API que
    só checam autenticação, sem precisar inserir dados). Sem isso, um teste
    desses rodando sozinho (ou antes de qualquer outro que use `db`) bate
    num banco sem tabela nenhuma.
    """
    Base.metadata.create_all(bind=engine)


@pytest.fixture()
def db():
    """Sessão de banco isolada por teste (SQLite em memória; tabelas limpas ao final)."""
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
