# bot/services/export_service.py

from sqlalchemy.orm import Session

from bot.db.models import User
from bot.services import subject_service, activity_service, absence_service, grade_service, reminder_service


def _format_time(t):
    return t.strftime('%H:%M') if t else None


def _format_date(d):
    return d.strftime('%d/%m/%Y') if d else None


def build_user_export(db: Session, user: User) -> dict:
    """Monta um dicionário com todos os dados do usuário, pronto para virar JSON."""
    subjects_data = []
    for subject in subject_service.get_subjects_by_user(db, user):
        activities = activity_service.get_activities_by_subject(db, subject)
        absences = absence_service.get_absences_by_subject(db, subject)
        grades = grade_service.get_grades_by_subject(db, subject)

        subjects_data.append({
            "nome": subject.name,
            "professor": subject.professor,
            "dia_semana": subject.day_of_week,
            "sala": subject.room,
            "horario_inicio": _format_time(subject.start_time),
            "horario_fim": _format_time(subject.end_time),
            "semestre": subject.semestre,
            "total_aulas": subject.total_classes,
            "total_faltas": subject.total_absences,
            "atividades": [
                {
                    "tipo": a.activity_type,
                    "nome": a.name,
                    "data_entrega": _format_date(a.due_date),
                    "observacoes": a.notes,
                }
                for a in activities
            ],
            "faltas": [
                {
                    "data": _format_date(ab.absence_date),
                    "quantidade": ab.quantity,
                    "observacoes": ab.notes,
                }
                for ab in absences
            ],
            "notas": [
                {"nome": g.name, "valor": str(g.value)}
                for g in grades
            ],
        })

    reminders_data = [
        {
            "mensagem": r.message,
            "quando": r.remind_at.strftime('%d/%m/%Y %H:%M'),
        }
        for r in reminder_service.get_pending_reminders_by_user(db, user)
    ]

    return {
        "usuario": {
            "nome": user.first_name,
            "username": user.username,
        },
        "materias": subjects_data,
        "lembretes_pendentes": reminders_data,
    }
