from datetime import date, timedelta

from bot.services import subject_service, absence_service


def _make_subject(db, user):
    return subject_service.create_subject(
        db, user, "Cálculo I", "Prof. X", "Segunda", "A1", None, None, 1
    )


def test_add_absence_increments_subject_total(db, user):
    subject = _make_subject(db, user)

    absence_service.add_absence(db, user, subject, date.today(), 2, "atestado")
    assert subject.total_absences == 2

    absence_service.add_absence(db, user, subject, date.today() - timedelta(days=7), 1, None)
    assert subject.total_absences == 3


def test_get_absences_by_subject_orders_by_date_desc(db, user):
    subject = _make_subject(db, user)
    older = date.today() - timedelta(days=10)
    newer = date.today()

    absence_service.add_absence(db, user, subject, older, 1, None)
    absence_service.add_absence(db, user, subject, newer, 1, None)

    dates = [a.absence_date for a in absence_service.get_absences_by_subject(db, subject)]
    assert dates == [newer, older]


def test_get_absence_by_id_returns_none_when_missing(db):
    assert absence_service.get_absence_by_id(db, 999) is None


def test_update_absence_quantity_adjusts_subject_total(db, user):
    subject = _make_subject(db, user)
    absence = absence_service.add_absence(db, user, subject, date.today(), 2, None)

    absence_service.update_absence_quantity(db, absence.id, 5)
    assert subject.total_absences == 5

    absence_service.update_absence_quantity(db, absence.id, 1)
    assert subject.total_absences == 1


def test_update_absence_quantity_returns_none_when_missing(db):
    assert absence_service.update_absence_quantity(db, 999, 3) is None


def test_delete_absence_by_id_decrements_subject_total(db, user):
    subject = _make_subject(db, user)
    absence = absence_service.add_absence(db, user, subject, date.today(), 3, None)

    deleted = absence_service.delete_absence_by_id(db, absence.id)

    assert deleted is True
    assert subject.total_absences == 0
    assert absence_service.get_absence_by_id(db, absence.id) is None


def test_delete_absence_by_id_returns_false_when_missing(db):
    assert absence_service.delete_absence_by_id(db, 999) is False


def test_get_absences_by_user_orders_by_date_desc_across_subjects(db, user):
    subject_a = _make_subject(db, user)
    subject_b = subject_service.create_subject(db, user, "Redes", "Prof. Y", "Terça", "A2", None, None, 1)
    older = date.today() - timedelta(days=10)
    newer = date.today()

    absence_service.add_absence(db, user, subject_a, older, 1, None)
    absence_service.add_absence(db, user, subject_b, newer, 2, None)

    absences = absence_service.get_absences_by_user(db, user)
    assert [a.absence_date for a in absences] == [newer, older]


def test_get_absences_by_user_only_returns_own_absences(db, user):
    from bot.services import user_service
    other_user, _ = user_service.get_or_create_user(db, 999, "Outro", "outro")
    other_subject = subject_service.create_subject(db, other_user, "Matéria de outro", "Prof. Z", "Segunda", "C1", None, None, 1)
    absence_service.add_absence(db, other_user, other_subject, date.today(), 1, None)

    subject = _make_subject(db, user)
    absence_service.add_absence(db, user, subject, date.today(), 1, None)

    absences = absence_service.get_absences_by_user(db, user)
    assert len(absences) == 1
    assert absences[0].subject_id == subject.id
