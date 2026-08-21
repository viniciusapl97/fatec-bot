from datetime import date, timedelta

from bot.services import subject_service, activity_service


def _make_subject(db, user, name="Cálculo I"):
    return subject_service.create_subject(
        db, user, name, "Prof. X", "Segunda", "A1", None, None, 1
    )


def test_create_activity_sets_fields(db, user):
    subject = _make_subject(db, user)
    due = date.today() + timedelta(days=5)

    activity = activity_service.create_activity(db, user, subject, "P1", due, "levar calculadora", "prova")

    assert activity.name == "P1"
    assert activity.due_date == due
    assert activity.notes == "levar calculadora"
    assert activity.activity_type == "prova"
    assert activity.subject_id == subject.id


def test_get_activities_by_user_orders_by_due_date(db, user):
    subject = _make_subject(db, user)
    later = date.today() + timedelta(days=10)
    sooner = date.today() + timedelta(days=1)

    activity_service.create_activity(db, user, subject, "Depois", later, None, "trabalho")
    activity_service.create_activity(db, user, subject, "Antes", sooner, None, "trabalho")

    names = [a.name for a in activity_service.get_activities_by_user(db, user)]
    assert names == ["Antes", "Depois"]


def test_get_activities_by_user_and_type_filters(db, user):
    subject = _make_subject(db, user)
    today = date.today()

    activity_service.create_activity(db, user, subject, "P1", today, None, "prova")
    activity_service.create_activity(db, user, subject, "T1", today, None, "trabalho")

    provas = activity_service.get_activities_by_user_and_type(db, user, "prova")
    assert [a.name for a in provas] == ["P1"]


def test_get_activity_by_id_returns_none_when_missing(db):
    assert activity_service.get_activity_by_id(db, 999) is None


def test_update_activity_changes_fields(db, user):
    subject = _make_subject(db, user)
    activity = activity_service.create_activity(db, user, subject, "P1", date.today(), None, "prova")

    updated = activity_service.update_activity(db, activity.id, {"notes": "sala trocada"})
    assert updated.notes == "sala trocada"


def test_update_activity_returns_none_when_missing(db):
    assert activity_service.update_activity(db, 999, {"notes": "x"}) is None


def test_delete_activity_by_id(db, user):
    subject = _make_subject(db, user)
    activity = activity_service.create_activity(db, user, subject, "P1", date.today(), None, "prova")

    assert activity_service.delete_activity_by_id(db, activity.id) is True
    assert activity_service.get_activity_by_id(db, activity.id) is None
    assert activity_service.delete_activity_by_id(db, activity.id) is False


def test_get_activities_by_date(db, user):
    subject = _make_subject(db, user)
    today = date.today()
    tomorrow = today + timedelta(days=1)

    activity_service.create_activity(db, user, subject, "Hoje", today, None, "prova")
    activity_service.create_activity(db, user, subject, "Amanhã", tomorrow, None, "prova")

    names = [a.name for a in activity_service.get_activities_by_date(db, user, today)]
    assert names == ["Hoje"]


def test_get_activities_by_date_range(db, user):
    subject = _make_subject(db, user)
    today = date.today()

    activity_service.create_activity(db, user, subject, "Dentro", today + timedelta(days=2), None, "prova")
    activity_service.create_activity(db, user, subject, "Fora", today + timedelta(days=20), None, "prova")

    names = [
        a.name for a in activity_service.get_activities_by_date_range(
            db, user, today, today + timedelta(days=7)
        )
    ]
    assert names == ["Dentro"]


def test_get_activities_by_subject_only_returns_that_subject(db, user):
    subject_a = _make_subject(db, user, name="Matéria A")
    subject_b = _make_subject(db, user, name="Matéria B")

    activity_service.create_activity(db, user, subject_a, "Da A", date.today(), None, "prova")
    activity_service.create_activity(db, user, subject_b, "Da B", date.today(), None, "prova")

    names = [a.name for a in activity_service.get_activities_by_subject(db, subject_a)]
    assert names == ["Da A"]
