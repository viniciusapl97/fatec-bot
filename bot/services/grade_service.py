from sqlalchemy.orm import Session
from decimal import Decimal
from typing import List

from bot.db.models import Grade, User, Subject

def add_grade(db: Session, user: User, subject: Subject, name: str, value: Decimal) -> Grade:
    """
    Adiciona uma nova nota a uma matéria para um determinado usuário.
    """
    db_grade = Grade(
        name=name,
        value=value,
        owner=user,
        subject=subject
    )
    db.add(db_grade)
    db.commit()
    db.refresh(db_grade)
    return db_grade

def get_grades_by_subject(db: Session, subject: Subject) -> List[Grade]:
    """
    Retorna uma lista de todas as notas de uma matéria específica,
    ordenadas pelo nome da avaliação (ex: P1, P2, Trabalho 1).
    """
    return db.query(Grade).filter(Grade.subject_id == subject.id).order_by(Grade.name).all()

def get_grades_by_user(db: Session, user: User) -> List[Grade]:
    """Retorna uma lista de todas as notas de um usuário."""
    return db.query(Grade).filter(Grade.user_id == user.user_id).all()