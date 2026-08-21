# bot/services/access_token_service.py

import hashlib
import secrets
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from bot.db.models import AccessToken, User


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


def create_access_token(db: Session, user: User) -> str:
    """
    Gera um novo token de acesso pessoal para o usuário (ex.: pro app/API) e
    retorna o valor em texto puro. Esse valor só existe aqui — o banco guarda
    só o hash, então não tem como recuperá-lo depois; se perder, gera outro.
    """
    token = secrets.token_urlsafe(32)
    db_token = AccessToken(
        token_hash=_hash_token(token),
        owner=user,
        created_at=datetime.now(timezone.utc),
    )
    db.add(db_token)
    db.commit()
    return token


def get_user_by_token(db: Session, token: str) -> User | None:
    """Valida um token de acesso e retorna o usuário dono dele, ou None se for inválido."""
    db_token = db.query(AccessToken).filter(AccessToken.token_hash == _hash_token(token)).first()
    if not db_token:
        return None
    db_token.last_used_at = datetime.now(timezone.utc)
    db.commit()
    return db_token.owner


def revoke_all_access_tokens(db: Session, user: User) -> int:
    """Revoga (apaga) todos os tokens de acesso do usuário. Retorna quantos foram removidos."""
    count = db.query(AccessToken).filter(AccessToken.user_id == user.user_id).delete()
    db.commit()
    return count
