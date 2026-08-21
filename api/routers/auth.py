# api/routers/auth.py
#
# Login pro site via Telegram Login Widget — diferente do token de acesso
# pessoal (/tokendeacesso no bot), que é pro app/uso pessoal. Ver
# docs/specs/frontend-web-and-app.md e docs/specs/api-design.md.

import hashlib
import hmac
import time

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.deps import get_db
from api.schemas import AccessTokenOut, TelegramLoginPayload
from bot.core.settings import TELEGRAM_TOKEN
from bot.services import access_token_service, user_service

router = APIRouter(prefix="/auth", tags=["auth"])

# O widget gera o payload no momento do clique; uma janela de 24h absorve
# atraso de rede/relógio sem deixar um link de login velho válido pra sempre.
TELEGRAM_AUTH_MAX_AGE_SECONDS = 24 * 60 * 60


def _verify_telegram_login(payload: TelegramLoginPayload) -> None:
    """
    Confere a assinatura do Telegram Login Widget — ver
    https://core.telegram.org/widgets/login#checking-authorization.
    A "data-check-string" é todo campo do payload (exceto `hash`, e exceto os
    que vieram None) como "chave=valor", ordenado por chave e unido por \\n;
    o hash esperado é HMAC-SHA256 dessa string usando SHA256(TELEGRAM_TOKEN)
    como chave.
    """
    data = payload.model_dump(exclude={"hash"}, exclude_none=True)
    data_check_string = "\n".join(f"{key}={data[key]}" for key in sorted(data))
    secret_key = hashlib.sha256(TELEGRAM_TOKEN.encode("utf-8")).digest()
    computed_hash = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(computed_hash, payload.hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Assinatura do Telegram inválida.")

    if time.time() - payload.auth_date > TELEGRAM_AUTH_MAX_AGE_SECONDS:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Login do Telegram expirado, tente novamente.")


@router.post("/telegram", response_model=AccessTokenOut)
async def login_with_telegram(
    payload: TelegramLoginPayload,
    db: Session = Depends(get_db),
) -> AccessTokenOut:
    """
    Valida o payload assinado do Telegram Login Widget e emite um token de
    acesso pro usuário — o mesmo mecanismo do AccessToken usado pelo app
    (/tokendeacesso no bot), só que emitido automaticamente aqui em vez de
    manualmente. O site guarda esse token e autentica como qualquer outro
    cliente da API (`Authorization: Bearer <token>`).
    """
    _verify_telegram_login(payload)

    user, _ = user_service.get_or_create_user(db, payload.id, payload.first_name, payload.username)
    token = access_token_service.create_access_token(db, user)
    return AccessTokenOut(access_token=token)
