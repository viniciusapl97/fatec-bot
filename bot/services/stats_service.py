# bot/services/stats_service.py

from sqlalchemy.orm import Session

from bot.db.models import User, Subject, Activity, Absence, Grade, Reminder


def get_bot_stats(db: Session) -> dict:
    """
    Retorna contagens gerais de uso do bot, para o /stats de admin.
    'total_users' é o total de usuários já cadastrados (User não guarda
    data de criação nem último acesso, então não dá pra medir "atividade
    recente" — é uma contagem de cadastro, não de uso ativo no momento).
    """
    return {
        "total_users": db.query(User).count(),
        "total_subjects": db.query(Subject).count(),
        "total_activities": db.query(Activity).count(),
        "total_trabalhos": db.query(Activity).filter(Activity.activity_type == "trabalho").count(),
        "total_provas": db.query(Activity).filter(Activity.activity_type == "prova").count(),
        "total_absence_records": db.query(Absence).count(),
        "total_grades": db.query(Grade).count(),
        "total_pending_reminders": db.query(Reminder).count(),
    }
