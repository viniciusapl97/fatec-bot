# bot/services/absence_service.py

from sqlalchemy.orm import Session
from datetime import date
from typing import List

from . import subject_service
from bot.db.models import Absence, User, Subject

def add_absence(db: Session, user: User, subject: Subject, absence_date: date, quantity: int, notes: str | None) -> Absence:
    """Adiciona um novo registro de falta e atualiza o contador total na matéria."""
    db_absence = Absence(
        absence_date=absence_date, quantity=quantity, notes=notes,
        owner=user, subject=subject
    )
    subject.total_absences = (subject.total_absences or 0) + quantity
    db.add(db_absence)
    db.commit()
    db.refresh(db_absence)
    return db_absence

def get_absences_by_subject(db: Session, subject: Subject) -> List[Absence]:
    """Retorna uma lista de todos os registros de falta para uma matéria específica."""
    return db.query(Absence).filter(Absence.subject_id == subject.id).order_by(Absence.absence_date.desc()).all()

def get_absence_by_id(db: Session, absence_id: int) -> Absence | None:
    """Busca um registro de falta pelo seu ID primário."""
    return db.query(Absence).filter(Absence.id == absence_id).first()

def update_absence_quantity(db: Session, absence_id: int, new_quantity: int) -> Absence | None:
    """Atualiza a quantidade de uma falta e ajusta o total na matéria."""
    db_absence = get_absence_by_id(db, absence_id)
    if db_absence:
        difference = new_quantity - db_absence.quantity
        db_absence.subject.total_absences = (db_absence.subject.total_absences or 0) + difference
        db_absence.quantity = new_quantity
        db.commit()
        db.refresh(db_absence)
        return db_absence
    return None

def delete_absence_by_id(db: Session, absence_id: int) -> bool:
    """Deleta um registro de falta e ajusta o total na matéria."""
    db_absence = get_absence_by_id(db, absence_id)
    if db_absence:
        db_absence.subject.total_absences -= db_absence.quantity
        db.delete(db_absence)
        db.commit()
        return True
    return False