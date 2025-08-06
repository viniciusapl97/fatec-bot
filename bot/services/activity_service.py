from sqlalchemy.orm import Session
from datetime import date
from typing import List
from datetime import date, timedelta

from bot.db.models import Activity, User, Subject

def create_activity(db: Session, user: User, subject: Subject, name: str, due_date: date, notes: str | None, activity_type: str) -> Activity:
    """Cria uma nova atividade, agora com um tipo ('trabalho' ou 'prova')."""
    db_activity = Activity(
        name=name, due_date=due_date, notes=notes,
        activity_type=activity_type, # Adiciona o tipo
        owner=user, subject=subject
    )
    db.add(db_activity)
    db.commit()
    db.refresh(db_activity)
    return db_activity

def get_activities_by_user(db: Session, user: User) -> List[Activity]:
    """
    Retorna uma lista de todas as atividades de um usuário específico,
    ordenada pela data de entrega.
    """
    # Filtra as atividades pelo ID do usuário e ordena pela data de entrega (due_date)
    return db.query(Activity).filter(Activity.user_id == user.user_id).order_by(Activity.due_date).all()

def get_activities_by_user_and_type(db: Session, user: User, activity_type: str) -> List[Activity]:
    """
    Retorna uma lista de atividades de um usuário, filtrada por tipo ('trabalho' ou 'prova'),
    ordenada pela data de entrega.
    """
    return db.query(Activity).filter(
        Activity.user_id == user.user_id,
        Activity.activity_type == activity_type
    ).order_by(Activity.due_date).all()



def get_activity_by_id(db: Session, activity_id: int) -> Activity | None:
    """Busca uma atividade pelo seu ID primário."""
    return db.query(Activity).filter(Activity.id == activity_id).first()

def update_activity(db: Session, activity_id: int, new_data: dict) -> Activity | None:
    """
    Atualiza os dados de uma atividade específica.
    'new_data' é um dicionário com os campos a serem atualizados.
    """
    db_activity = get_activity_by_id(db, activity_id)
    if db_activity:
        for key, value in new_data.items():
            setattr(db_activity, key, value)
        db.commit()
        db.refresh(db_activity)
        return db_activity
    return None

def delete_activity_by_id(db: Session, activity_id: int) -> bool:
    """Deleta uma atividade pelo seu ID primário."""
    activity_to_delete = get_activity_by_id(db, activity_id)
    if activity_to_delete:
        db.delete(activity_to_delete)
        db.commit()
        return True
    return False



def get_activities_by_date(db: Session, user: User, target_date: date) -> List[Activity]:
    """Retorna uma lista de atividades de um usuário para uma data específica."""
    return db.query(Activity).filter(
        Activity.user_id == user.user_id,
        Activity.due_date == target_date
    ).order_by(Activity.name).all()
    

def get_activities_by_date_range(db: Session, user: User, start_date: date, end_date: date) -> List[Activity]:
    """Retorna atividades de um usuário dentro de um intervalo de datas."""
    return db.query(Activity).filter(
        Activity.user_id == user.user_id,
        Activity.due_date >= start_date,
        Activity.due_date <= end_date
    ).order_by(Activity.due_date).all()
    
def get_activities_by_subject(db: Session, subject: Subject) -> List[Activity]:
    """
    Retorna uma lista de todas as atividades de uma matéria específica,
    ordenada pela data de entrega.
    """
    return db.query(Activity).filter(Activity.subject_id == subject.id).order_by(Activity.due_date).all()
