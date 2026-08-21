from datetime import date, datetime, timedelta, timezone, time
from decimal import Decimal

from bot.services import (
    user_service,
    subject_service,
    activity_service,
    absence_service,
    grade_service,
    reminder_service,
    stats_service,
)


def test_get_bot_stats_with_no_data(db):
    stats = stats_service.get_bot_stats(db)

    assert stats == {
        "total_users": 0,
        "total_subjects": 0,
        "total_activities": 0,
        "total_trabalhos": 0,
        "total_provas": 0,
        "total_absence_records": 0,
        "total_grades": 0,
        "total_pending_reminders": 0,
    }


def test_get_bot_stats_counts_across_all_users(db, user):
    other_user, _ = user_service.get_or_create_user(db, 999, "Outro", "outro")

    subject = subject_service.create_subject(
        db, user, "Cálculo I", "Prof. X", "Segunda", "A1", time(19, 0), time(20, 40), 1
    )
    activity_service.create_activity(db, user, subject, "P1", date.today(), None, "prova")
    activity_service.create_activity(db, user, subject, "T1", date.today(), None, "trabalho")
    activity_service.create_activity(db, user, subject, "T2", date.today(), None, "trabalho")
    absence_service.add_absence(db, user, subject, date.today(), 1, None)
    grade_service.add_grade(db, user, subject, "P1", Decimal("7.0"))
    reminder_service.create_reminder(db, user, "Estudar", datetime.now(timezone.utc) + timedelta(hours=1))

    subject_service.create_subject(
        db, other_user, "Redes", "Prof. Y", "Terça", "B2", time(19, 0), time(20, 40), 1
    )

    stats = stats_service.get_bot_stats(db)

    assert stats["total_users"] == 2
    assert stats["total_subjects"] == 2
    assert stats["total_activities"] == 3
    assert stats["total_trabalhos"] == 2
    assert stats["total_provas"] == 1
    assert stats["total_absence_records"] == 1
    assert stats["total_grades"] == 1
    assert stats["total_pending_reminders"] == 1
