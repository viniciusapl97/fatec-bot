# api/routers/subjects.py

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.deps import get_current_user, get_db, get_owned_subject
from api.schemas import (
    AttendanceOut,
    GradeOut,
    SubjectCreate,
    SubjectGradesOut,
    SubjectOut,
    SubjectUpdate,
)
from bot.db.models import Subject, User
from bot.services import grade_service, subject_service

router = APIRouter(prefix="/subjects", tags=["subjects"])


def _conflict_detail(conflicting: Subject) -> str:
    return (
        f'Conflito de horário com "{conflicting.name}" ({conflicting.day_of_week} '
        f"{conflicting.start_time.strftime('%H:%M')}-{conflicting.end_time.strftime('%H:%M')})."
    )


@router.get("", response_model=List[SubjectOut])
async def list_subjects(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list:
    """Lista as matérias do usuário dono do token, ordenadas por dia/horário (mesma lógica do /grade)."""
    return subject_service.get_subjects_by_user(db, user)


@router.post("", response_model=SubjectOut, status_code=status.HTTP_201_CREATED)
async def create_subject(
    payload: SubjectCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Subject:
    """Cria uma matéria (mesma lógica do /addmateria). 409 se o horário colidir com outra matéria já cadastrada."""
    if payload.start_time and payload.end_time:
        conflicting = subject_service.check_conflict_with_existing(
            db, user, payload.day_of_week, payload.start_time, payload.end_time
        )
        if conflicting:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=_conflict_detail(conflicting))

    return subject_service.create_subject(
        db,
        user,
        name=payload.name,
        professor=payload.professor,
        day=payload.day_of_week,
        room=payload.room,
        start_time=payload.start_time,
        end_time=payload.end_time,
        semestre=payload.semestre,
        total_classes=payload.total_classes,
    )


@router.patch("/{subject_id}", response_model=SubjectOut)
async def update_subject(
    subject_id: int,
    payload: SubjectUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Subject:
    """Atualiza campos de uma matéria (só os enviados). 409 se a mudança de dia/horário colidir com outra matéria."""
    subject = get_owned_subject(db, subject_id, user)
    updates = payload.model_dump(exclude_unset=True)

    new_day = updates.get("day_of_week", subject.day_of_week)
    new_start = updates.get("start_time", subject.start_time)
    new_end = updates.get("end_time", subject.end_time)
    if new_start and new_end:
        conflicting = subject_service.check_conflict_with_existing(
            db, user, new_day, new_start, new_end, exclude_subject_id=subject.id
        )
        if conflicting:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=_conflict_detail(conflicting))

    return subject_service.update_subject(db, subject_id, updates)


@router.delete("/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subject(
    subject_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Apaga uma matéria (e, em cascata, suas atividades/faltas/notas — ver bot/db/models.py)."""
    get_owned_subject(db, subject_id, user)
    subject_service.delete_subject_by_id(db, subject_id)


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
    subject = get_owned_subject(db, subject_id, user)
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
    subject = get_owned_subject(db, subject_id, user)
    grades = grade_service.get_grades_by_subject(db, subject)

    return SubjectGradesOut(
        subject_id=subject.id,
        subject_name=subject.name,
        grades=[GradeOut(id=g.id, name=g.name, value=g.value, subject_id=g.subject_id, subject_name=subject.name) for g in grades],
        average=grade_service.get_average(grades),
    )
