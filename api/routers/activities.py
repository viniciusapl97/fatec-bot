# api/routers/activities.py

from typing import List, Literal, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.deps import get_current_user, get_db
from api.schemas import ActivityOut
from bot.db.models import User
from bot.services import activity_service

router = APIRouter(prefix="/activities", tags=["activities"])


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

    return [
        ActivityOut(
            id=a.id,
            activity_type=a.activity_type,
            name=a.name,
            due_date=a.due_date,
            notes=a.notes,
            subject_id=a.subject_id,
            subject_name=a.subject.name,
        )
        for a in activities
    ]
