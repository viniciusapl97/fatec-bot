from datetime import date, timedelta

from bot.services import user_service, subject_service, activity_service


def test_get_or_create_user_creates_new_user(db):
    created_user, is_new = user_service.get_or_create_user(db, 1, "Bruno", "bruno_tg")

    assert is_new is True
    assert created_user.user_id == 1
    assert created_user.first_name == "Bruno"
    assert created_user.username == "bruno_tg"


def test_get_or_create_user_returns_existing_user(db):
    first_call, _ = user_service.get_or_create_user(db, 1, "Bruno", "bruno_tg")
    second_call, is_new = user_service.get_or_create_user(db, 1, "Bruno", "bruno_tg")

    assert is_new is False
    assert second_call.id == first_call.id


def test_get_user_by_telegram_id_returns_none_when_not_found(db):
    assert user_service.get_user_by_telegram_id(db, 999) is None


def test_get_user_by_telegram_id_finds_existing_user(db, user):
    found = user_service.get_user_by_telegram_id(db, user.user_id)
    assert found is not None
    assert found.user_id == user.user_id


def test_get_all_active_users_returns_every_user(db):
    user_service.get_or_create_user(db, 1, "Bruno", "bruno")
    user_service.get_or_create_user(db, 2, "Carla", "carla")

    all_users = user_service.get_all_active_users(db)
    assert {u.user_id for u in all_users} == {1, 2}


def test_delete_user_by_id_returns_false_when_not_found(db):
    assert user_service.delete_user_by_id(db, 999) is False


def test_delete_user_by_id_cascades_to_subjects(db, user):
    subject_service.create_subject(
        db, user, "Cálculo I", "Prof. X", "Segunda", "A1",
        None, None, 1,
    )

    deleted = user_service.delete_user_by_id(db, user.user_id)

    assert deleted is True
    assert user_service.get_user_by_telegram_id(db, user.user_id) is None
    assert subject_service.get_subjects_by_user(db, user) == []


def test_get_upcoming_activities_filters_by_exact_days_ahead(db, user):
    subject = subject_service.create_subject(
        db, user, "Redes", "Prof. Y", "Terça", "B2", None, None, 2
    )
    tomorrow = date.today() + timedelta(days=1)
    in_three_days = date.today() + timedelta(days=3)
    in_five_days = date.today() + timedelta(days=5)

    activity_service.create_activity(db, user, subject, "P1", tomorrow, None, "prova")
    activity_service.create_activity(db, user, subject, "P2", in_three_days, None, "prova")
    activity_service.create_activity(db, user, subject, "Trabalho", in_five_days, None, "trabalho")

    due_tomorrow = user_service.get_upcoming_activities(db, days_ahead=1)
    due_in_three_days = user_service.get_upcoming_activities(db, days_ahead=3)
    due_in_four_days = user_service.get_upcoming_activities(db, days_ahead=4)

    assert [a.name for a in due_tomorrow] == ["P1"]
    assert [a.name for a in due_in_three_days] == ["P2"]
    assert due_in_four_days == []
