from sqlalchemy.orm import Session
from bot.db.models import User
from typing import Tuple # Importe Tuple
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