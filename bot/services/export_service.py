# bot/services/export_service.py

from datetime import datetime, timedelta, timezone
from typing import List

from sqlalchemy.orm import Session

from bot.db.models import Activity, User
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


def _escape_ics_text(text: str) -> str:
    """Escapa caracteres especiais em campos de texto do iCalendar (RFC 5545)."""
    return (
        text.replace('\\', '\\\\')
        .replace(';', '\\;')
        .replace(',', '\\,')
        .replace('\n', '\\n')
    )


def _fold_ics_line(line: str) -> str:
    """Quebra ('dobra') linhas maiores que 75 octets, como o RFC 5545 exige."""
    line_bytes = line.encode('utf-8')
    if len(line_bytes) <= 75:
        return line

    folded = []
    remaining = line
    while len(remaining.encode('utf-8')) > 75:
        cut = 75
        while len(remaining[:cut].encode('utf-8')) > 75:
            cut -= 1
        folded.append(remaining[:cut])
        remaining = ' ' + remaining[cut:]
    folded.append(remaining)
    return '\r\n'.join(folded)


def build_activities_ics(activities: List[Activity]) -> str:
    """Monta um arquivo .ics (iCalendar) com os trabalhos e provas do usuário."""
    now_stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Jovis//Calendario Academico//PT",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
    ]

    for activity in activities:
        start = activity.due_date.strftime('%Y%m%d')
        end = (activity.due_date + timedelta(days=1)).strftime('%Y%m%d')
        type_label = "Prova" if activity.activity_type == "prova" else "Trabalho"
        summary = _escape_ics_text(f"{type_label}: {activity.name} — {activity.subject.name}")

        lines.append("BEGIN:VEVENT")
        lines.append(f"UID:activity-{activity.id}@jovisbot")
        lines.append(f"DTSTAMP:{now_stamp}")
        lines.append(f"DTSTART;VALUE=DATE:{start}")
        lines.append(f"DTEND;VALUE=DATE:{end}")
        lines.append(f"SUMMARY:{summary}")
        if activity.notes:
            lines.append(f"DESCRIPTION:{_escape_ics_text(activity.notes)}")
        lines.append("END:VEVENT")

    lines.append("END:VCALENDAR")

    return '\r\n'.join(_fold_ics_line(line) for line in lines) + '\r\n'
