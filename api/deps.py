# api/deps.py
#
# Dependências compartilhadas pelos endpoints: sessão de banco e autenticação
# via token de acesso pessoal (gerado pelo bot com /tokendeacesso).

from typing import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from bot.db.base import SessionLocal
from bot.db.models import User
from bot.services import access_token_service

bearer_scheme = HTTPBearer(auto_error=True)


def get_db() -> Generator[Session, None, None]:
    """Uma sessão de banco por requisição, fechada ao final mesmo se der erro."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Resolve o usuário dono do token enviado em `Authorization: Bearer <token>`.
    Gere um token com /tokendeacesso no bot.
    """
    user = access_token_service.get_user_by_token(db, credentials.credentials)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de acesso inválido ou revogado.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
