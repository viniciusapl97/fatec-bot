from datetime import datetime, timedelta, timezone

from bot.services import user_service, reminder_service


def test_create_reminder_sets_fields(db, user):
    when = datetime.now(timezone.utc) + timedelta(hours=1)
    reminder = reminder_service.create_reminder(db, user, "Estudar SQL", when)

    assert reminder.message == "Estudar SQL"
    # SQLite (usado nos testes) não preserva tzinfo em DateTime(timezone=True) como o
    # Postgres (usado em produção) faz, então comparamos ignorando o fuso.
    assert reminder.remind_at.replace(tzinfo=None) == when.replace(tzinfo=None)
    assert reminder.user_id == user.user_id


def test_get_pending_reminders_returns_all_users(db, user):
    other_user, _ = user_service.get_or_create_user(db, 999, "Outro", "outro")
    when = datetime.now(timezone.utc) + timedelta(hours=1)

    reminder_service.create_reminder(db, user, "Do usuário 1", when)
    reminder_service.create_reminder(db, other_user, "Do usuário 2", when)

    pending = reminder_service.get_pending_reminders(db)
    assert len(pending) == 2


def test_get_pending_reminders_by_user_filters(db, user):
    other_user, _ = user_service.get_or_create_user(db, 999, "Outro", "outro")
    when = datetime.now(timezone.utc) + timedelta(hours=1)

    reminder_service.create_reminder(db, user, "Do usuário 1", when)
    reminder_service.create_reminder(db, other_user, "Do usuário 2", when)

    mine = reminder_service.get_pending_reminders_by_user(db, user)
    assert [r.message for r in mine] == ["Do usuário 1"]


def test_delete_reminder_by_id(db, user):
    when = datetime.now(timezone.utc) + timedelta(hours=1)
    reminder = reminder_service.create_reminder(db, user, "Estudar SQL", when)

    assert reminder_service.delete_reminder_by_id(db, reminder.id) is True
    assert reminder_service.get_pending_reminders_by_user(db, user) == []


def test_delete_reminder_by_id_returns_false_when_missing(db):
    assert reminder_service.delete_reminder_by_id(db, 999) is False
