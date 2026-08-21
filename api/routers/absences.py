# api/routers/absences.py

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.deps import get_current_user, get_db, get_owned_subject
from api.schemas import AbsenceCreate, AbsenceOut, AbsenceUpdate
from bot.db.models import Absence, User
from bot.services import absence_service

router = APIRouter(prefix="/absences", tags=["absences"])


def _to_out(a: Absence) -> AbsenceOut:
    return AbsenceOut(
        id=a.id,
        absence_date=a.absence_date,
        quantity=a.quantity,
        notes=a.notes,
        subject_id=a.subject_id,
        subject_name=a.subject.name,
    )


def _get_own_absence_or_404(db: Session, absence_id: int, user: User) -> Absence:
    absence = absence_service.get_absence_by_id(db, absence_id)
    if not absence or absence.user_id != user.user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Falta não encontrada.")
    return absence


@router.get("", response_model=List[AbsenceOut])
async def list_absences(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list:
    """Lista todos os registros de falta do usuário (todas as matérias), mais recentes primeiro."""
    absences = absence_service.get_absences_by_user(db, user)
    return [_to_out(a) for a in absences]


@router.post("", response_model=AbsenceOut, status_code=status.HTTP_201_CREATED)
async def create_absence(
    payload: AbsenceCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AbsenceOut:
    """Registra uma falta (mesma lógica do /faltei) — soma `quantity` ao total de faltas da matéria."""
    subject = get_owned_subject(db, payload.subject_id, user)
    absence = absence_service.add_absence(db, user, subject, payload.absence_date, payload.quantity, payload.notes)
    return _to_out(absence)


@router.patch("/{absence_id}", response_model=AbsenceOut)
async def update_absence(
    absence_id: int,
    payload: AbsenceUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AbsenceOut:
    """Corrige a quantidade de um registro de falta, ajustando o total da matéria pela diferença."""
    _get_own_absence_or_404(db, absence_id, user)
    absence = absence_service.update_absence_quantity(db, absence_id, payload.quantity)
    return _to_out(absence)


@router.delete("/{absence_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_absence(
    absence_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Apaga um registro de falta, subtraindo `quantity` do total da matéria."""
    _get_own_absence_or_404(db, absence_id, user)
    absence_service.delete_absence_by_id(db, absence_id)
