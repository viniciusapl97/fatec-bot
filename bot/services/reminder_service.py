# bot/services/reminder_service.py

from datetime import datetime
from typing import List
from sqlalchemy.orm import Session

from bot.db.models import Reminder, User


def create_reminder(db: Session, user: User, message: str, remind_at: datetime) -> Reminder:
    """Cria um lembrete personalizado pendente para o usuário."""
    db_reminder = Reminder(message=message, remind_at=remind_at, owner=user)
    db.add(db_reminder)
    db.commit()
    db.refresh(db_reminder)
    return db_reminder


def get_pending_reminders(db: Session) -> List[Reminder]:
    """Retorna todos os lembretes ainda não entregues, de todos os usuários."""
    return db.query(Reminder).all()


def delete_reminder_by_id(db: Session, reminder_id: int) -> bool:
    """Remove um lembrete (usado assim que ele é entregue ao usuário)."""
    db_reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
    if db_reminder:
        db.delete(db_reminder)
        db.commit()
        return True
    return False
