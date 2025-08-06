from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from bot.core.settings import DATABASE_URL

# O 'engine' é o ponto de entrada para o banco de dados.
# Ele gerencia as conexões. O pool_pre_ping=True verifica as conexões antes de usá-las.
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# A 'SessionLocal' é uma fábrica de sessões. Cada instância dela será uma "conversa"
# com o banco de dados.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# A 'Base' é uma classe base da qual todos os nossos modelos de tabela (como Usuario)
# irão herdar.
Base = declarative_base()