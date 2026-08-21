# api/routers/subjects.py

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.deps import get_current_user, get_db
from api.schemas import SubjectOut
from bot.db.models import User
from bot.services import subject_service

router = APIRouter(prefix="/subjects", tags=["subjects"])


@router.get("", response_model=List[SubjectOut])
async def list_subjects(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list:
    """Lista as matérias do usuário dono do token, ordenadas por dia/horário (mesma lógica do /grade)."""
    return subject_service.get_subjects_by_user(db, user)
