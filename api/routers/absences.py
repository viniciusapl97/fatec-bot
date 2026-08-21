# api/routers/absences.py

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.deps import get_current_user, get_db
from api.schemas import AbsenceOut
from bot.db.models import User
from bot.services import absence_service

router = APIRouter(prefix="/absences", tags=["absences"])


@router.get("", response_model=List[AbsenceOut])
async def list_absences(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list:
    """Lista todos os registros de falta do usuário (todas as matérias), mais recentes primeiro."""
    absences = absence_service.get_absences_by_user(db, user)

    return [
        AbsenceOut(
            id=a.id,
            absence_date=a.absence_date,
            quantity=a.quantity,
            notes=a.notes,
            subject_id=a.subject_id,
            subject_name=a.subject.name,
        )
        for a in absences
    ]
