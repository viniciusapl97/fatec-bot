from datetime import date, timedelta
from sqlalchemy.orm import Session
from bot.db.models import Activity, User
from typing import Tuple 
from typing import List



def get_or_create_user(db: Session, user_id: int, first_name: str, username: str | None) -> Tuple[User, bool]:
    """
    Busca um usuário no banco de dados pelo user_id.
    Se o usuário não existir, cria um novo.
    Retorna a instância do usuário e um booleano 'is_new' (True se foi criado agora).
    """
    db_user = db.query(User).filter(User.user_id == user_id).first()
    
    if not db_user:
        is_new = True
        db_user = User(
            user_id=user_id,
            first_name=first_name,
            username=username
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
    else:
        is_new = False
        
    return db_user, is_new

def get_all_active_users(db: Session) -> List[User]:
    """Retorna uma lista de todos os usuários no banco de dados."""
    return db.query(User).all()

def get_user_by_telegram_id(db: Session, user_id: int) -> User | None:
    """Busca um usuário pelo seu ID do Telegram."""
    return db.query(User).filter(User.user_id == user_id).first()

def delete_user_by_id(db: Session, user_id: int) -> bool:
    """
    Busca um usuário pelo seu ID do Telegram e o remove do banco de dados.
    A remoção em cascata apagará todos os dados associados a ele.
    """
    db_user = db.query(User).filter(User.user_id == user_id).first()
    if db_user:
        db.delete(db_user)
        db.commit()
        return True
    return False

def get_upcoming_activities(db: Session, days_ahead: int) -> List[Activity]:
    """
    Busca todas as atividades de todos os usuários que vencem em exatamente 'days_ahead' dias.
    """
    target_date = date.today() + timedelta(days=days_ahead)
    return db.query(Activity).filter(Activity.due_date == target_date).all()