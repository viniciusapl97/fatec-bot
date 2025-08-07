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

def get_grade_by_id(db: Session, grade_id: int) -> Grade | None:
    """Busca uma nota pelo seu ID primário."""
    return db.query(Grade).filter(Grade.id == grade_id).first()

def update_grade(db: Session, grade_id: int, new_name: str, new_value: Decimal) -> Grade | None:
    """Atualiza o nome e o valor de uma nota específica."""
    db_grade = get_grade_by_id(db, grade_id)
    if db_grade:
        db_grade.name = new_name
        db_grade.value = new_value
        db.commit()
        db.refresh(db_grade)
        return db_grade
    return None

def delete_grade_by_id(db: Session, grade_id: int) -> bool:
    """Deleta uma nota pelo seu ID primário."""
    grade_to_delete = get_grade_by_id(db, grade_id)
    if grade_to_delete:
        db.delete(grade_to_delete)
        db.commit()
        return True
    return False