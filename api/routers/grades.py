# api/routers/grades.py

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.deps import get_current_user, get_db
from api.schemas import GradeOut
from bot.db.models import User
from bot.services import grade_service

router = APIRouter(prefix="/grades", tags=["grades"])


@router.get("", response_model=List[GradeOut])
async def list_grades(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list:
    """Lista todas as notas lançadas pelo usuário (todas as matérias)."""
    grades = grade_service.get_grades_by_user(db, user)

    return [
        GradeOut(
            id=g.id,
            name=g.name,
            value=g.value,
            subject_id=g.subject_id,
            subject_name=g.subject.name,
        )
        for g in grades
    ]
