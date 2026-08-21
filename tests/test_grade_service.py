from decimal import Decimal

from bot.services import subject_service, grade_service


def _make_subject(db, user, name="Cálculo I"):
    return subject_service.create_subject(
        db, user, name, "Prof. X", "Segunda", "A1", None, None, 1
    )


def test_add_grade_sets_fields(db, user):
    subject = _make_subject(db, user)
    grade = grade_service.add_grade(db, user, subject, "P1", Decimal("8.5"))

    assert grade.name == "P1"
    assert grade.value == Decimal("8.50")
    assert grade.subject_id == subject.id


def test_get_grades_by_subject_orders_by_name(db, user):
    subject = _make_subject(db, user)
    grade_service.add_grade(db, user, subject, "P2", Decimal("6.0"))
    grade_service.add_grade(db, user, subject, "P1", Decimal("8.0"))

    names = [g.name for g in grade_service.get_grades_by_subject(db, subject)]
    assert names == ["P1", "P2"]


def test_get_grades_by_user(db, user):
    subject = _make_subject(db, user)
    grade_service.add_grade(db, user, subject, "P1", Decimal("7.0"))

    grades = grade_service.get_grades_by_user(db, user)
    assert len(grades) == 1


def test_get_grade_by_id_returns_none_when_missing(db):
    assert grade_service.get_grade_by_id(db, 999) is None


def test_update_grade_changes_name_and_value(db, user):
    subject = _make_subject(db, user)
    grade = grade_service.add_grade(db, user, subject, "P1", Decimal("5.0"))

    updated = grade_service.update_grade(db, grade.id, "P1 (revisão)", Decimal("7.0"))

    assert updated.name == "P1 (revisão)"
    assert updated.value == Decimal("7.00")


def test_update_grade_returns_none_when_missing(db):
    assert grade_service.update_grade(db, 999, "X", Decimal("1.0")) is None


def test_delete_grade_by_id(db, user):
    subject = _make_subject(db, user)
    grade = grade_service.add_grade(db, user, subject, "P1", Decimal("5.0"))

    assert grade_service.delete_grade_by_id(db, grade.id) is True
    assert grade_service.get_grade_by_id(db, grade.id) is None
    assert grade_service.delete_grade_by_id(db, grade.id) is False


def test_get_average_returns_none_for_empty_list():
    assert grade_service.get_average([]) is None


def test_get_average_computes_arithmetic_mean(db, user):
    subject = _make_subject(db, user)
    grade_service.add_grade(db, user, subject, "P1", Decimal("7.5"))
    grade_service.add_grade(db, user, subject, "P2", Decimal("5.0"))

    grades = grade_service.get_grades_by_subject(db, subject)
    assert grade_service.get_average(grades) == Decimal("6.25")
