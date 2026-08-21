# api/routers/subjects.py

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.deps import get_current_user, get_db
from api.schemas import AttendanceOut, GradeOut, SubjectGradesOut, SubjectOut
from bot.db.models import Subject, User
from bot.services import grade_service, subject_service

router = APIRouter(prefix="/subjects", tags=["subjects"])


def _get_own_subject_or_404(db: Session, subject_id: int, user: User) -> Subject:
    """Busca uma matéria garantindo que pertence ao usuário do token; 404 se não existir ou for de outro usuário."""
    subject = subject_service.get_subject_by_id(db, subject_id)
    if not subject or subject.user_id != user.user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Matéria não encontrada.")
    return subject


@router.get("", response_model=List[SubjectOut])
async def list_subjects(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list:
    """Lista as matérias do usuário dono do token, ordenadas por dia/horário (mesma lógica do /grade)."""
    return subject_service.get_subjects_by_user(db, user)


@router.get("/{subject_id}/attendance", response_model=AttendanceOut)
async def get_subject_attendance(
    subject_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AttendanceOut:
    """
    Frequência de uma matéria (mesmo cálculo do /faltas). Os campos de
    percentual/faltas restantes ficam `null` se o usuário ainda não informou
    o total de aulas previstas para a matéria.
    """
    subject = _get_own_subject_or_404(db, subject_id, user)
    attendance = subject_service.get_attendance_info(subject)

    return AttendanceOut(
        subject_id=subject.id,
        total_classes=subject.total_classes,
        total_absences=subject.total_absences,
        **(attendance or {}),
    )


@router.get("/{subject_id}/grades", response_model=SubjectGradesOut)
async def get_subject_grades(
    subject_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SubjectGradesOut:
    """Notas de uma matéria específica, com a média aritmética simples (mesmo cálculo do /notas)."""
    subject = _get_own_subject_or_404(db, subject_id, user)
    grades = grade_service.get_grades_by_subject(db, subject)

    return SubjectGradesOut(
        subject_id=subject.id,
        subject_name=subject.name,
        grades=[GradeOut(id=g.id, name=g.name, value=g.value, subject_id=g.subject_id, subject_name=subject.name) for g in grades],
        average=grade_service.get_average(grades),
    )
