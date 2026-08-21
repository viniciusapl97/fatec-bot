# api/deps.py
#
# Dependências compartilhadas pelos endpoints: sessão de banco e autenticação
# via token de acesso pessoal (gerado pelo bot com /tokendeacesso).

from typing import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from bot.db.base import SessionLocal
from bot.db.models import Subject, User
from bot.services import access_token_service, subject_service

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


def get_owned_subject(db: Session, subject_id: int, user: User) -> Subject:
    """
    Busca uma matéria garantindo que pertence ao usuário do token; 404 (não
    403) tanto se ela não existir quanto se for de outro usuário, pra não
    vazar quais IDs existem. Usado por qualquer endpoint que recebe um
    subject_id (na URL ou no corpo) e precisa validar posse antes de agir.
    """
    subject = subject_service.get_subject_by_id(db, subject_id)
    if not subject or subject.user_id != user.user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Matéria não encontrada.")
    return subject
