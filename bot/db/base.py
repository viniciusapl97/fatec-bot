from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import StaticPool

from bot.core.settings import DATABASE_URL

# O 'engine' é o ponto de entrada para o banco de dados.
# Ele gerencia as conexões. O pool_pre_ping=True verifica as conexões antes de usá-las.
_engine_kwargs = {"pool_pre_ping": True}
if DATABASE_URL.startswith("sqlite"):
    # SQLite em memória (usado nos testes) cria um banco NOVO e vazio por thread
    # por padrão. Isso quebra testes que batem na API via TestClient, já que o
    # FastAPI roda a aplicação numa thread separada da do teste. StaticPool faz
    # todo mundo reusar a mesma conexão/banco, independente da thread; é a
    # correção padrão documentada pelo próprio FastAPI para esse cenário. Só se
    # aplica a SQLite — não afeta o Postgres usado em produção.
    _engine_kwargs["poolclass"] = StaticPool
    _engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **_engine_kwargs)

# A 'SessionLocal' é uma fábrica de sessões. Cada instância dela será uma "conversa"
# com o banco de dados.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# A 'Base' é uma classe base da qual todos os nossos modelos de tabela (como Usuario)
# irão herdar.
Base = declarative_base()