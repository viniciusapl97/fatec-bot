# api/routers/me.py

from fastapi import APIRouter, Depends

from api.deps import get_current_user
from api.schemas import UserOut
from bot.db.models import User

router = APIRouter(tags=["me"])


@router.get("/me", response_model=UserOut)
async def read_me(user: User = Depends(get_current_user)) -> User:
    """Retorna os dados do usuário dono do token de acesso usado na requisição."""
    return user
