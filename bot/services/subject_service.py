# bot/services/subject_service.py

from sqlalchemy.orm import Session
from sqlalchemy import case
from bot.db.models import Subject, User, Absence, Grade
from typing import List
from datetime import time

def create_subject(db: Session, user: User, name: str, professor: str, day: str, room: str, start_time: time, end_time: time, semestre: int) -> Subject:
    """Cria uma nova matéria, agora com semestre."""
    db_subject = Subject(
        name=name, professor=professor, day_of_week=day, room=room,
        start_time=start_time, end_time=end_time, semestre=semestre, owner=user
    )
    db.add(db_subject)
    db.commit()
    db.refresh(db_subject)
    return db_subject

def get_subjects_by_user(db: Session, user: User) -> List[Subject]:
    """Retorna matérias de um usuário, ordenadas por dia e horário de início."""
    day_order_case = case(
        {"Segunda": 1, "Terça": 2, "Quarta": 3, "Quinta": 4, "Sexta": 5, "Sábado": 6},
        value=Subject.day_of_week
    )
    # Ordena primeiro pelo dia, depois pelo horário de início
    return db.query(Subject).filter(Subject.user_id == user.user_id).order_by(day_order_case, Subject.start_time).all()

def get_subjects_by_day_of_week(db: Session, user: User, day_name: str) -> List[Subject]:
    """Retorna matérias de um dia, ordenadas por horário de início."""
    return db.query(Subject).filter(
        Subject.user_id == user.user_id,
        Subject.day_of_week == day_name
    ).order_by(Subject.start_time).all()

def get_subject_by_id(db: Session, subject_id: int) -> Subject | None:
    return db.query(Subject).filter(Subject.id == subject_id).first()

def update_subject(db: Session, subject_id: int, new_data: dict) -> Subject | None:
    db_subject = get_subject_by_id(db, subject_id)
    if db_subject:
        for key, value in new_data.items():
            setattr(db_subject, key, value)
        db.commit()
        db.refresh(db_subject)
        return db_subject
    return None

def delete_subject_by_id(db: Session, subject_id: int) -> bool:
    subject_to_delete = get_subject_by_id(db, subject_id)
    if subject_to_delete:
        db.delete(subject_to_delete)
        db.commit()
        return True
    return False