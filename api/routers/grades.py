# api/routers/grades.py

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.deps import get_current_user, get_db, get_owned_subject
from api.schemas import GradeCreate, GradeOut, GradeUpdate
from bot.db.models import Grade, User
from bot.services import grade_service

router = APIRouter(prefix="/grades", tags=["grades"])


def _to_out(g: Grade) -> GradeOut:
    return GradeOut(
        id=g.id,
        name=g.name,
        value=g.value,
        subject_id=g.subject_id,
        subject_name=g.subject.name,
    )


def _get_own_grade_or_404(db: Session, grade_id: int, user: User) -> Grade:
    grade = grade_service.get_grade_by_id(db, grade_id)
    if not grade or grade.user_id != user.user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nota não encontrada.")
    return grade


@router.get("", response_model=List[GradeOut])
async def list_grades(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list:
    """Lista todas as notas lançadas pelo usuário (todas as matérias)."""
    grades = grade_service.get_grades_by_user(db, user)
    return [_to_out(g) for g in grades]


@router.post("", response_model=GradeOut, status_code=status.HTTP_201_CREATED)
async def create_grade(
    payload: GradeCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> GradeOut:
    """Lança uma nota numa matéria (mesma lógica do /addnota)."""
    subject = get_owned_subject(db, payload.subject_id, user)
    grade = grade_service.add_grade(db, user, subject, payload.name, payload.value)
    return _to_out(grade)


@router.patch("/{grade_id}", response_model=GradeOut)
async def update_grade(
    grade_id: int,
    payload: GradeUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> GradeOut:
    """Atualiza o nome e o valor de uma nota (os dois campos são obrigatórios, mesma lógica do bot)."""
    _get_own_grade_or_404(db, grade_id, user)
    grade = grade_service.update_grade(db, grade_id, payload.name, payload.value)
    return _to_out(grade)


@router.delete("/{grade_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_grade(
    grade_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Apaga uma nota."""
    _get_own_grade_or_404(db, grade_id, user)
    grade_service.delete_grade_by_id(db, grade_id)
