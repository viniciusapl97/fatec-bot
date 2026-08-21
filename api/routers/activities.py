# api/routers/activities.py

from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.deps import get_current_user, get_db, get_owned_subject
from api.schemas import ActivityCreate, ActivityOut, ActivityUpdate
from bot.db.models import Activity, User
from bot.services import activity_service

router = APIRouter(prefix="/activities", tags=["activities"])


def _to_out(a: Activity) -> ActivityOut:
    return ActivityOut(
        id=a.id,
        activity_type=a.activity_type,
        name=a.name,
        due_date=a.due_date,
        notes=a.notes,
        subject_id=a.subject_id,
        subject_name=a.subject.name,
    )


def _get_own_activity_or_404(db: Session, activity_id: int, user: User) -> Activity:
    activity = activity_service.get_activity_by_id(db, activity_id)
    if not activity or activity.user_id != user.user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Atividade não encontrada.")
    return activity


@router.get("", response_model=List[ActivityOut])
async def list_activities(
    activity_type: Optional[Literal["trabalho", "prova"]] = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list:
    """
    Lista os trabalhos e provas do usuário (mesma lógica do /calendario).
    Filtra por `?activity_type=trabalho` ou `?activity_type=prova`, se informado.
    """
    if activity_type:
        activities = activity_service.get_activities_by_user_and_type(db, user, activity_type)
    else:
        activities = activity_service.get_activities_by_user(db, user)

    return [_to_out(a) for a in activities]


@router.post("", response_model=ActivityOut, status_code=status.HTTP_201_CREATED)
async def create_activity(
    payload: ActivityCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ActivityOut:
    """Cria um trabalho ou prova (mesma lógica do /addtrabalho e /addprova)."""
    subject = get_owned_subject(db, payload.subject_id, user)
    activity = activity_service.create_activity(
        db, user, subject, payload.name, payload.due_date, payload.notes, payload.activity_type
    )
    return _to_out(activity)


@router.patch("/{activity_id}", response_model=ActivityOut)
async def update_activity(
    activity_id: int,
    payload: ActivityUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ActivityOut:
    """Atualiza campos de um trabalho/prova (só os enviados; mover pra outra matéria com `subject_id`)."""
    _get_own_activity_or_404(db, activity_id, user)
    updates = payload.model_dump(exclude_unset=True)

    if "subject_id" in updates:
        get_owned_subject(db, updates["subject_id"], user)

    activity = activity_service.update_activity(db, activity_id, updates)
    return _to_out(activity)


@router.delete("/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_activity(
    activity_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Apaga um trabalho/prova."""
    _get_own_activity_or_404(db, activity_id, user)
    activity_service.delete_activity_by_id(db, activity_id)
