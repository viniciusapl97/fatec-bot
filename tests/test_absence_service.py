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
